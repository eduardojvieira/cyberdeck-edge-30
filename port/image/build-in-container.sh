#!/bin/bash
# Offline composition only: mounts a NEW regular image file, never a phone.
set -euo pipefail
fail() { echo "eqs-image: $*" >&2; exit 1; }
[[ -f /.dockerenv && $(id -u) == 0 && $# == 1 ]] || fail 'use build.sh, not the host shell'
touch_profile=$1
[[ $touch_profile == stock || $touch_profile == replacement ]] || fail 'explicit touch profile required'
cd /inputs
sha256sum --strict -c SHA256SUMS
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
[[ $free_loop =~ ^/dev/loop[0-9]+$ ]] || fail 'unexpected free loop path'
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
rm "$root/tmp/eqs-plasma.deb" "$root/usr/sbin/policy-rc.d"
python3 /source/port/image/apply-fixes.py "$root" /inputs "$touch_profile"
mkdir -p /work/release/{candidate,rescue}
for name in boot vendor_boot dtbo vbmeta; do
    cp "/inputs/candidate-$name.img" "$root/boot/$name.img"
    cp "/inputs/candidate-$name.img" "/work/release/candidate/$name.img"
    cp "/inputs/rescue-$name.img" "/work/release/rescue/$name.img"
done
cp /inputs/rescue-recovery.img /work/release/rescue/recovery.img
python3 /source/port/image/verify-rootfs.py "$root" /inputs | tee /work/rootfs-green.log
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
cp /source/port/bringup/flash-candidate.sh /work/release/
cp /source/port/image/INSTALL.md /work/release/INSTALL.md
# Tar preserves the intentionally dangling vendor-profile alias. Plain zip -r
# dereferences it and would silently omit a required source file.
tar --exclude=__pycache__ -C /source -czf /work/release/SOURCE.tar.gz port
printf 'eqs-preview-20260910\nH29 boot; Plasma eqs4; touch=%s\nuserdata_bytes=241246908416\nHOST-VERIFIED IMAGE; NEW IMAGE NOT FLASHED/HIL-VALIDATED\n' "$touch_profile" > /work/release/RELEASE.txt
cd /work/release
find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
# The reviewed boot-only helper uses paths without ./ in its manifest.
sed -i 's#  \./#  #' SHA256SUMS
bash flash-candidate.sh --check
zip -q -1 -r /work/eqs-preview-20260910.zip .
cd /work
sha256sum eqs-preview-20260910.zip > SHA256SUMS
echo 'PASS: new clean preview image built; no phone was accessed or flashed'
