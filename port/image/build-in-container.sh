#!/bin/bash
# Offline composition only: mounts a NEW regular image file, never a phone.
set -euo pipefail
fail() { echo "eqs-image: $*" >&2; exit 1; }
[[ -f /.dockerenv && $(id -u) == 0 && $# == 2 ]] || fail 'use build.sh, not the host shell'
touch_profile=$1
edition=$2
archive=eqs-preview-20260910.zip
[[ $edition != current ]] || archive=eqs-current-20260928.zip
[[ $touch_profile == stock || $touch_profile == replacement ]] || fail 'explicit touch profile required'
[[ $edition == preview || $edition == current ]] || fail 'unknown edition'
cd /inputs
sha256sum --strict -c SHA256SUMS
if [[ $edition == current ]]; then
    cd /packages
    sha256sum --strict -c SHA256SUMS >/work/packages-hash-check.log
fi
cd /inputs
[[ ! -e /work/userdata.raw && ! -L /work/userdata.raw ]] || fail 'output already exists'
[[ ! -e /host-dev/mapper/droidian-droidian--rootfs ]] || fail 'droidian VG already mapped on host'
if vgs --noheadings -o vg_name 2>/dev/null | grep -qw droidian; then
    fail 'host already has a droidian VG; refusing activation'
fi
loop= active= mounted= proc_mounted= dev_mounted=
root=/work/root
cleanup() {
    set +e
    [[ -z $proc_mounted ]] || umount "$root/proc"
    [[ -z $dev_mounted ]] || umount "$root/dev"
    [[ -z $mounted ]] || umount "$root"
    [[ -z $active ]] || vgchange --config "$lvm_config" -an droidian
    [[ -z $loop ]] || losetup -d "$loop"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
simg2img base-userdata.img /work/userdata.raw
# Exact userdata size of the project's 256GB XT2241-2. No first-boot resize.
truncate -s 241246908416 /work/userdata.raw
# Docker's private /dev does not receive new host devtmpfs loop nodes.
free_loop=$(losetup --find)
[[ $free_loop =~ ^/dev/loop[0-9]+$ ]] || fail "unexpected free loop path: $(printf '%q' "$free_loop")"
if [[ ! -b $free_loop ]]; then
    devno=$(cat "/sys/class/block/${free_loop##*/}/dev")
    [[ $devno =~ ^7:[0-9]+$ ]] || fail 'unexpected loop device number'
    mknod -m 600 "$free_loop" b 7 "${devno#*:}"
fi
loop=$(losetup --find --show /work/userdata.raw)
[[ $loop =~ ^/dev/loop[0-9]+$ ]] || fail 'unexpected loop path'
[[ $(losetup -n -O BACK-FILE "$loop") == /work/userdata.raw ]] || fail 'loop ownership differs'
lvm_config="devices { filter = [ \"a|^$loop$|\", \"r|.*|\" ] global_filter = [ \"a|^$loop$|\", \"r|.*|\" ] } backup { backup=0 archive=0 }"
pvresize --config "$lvm_config" "$loop"
vgchange --config "$lvm_config" -ay droidian
active=yes
attr=$(lvs --config "$lvm_config" --noheadings -o lv_attr droidian/droidian-rootfs | tr -d '[:space:]')
[[ ${attr:1:1} == w ]] || lvchange --config "$lvm_config" --permission rw droidian/droidian-rootfs
lvextend --config "$lvm_config" -l +100%FREE droidian/droidian-rootfs
rootdev=/host-dev/mapper/droidian-droidian--rootfs
for i in {1..50}; do [[ ! -b $rootdev ]] || break; sleep .1; done
[[ -b $rootdev ]] || fail 'new root LV not visible'
e2fsck -fn "$rootdev"
resize2fs "$rootdev"
e2fsck -fn "$rootdev"
mkdir "$root"
mount -o nosuid,nodev "$rootdev" "$root"
mounted=yes
# RED: the untouched historical root must not pass cumulative image acceptance.
if python3 /source/port/image/verify-rootfs.py "$root" /inputs > /work/base-red.log 2>&1; then
    fail 'historical base unexpectedly already satisfies the new contract'
fi
grep -F '6.3.3-1~git20250414214107.69444e6.next.upgrade.6.3' /work/base-red.log
[[ $(chroot "$root" dpkg-query -W -f='${Version}' libqt5waylandclient5) == 5.15.15-3 ]] || fail 'Qt5 ABI differs'
# Suppress services and ALL flash triggers while configuring the one updated package.
[[ ! -e $root/usr/sbin/policy-rc.d ]] || fail 'unexpected policy-rc.d in clean base'
printf '#!/bin/sh\nexit 101\n' > "$root/usr/sbin/policy-rc.d"
chmod 755 "$root/usr/sbin/policy-rc.d"
mkdir -p "$root/etc/flash-bootimage"
printf 'FLASH_BOOTIMAGE=no\n' > "$root/etc/flash-bootimage/01prevent-flashing"
cp /inputs/plasma-mobile-wf.deb "$root/tmp/eqs-plasma.deb"
mount -t tmpfs -o nosuid tmpfs "$root/dev"
dev_mounted=yes
mknod -m 666 "$root/dev/null" c 1 3
mknod -m 666 "$root/dev/zero" c 1 5
mknod -m 666 "$root/dev/random" c 1 8
mknod -m 666 "$root/dev/urandom" c 1 9
ln -s /proc/self/fd "$root/dev/fd"
mount -t proc proc "$root/proc"
proc_mounted=yes
chroot "$root" /usr/bin/env DEBIAN_FRONTEND=noninteractive /usr/bin/dpkg --install /tmp/eqs-plasma.deb
chroot "$root" apt-mark hold plasma-mobile-wf linux-image-motorola-eqs linux-bootimage-motorola-eqs
[[ -z $(chroot "$root" dpkg --audit) ]] || fail 'dpkg audit failed'
umount "$root/proc"
proc_mounted=
umount "$root/dev"
dev_mounted=
rm "$root/tmp/eqs-plasma.deb"
python3 /source/port/image/apply-fixes.py "$root" /inputs "$touch_profile"
if [[ $edition == current ]]; then
    mkdir -p "$root/tmp/eqs-repo"
    cp /packages/*.deb "$root/tmp/eqs-repo/"
    (cd "$root/tmp/eqs-repo" && dpkg-scanpackages . /dev/null > Packages 2>/work/scan.log && gzip -9n -c Packages > Packages.gz)
    printf 'deb [trusted=yes] file:/tmp/eqs-repo ./\n' > "$root/tmp/eqs-only.list"
    mount -t tmpfs -o nosuid tmpfs "$root/dev"
    dev_mounted=yes
    mknod -m 666 "$root/dev/null" c 1 3
    mknod -m 666 "$root/dev/zero" c 1 5
    mknod -m 666 "$root/dev/random" c 1 8
    mknod -m 666 "$root/dev/urandom" c 1 9
    ln -s /proc/self/fd "$root/dev/fd"
    mount -t proc proc "$root/proc"
    proc_mounted=yes
    apt_opts=(-o Dir::Etc::sourcelist=/tmp/eqs-only.list -o Dir::Etc::sourceparts=- -o Acquire::Languages=none)
    chroot "$root" apt-get "${apt_opts[@]}" update
    chroot "$root" apt-mark unhold plasma-mobile-wf
    mobile=$(find "$root/tmp/eqs-repo" -maxdepth 1 -name 'plasma-mobile-wf_6.7.5-0+eqs1~pre2_arm64.deb' -print -quit)
    [[ -n $mobile ]] || fail 'current Mobile package missing'
    chroot "$root" dpkg --unpack --no-triggers /tmp/eqs-repo/"${mobile##*/}"
    python3 /source/port/image/current-targets.py /packages/INPUTS.json /source/port/image/current-package-versions.tsv > /work/current-targets.txt
    mapfile -t targets < /work/current-targets.txt
    [[ ${#targets[@]} == 1777 ]] || fail 'current package target count changed'
    mapfile -t obsolete < <(sed 's/$/-/' /source/port/image/current-removed-packages.txt)
    targets+=("${obsolete[@]}")
    if ! chroot "$root" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get "${apt_opts[@]}" -s --fix-broken install "${targets[@]}" > /work/current-apt-plan.log 2>&1; then
        tail -60 /work/current-apt-plan.log
        fail 'offline current upgrade simulation failed'
    fi
    if ! chroot "$root" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get "${apt_opts[@]}" -y --fix-broken --no-install-recommends install "${targets[@]}" > /work/current-install.log 2>&1; then
        tail -80 /work/current-install.log
        fail 'offline current package installation failed'
    fi
    [[ -z $(chroot "$root" dpkg --audit) ]] || fail 'current dpkg audit failed'
    chroot "$root" apt-get "${apt_opts[@]}" check
    systemctl --root="$root" disable ssh.service ssh.socket
    for key in "$root"/etc/ssh/ssh_host_*; do
        [[ ! -e $key ]] || rm "$key"
    done
    : > "$root/etc/machine-id"
    rm -f "$root/var/lib/dbus/machine-id" "$root/var/lib/systemd/random-seed"
    cp /source/port/apt/debian-sid.sources "$root/etc/apt/sources.list.d/debian-sid.sources"
    cp /source/port/apt/50-eqs-sid.pref "$root/etc/apt/preferences.d/50-eqs-sid.pref"
    mapfile -t retained < <(awk '{for (i=1; i<=NF && $i !~ /^#/; i++) print $i}' /source/port/apt/protected-packages.txt)
    [[ ${#retained[@]} == 258 ]] || fail 'retained package manifest changed'
    chroot "$root" apt-mark hold "${retained[@]}"
    mapfile -t automatic < /source/port/image/current-auto-packages.txt
    [[ ${#automatic[@]} == 1837 ]] || fail 'automatic package manifest changed'
    chroot "$root" apt-mark auto "${automatic[@]}" > /work/current-auto.log
    mapfile -t manual < /source/port/image/current-manual-packages.txt
    [[ ${#manual[@]} == 217 ]] || fail 'manual package manifest changed'
    chroot "$root" apt-mark manual "${manual[@]}" > /work/current-manual.log
    LC_ALL=C sort /source/port/image/current-auto-packages.txt > /work/expected-auto.txt
    chroot "$root" apt-mark showauto | LC_ALL=C sort > /work/actual-auto.txt
    cmp /work/expected-auto.txt /work/actual-auto.txt || fail 'APT auto/manual selections differ'
    umount "$root/proc"
    proc_mounted=
    umount "$root/dev"
    dev_mounted=
    rm -r "$root/tmp/eqs-repo"
    rm "$root/tmp/eqs-only.list"
    printf '[General]\nautoHidePanelsEnabled=true\n' > "$root/home/droidian/.config/plasmamobilerc"
    chroot "$root" chown droidian:droidian /home/droidian/.config/plasmamobilerc
    printf 'LANG=es_AR.UTF-8\nLANGUAGE=es_AR:es\n' > "$root/etc/default/locale"
fi
rm "$root/usr/sbin/policy-rc.d"
mkdir -p /work/release/{candidate,rescue}
for name in boot vendor_boot dtbo vbmeta; do
    cp "/inputs/candidate-$name.img" "$root/boot/$name.img"
    cp "/inputs/candidate-$name.img" "/work/release/candidate/$name.img"
    cp "/inputs/rescue-$name.img" "/work/release/rescue/$name.img"
done
cp /inputs/rescue-recovery.img /work/release/rescue/recovery.img
python3 /source/port/image/verify-rootfs.py "$root" /inputs "$edition" | tee /work/rootfs-green.log
dpkg-query --admindir="$root/var/lib/dpkg" -W -f='${Package}\t${Version}\t${db:Status-Abbrev}\n' | sort > /work/release/PACKAGES.tsv
lvdisplay --config "$lvm_config" droidian/droidian-rootfs > /work/release/LVM.txt
sync
umount "$root"
mounted=
e2fsck -fn "$rootdev" | tee /work/fsck-final.log
tune2fs -l "$rootdev" > /work/release/FILESYSTEM.txt
vgchange --config "$lvm_config" -an droidian
active=
losetup -d "$loop"
loop=
img2simg /work/userdata.raw /work/release/userdata.img
cp /inputs/INPUTS.json /work/release/INPUTS.json
if [[ $edition == current ]]; then
    cp /packages/INPUTS.json /work/release/CURRENT-PACKAGES.json
    cp /source/port/image/current-missing-packages.tsv /work/release/MISSING-PACKAGES.tsv
fi
cp /source/port/bringup/flash-candidate.sh /work/release/
cp /source/port/image/INSTALL.md /work/release/INSTALL.md
# Tar preserves the intentionally dangling vendor-profile alias. Plain zip -r
# dereferences it and would silently omit a required source file.
tar --exclude=__pycache__ -C /source -czf /work/release/SOURCE.tar.gz port
printf 'eqs-%s-20260928\nH29 boot; touch=%s\nuserdata_bytes=241246908416\nHOST-VERIFIED IMAGE; NEW IMAGE NOT FLASHED/HIL-VALIDATED\n' "$edition" "$touch_profile" > /work/release/RELEASE.txt
if [[ $edition == current ]]; then
    printf 'Plasma Mobile 6.7.5+eqs1~pre2; Debian Sid cohort.\n' >> /work/release/RELEASE.txt
else
    printf 'Plasma Mobile 6.3.3+eqs5; Droidian base.\n' >> /work/release/RELEASE.txt
fi
if [[ $edition == current ]]; then
    printf 'Six optional live-phone packages are absent; see MISSING-PACKAGES.tsv.\n' >> /work/release/RELEASE.txt
fi
cd /work/release
find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
# The reviewed boot-only helper uses paths without ./ in its manifest.
sed -i 's#  \./#  #' SHA256SUMS
bash flash-candidate.sh --check
zip -q -1 -r "/work/$archive" .
cd /work
sha256sum "$archive" > SHA256SUMS
echo "PASS: new clean $edition image built; no phone was accessed or flashed"
