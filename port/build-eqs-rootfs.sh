#!/usr/bin/env bash
# Build and inspect the pinned Droidian 101 Plasma/Wayfire rootfs for eqs.
set -euo pipefail

# Default deliverable is the consolidated working port, not the September 1
# host-only experiment below. Keep historical reconstruction explicit.
case ${1:-} in
    --consolidated)
        shift
        exec "$(dirname -- "$0")/image/build.sh" "$@"
        ;;
    --historical) shift ;;
    --inspect-existing) ;;
    *)
        echo 'Use: port/build-eqs-rootfs.sh --consolidated NEW_OUTPUT_DIRECTORY stock|replacement' >&2
        echo 'Historical September 1 build only: --historical [--reuse-packages]' >&2
        exit 1
        ;;
esac

readonly DROIDIAN_COMMIT='d5b764309d9c9f401f171be603686efd5b853c4d'
readonly ROOTFS_TEMPLATES_COMMIT='d2212f43e8de78e3b759d94ee427e24268655aee'
readonly FLASHING_TEMPLATE_COMMIT='b846fa1fa3ec107e4e8675f8b82ee20bbc23866b'
readonly BUILDER='quay.io/droidian/rootfs-builder@sha256:749133320ea6d913989005ac8519630059dac465dd91d7be95066255b0ba434e'
readonly RELEASE='101.20251130'
readonly PRODUCT='motorola_eqs'

fail() { printf 'build-eqs-rootfs: %s\n' "$*" >&2; exit 1; }

reuse_packages=false
inspect_existing=false
case ${1:-} in
    --reuse-packages) reuse_packages=true; shift ;;
    --inspect-existing) inspect_existing=true; shift ;;
esac
[[ $# -eq 0 ]] || fail 'usage: port/build-eqs-rootfs.sh [--reuse-packages|--inspect-existing]'

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel) || fail 'must run from the worktree'
reference="$repo_root/reference/repos/droidian-images/droidian"
work="$repo_root/.work/eqs-rootfs"
build="$work/droidian"
out="$work/droidian/out"
apt="$build/apt"
kernel_dir="$(readlink -m -- "${EQS_KERNEL_WORKDIR:-$repo_root/.work/eqs-kernel}")/eqs-dev-packages"
adaptation_dir="$repo_root/.work/eqs-adaptation"

for tool in bash cmp cp docker find git grep mkdir rm sed sha256sum sort stat tar tee unzip; do
    command -v "$tool" >/dev/null 2>&1 || fail "required host tool is unavailable: $tool"
done

if [[ ! -d $reference/.git ]]; then
    mkdir -p "$(dirname -- "$reference")"
    git clone --recurse-submodules https://github.com/droidian-images/droidian "$reference" || \
        fail "could not bootstrap Droidian reference from HTTPS; check network access and retry"
    git -C "$reference" checkout --detach "$DROIDIAN_COMMIT" || \
        fail 'could not check out the pinned Droidian commit'
    git -C "$reference" submodule update --init --recursive || \
        fail 'could not initialize pinned Droidian submodules'
fi
[[ $(git -C "$reference" rev-parse HEAD) == "$DROIDIAN_COMMIT" ]] || fail 'Droidian reference commit differs'
[[ $(git -C "$reference/rootfs-templates" rev-parse HEAD) == "$ROOTFS_TEMPLATES_COMMIT" ]] || fail 'rootfs-templates commit differs'
[[ $(git -C "$reference/android-image-flashing-template" rev-parse HEAD) == "$FLASHING_TEMPLATE_COMMIT" ]] || fail 'android-image-flashing-template commit differs'
[[ -z $(git -C "$reference" status --porcelain) ]] || fail 'Droidian reference must be clean'
if ! $inspect_existing; then
    # debos must execute the arm64 second stage.  Registering binfmt changes the
    # host kernel and is intentionally an explicit prerequisite, not a side effect.
    [[ -r /proc/sys/fs/binfmt_misc/qemu-aarch64 ]] || fail 'qemu-aarch64 binfmt is not registered; enable it with the host-approved QEMU setup before building'
fi

# The upstream image builder and the read-only inspector both use this VG name.
# Never activate or deactivate an existing host VG with the same name.
if docker run --rm --privileged "$BUILDER" vgs droidian >/dev/null 2>&1; then
    fail 'host volume group droidian already exists; refusing to touch it'
fi

if ! $inspect_existing && ! $reuse_packages; then
    "$repo_root/port/kernel/build-dev-packages.sh"
    "$repo_root/port/build-adaptation-packages.sh"
fi

declare -a debs=(
    "$kernel_dir/linux-image-motorola-eqs_5.10.209+git20240821.bd42a1bb-1~eqsdev2_arm64.deb"
    "$kernel_dir/linux-bootimage-motorola-eqs_5.10.209+git20240821.bd42a1bb-1~eqsdev2_arm64.deb"
    "$adaptation_dir/adaptation-motorola-eqs_0.1.0_arm64.deb"
    "$adaptation_dir/adaptation-motorola-eqs-configs_0.1.0_arm64.deb"
)
for deb in "${debs[@]}"; do
    [[ -f $deb ]] || fail "missing local package: $deb"
    if $inspect_existing; then
        [[ -f $apt/${deb##*/} ]] || fail "inspection APT repository is missing ${deb##*/}"
        cmp "$deb" "$apt/${deb##*/}"
    fi
done
if $inspect_existing; then
    [[ -f $apt/local-packages.tsv ]] || fail 'inspection APT repository is missing local-packages.tsv'
fi

if ! $inspect_existing; then
rm -rf -- "$work"
mkdir -p "$work"
cp -a "$reference/." "$build/"
flasher_template="$build/android-image-flashing-template/template/flash_all.sh"
[[ -f $flasher_template ]] || fail 'Droidian flashing template is missing'
# eqs userdata is raw in AP Fastboot: use the accepted erase operation, then
# transfer through panic-RNDIS without the optional progress utility.
sed -i \
    -e 's/check_deps ping telnet nc pv/check_deps ping telnet nc/' \
    -e 's/fastboot format "${partition}"/fastboot -s "${DEVICE}" erase "${partition}"/' \
    -e 's/pv userdata-raw.img | nc/cat userdata-raw.img | nc/' \
    "$flasher_template"
grep -Fq 'check_deps ping telnet nc' "$flasher_template"
grep -Fq 'fastboot -s "${DEVICE}" erase "${partition}"' "$flasher_template"
grep -Fq 'if cat userdata-raw.img | nc -q 0 192.168.2.15 12345; then' "$flasher_template"
! grep -Fq 'pv userdata-raw.img' "$flasher_template"
snapshot_clean="$build/rootfs-templates/scripts/clean.sh"
expected_snapshot_cleanup=$'# Workaround until droidian-update-service is in the archive\nif ! grep -q next /etc/apt/apt.conf.d/90-droidian-snapshot; then\n  rm -f /etc/apt/apt.conf.d/90-droidian-snapshot\nfi'
[[ $(sed -n '/^# Workaround until droidian-update-service is in the archive$/,/^fi$/p' "$snapshot_clean") == "$expected_snapshot_cleanup" ]] || fail 'unexpected upstream snapshot cleanup block'
sed -i '/^# Workaround until droidian-update-service is in the archive$/,/^fi$/d' "$snapshot_clean"
! grep -Fq 'rm -f /etc/apt/apt.conf.d/90-droidian-snapshot' "$snapshot_clean"
grep -Fqx 'if [ -f "/usr/bin/flatpak" ]; then' "$snapshot_clean"
grep -Fqx '   flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo' "$snapshot_clean"
mkdir -p "$out"
rm -rf -- "$apt"/*
cp -- "${debs[@]}" "$apt/"
docker run --rm --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$apt,dst=/apt" \
    "$BUILDER" /bin/sh -ec '
        cd /apt
        : > local-packages.tsv
        for deb in *.deb; do
            test "$(dpkg-deb -f "$deb" Architecture)" = arm64
            printf "%s\t%s\t%s\n" "$(dpkg-deb -f "$deb" Package)" "$(dpkg-deb -f "$deb" Version)" "$(sha256sum "$deb" | cut -d " " -f1)" >> local-packages.tsv
        done
        dpkg-scanpackages --multiversion . /dev/null > Packages
        gzip -9n -c Packages > Packages.gz
    '

cat > "$build/community_devices.yml" <<'EOF'
motorola_eqs:
  type: image
  arch: arm64
  edition: plamo_wf_experimental
  variant: phone
  apilevel: 32
  use_internal_repository: true
  packages:
    - adaptation-motorola-eqs
    - adaptation-motorola-eqs-configs
    - linux-image-motorola-eqs
    - linux-bootimage-motorola-eqs
    - openssh-client
EOF

(
    cd "$build"
    DROIDIAN_VERSION="$RELEASE" ./generate_device_recipe.py "$PRODUCT" arm64 plamo_wf_experimental phone 32
)
grep -Fq '$edition := or .edition "plamo_wf_experimental"' "$build/generated/droidian.yaml"
grep -Fq '$apilevel := or .apilevel 32' "$build/generated/droidian.yaml"
grep -Fq '$version := or .version "101.20251130"' "$build/generated/droidian.yaml"
grep -Fq 'droidian-plamo-wf-full' "$build/rootfs-templates/droidian_plamo_wf_experimental.yaml"
grep -Fq 'packages: adaptation-motorola-eqs adaptation-motorola-eqs-configs linux-image-motorola-eqs linux-bootimage-motorola-eqs openssh-client' "$build/generated/product.yaml"

# The official builder creates the LVM userdata image and fastboot zip.  Its
# network access is limited to the Droidian snapshot pinned by RELEASE.
docker run --rm --privileged --cgroupns=host \
    --mount "type=bind,src=$out,dst=/buildd/out" \
    --mount "type=bind,src=/dev,dst=/host-dev" \
    --mount "type=bind,src=/sys/fs/cgroup,dst=/sys/fs/cgroup" \
    --mount "type=bind,src=$build,dst=/buildd/sources" \
    --security-opt seccomp=unconfined \
    "$BUILDER" /bin/sh -ec 'cd /buildd/sources && debos --disable-fakemachine generated/droidian.yaml' 2>&1 | tee "$work/build.log"
grep -Fq 'snapshots/101.20251130/' "$work/build.log" || fail 'builder did not use the pinned Droidian snapshot'
if grep -Fq 'http://releases.droidian.org/snapshots/current/' "$work/build.log"; then
    fail 'builder resolved packages from Droidian current instead of the pinned snapshot'
fi
fi

zip=$(find "$out" -maxdepth 1 -type f -name 'droidian-UNOFFICIAL-plamo_wf_experimental-phone-motorola_eqs-api32-arm64-101.20251130_*.zip' -print -quit)
[[ -n $zip ]] || fail 'official builder did not produce the eqs fastboot zip'
inspection="$work/inspection"
rm -rf -- "$inspection"
mkdir -p "$inspection/zip"
unzip -q "$zip" -d "$inspection/zip"
[[ -f $inspection/zip/data/userdata.img ]] || fail 'fastboot zip is missing userdata.img'
for image in boot.img dtbo.img vbmeta.img vendor_boot.img userdata.img; do
    [[ -f $inspection/zip/data/$image ]] || fail "fastboot zip is missing data/$image"
done
[[ ! -e $inspection/zip/data/recovery.img ]] || fail 'fastboot zip unexpectedly includes recovery.img'
grep -Fxq 'DEVICE_IS_AB=yes' "$inspection/zip/data/device-configuration.conf"
grep -Fxq 'DEVICE_HAS_VENDORBOOT_PARTITION=yes' "$inspection/zip/data/device-configuration.conf"
grep -Fxq 'USERDATA_FLASHING_METHOD=telnet' "$inspection/zip/data/device-configuration.conf"
grep -Fxq 'EXTRA_INFO_DEVICE_IDS="eqs"' "$inspection/zip/data/device-configuration.conf"
bash -n "$inspection/zip/flash_all.sh"
grep -Fq 'check_deps ping telnet nc' "$inspection/zip/flash_all.sh"
grep -Fq 'fastboot -s "${DEVICE}" erase "${partition}"' "$inspection/zip/flash_all.sh"
grep -Fq 'if cat userdata-raw.img | nc -q 0 192.168.2.15 12345; then' "$inspection/zip/flash_all.sh"
! grep -Fq 'pv userdata-raw.img' "$inspection/zip/flash_all.sh"

# Exercise the generated flasher against fake host commands only.  This proves
# its A/B, raw-userdata erase, panic-RNDIS transfer and product gate paths.
flasher_test="$inspection/flasher-test"
mkdir -p "$flasher_test/bin"
cat > "$flasher_test/bin/fastboot" <<'EOF'
#!/bin/sh
case "$1" in
    devices) printf 'TEST-EQS\tfastboot\n' ;;
    -s)
        [ "$2" = TEST-EQS ] || exit 2
        case "$3" in
            getvar) printf 'product: %s\n' "${FAKE_FASTBOOT_PRODUCT:?}" ;;
            flash) printf 'flash %s %s\n' "$4" "$5" >> "$FAKE_FASTBOOT_LOG" ;;
            erase) printf 'erase %s\n' "$4" >> "$FAKE_FASTBOOT_LOG" ;;
            reboot) printf 'reboot\n' >> "$FAKE_FASTBOOT_LOG" ;;
            *) exit 2 ;;
        esac
        ;;
    *) exit 2 ;;
esac
EOF
cat > "$flasher_test/bin/sleep" <<'EOF'
#!/bin/sh
exit 0
EOF
cat > "$flasher_test/bin/ping" <<'EOF'
#!/bin/sh
exit 0
EOF
cat > "$flasher_test/bin/simg2img" <<'EOF'
#!/bin/sh
: > "$2"
EOF
cat > "$flasher_test/bin/telnet" <<'EOF'
#!/bin/sh
cat >> "$FAKE_TELNET_LOG"
EOF
cat > "$flasher_test/bin/nc" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "$FAKE_NC_LOG"
cat >/dev/null
EOF
chmod +x "$flasher_test/bin/fastboot" "$flasher_test/bin/sleep" "$flasher_test/bin/ping" "$flasher_test/bin/simg2img" "$flasher_test/bin/telnet" "$flasher_test/bin/nc"
cat > "$flasher_test/expected-eqs.log" <<'EOF'
flash boot_a data/boot.img
flash boot_b data/boot.img
flash dtbo_a data/dtbo.img
flash dtbo_b data/dtbo.img
flash vbmeta_a data/vbmeta.img
flash vbmeta_b data/vbmeta.img
flash vendor_boot_a data/vendor_boot.img
flash vendor_boot_b data/vendor_boot.img
erase userdata
reboot
EOF
: > "$flasher_test/eqs.log"
: > "$flasher_test/telnet.log"
: > "$flasher_test/nc.log"
(
    cd "$inspection/zip"
    PATH="$flasher_test/bin:$PATH" FAKE_FASTBOOT_PRODUCT=eqs FAKE_FASTBOOT_LOG="$flasher_test/eqs.log" FAKE_TELNET_LOG="$flasher_test/telnet.log" FAKE_NC_LOG="$flasher_test/nc.log" bash ./flash_all.sh
) > "$flasher_test/eqs.stdout" 2> "$flasher_test/eqs.stderr"
cmp "$flasher_test/expected-eqs.log" "$flasher_test/eqs.log"
grep -Fqx 'nc -l -p 12345 > /dev/disk/by-partlabel/userdata' "$flasher_test/telnet.log"
grep -Fqx 'reboot -f' "$flasher_test/telnet.log"
grep -Fqx -- '-q 0 192.168.2.15 12345' "$flasher_test/nc.log"
: > "$flasher_test/bronco.log"
if (
    cd "$inspection/zip"
    PATH="$flasher_test/bin:$PATH" FAKE_FASTBOOT_PRODUCT=bronco FAKE_FASTBOOT_LOG="$flasher_test/bronco.log" FAKE_TELNET_LOG="$flasher_test/telnet.log" FAKE_NC_LOG="$flasher_test/nc.log" bash ./flash_all.sh
) > "$flasher_test/bronco.stdout" 2> "$flasher_test/bronco.stderr"; then
    fail 'generated flasher accepted a non-eqs product'
fi
[[ ! -s $flasher_test/bronco.log ]] || fail 'generated flasher issued flash for a non-eqs product'
cp "$apt/local-packages.tsv" "$inspection/local-packages.tsv"

# Read-only inspection is isolated in the builder container.  The temporary
# loop device is read-only and is always deactivated/unmounted before exit.
docker run --rm --privileged --cgroupns=host \
    --mount "type=bind,src=$inspection,dst=/inspection" \
    --mount "type=bind,src=/dev,dst=/host-dev" \
    --security-opt seccomp=unconfined \
    "$BUILDER" /bin/sh -ec '
        set -eu
        raw=/tmp/userdata.raw mountpoint=/tmp/eqs-rootfs
        loop= rootdev= mounted= active=
        cleanup() {
            [ -z "$mounted" ] || umount "$mountpoint"
            [ -z "$active" ] || vgchange -an droidian >/dev/null 2>&1 || true
            [ -z "$loop" ] || losetup -d "$loop" >/dev/null 2>&1 || true
            rm -f "$raw"
        }
        trap cleanup EXIT HUP INT TERM
        simg2img /inspection/zip/data/userdata.img "$raw"
        loop=$(losetup --read-only --find --show "$raw")
        vgchange -ay droidian >/dev/null
        active=1
        rootdev=/host-dev/mapper/droidian-droidian--rootfs
        mkdir -p "$mountpoint"
        mount -o ro,noload "$rootdev" "$mountpoint"
        mounted=1
        report=/inspection/ROOTFS-INSPECTION.txt
        : > "$report"
        dpkg-query --admindir="$mountpoint/var/lib/dpkg" -W -f="\${db:Status-Abbrev}\t\${Package}\t\${Version}\t\${Architecture}\n" | awk "\$1 == \"ii\" { print \$2 \"\\t\" \$3 \"\\t\" \$4 }" | sort > /inspection/PACKAGES.tsv
        printf "rootfs_architecture=" >> "$report"
        readelf -h "$mountpoint/bin/sh" | awk -F: "/Machine:/{gsub(/^ +/, \"\", \$2); print \$2}" >> "$report"
        grep -Eq "^ID=droidian$" "$mountpoint/etc/os-release"
        grep -Eq "^VERSION=.*101" "$mountpoint/etc/os-release"
        cat "$mountpoint/etc/os-release" >> "$report"
        snapshot_pin="$mountpoint/etc/apt/apt.conf.d/90-droidian-snapshot"
        grep -Fxq "Acquire::Droidian::Version \"101.20251130\";" "$snapshot_pin"
        printf "snapshot_pin=%s\\n" "$(cat "$snapshot_pin")" >> "$report"
        package_version() {
            awk -v wanted="$1" "BEGIN {RS=\"\"; FS=\"\\n\"} \$1 == \"Package: \" wanted { for (i = 1; i <= NF; i++) { if (\$i ~ /^Status: /) status=\$i; if (\$i ~ /^Version: /) version=\$i } if (status != \"Status: install ok installed\") exit 1; sub(/^Version: /, \"\", version); print version; exit } END { if (!version) exit 1 }" "$mountpoint/var/lib/dpkg/status"
        }
        while IFS="$(printf \"\\t\")" read -r package version digest; do
            installed=$(package_version "$package")
            test "$installed" = "$version"
            printf "local_package=%s version=%s sha256=%s\n" "$package" "$installed" "$digest" >> "$report"
        done < /inspection/local-packages.tsv
        for package in droidian-plamo-wf-full plasma-mobile-wf plasma-mobile-wf-config-hwcomposer droidian-quirks-plamo-wf wayfire libhybris; do
            printf "plasma_component=%s version=%s\n" "$package" "$(package_version "$package")" >> "$report"
        done
        for package in openssh-client qmlkonsole network-manager xwayland; do
            printf "runtime_component=%s version=%s\n" "$package" "$(package_version "$package")" >> "$report"
        done
        for executable in /usr/bin/ssh /usr/bin/qmlkonsole /usr/bin/Xwayland; do
            test -x "$mountpoint$executable"
            printf "runtime_executable=%s\n" "$executable" >> "$report"
        done
        service_link="$mountpoint/etc/systemd/system/graphical.target.wants/plasma-mobile-wf.service"
        test -L "$service_link"
        service_target=$(readlink "$service_link")
        case "$service_target" in
            /*) service="$mountpoint$service_target" ;;
            *) service="$(dirname "$service_link")/$service_target" ;;
        esac
        test -f "$service"
        test "$(basename "$service")" = plasma-mobile-wf.service
        grep -Fxq "ExecStart=/usr/bin/startplasmamobile-wf" "$service"
        grep -Fxq "xwayland = true" "$mountpoint/usr/share/plasma-mobile-wf/wayfire.ini"
        if package_version phosh >/dev/null 2>&1 || package_version phoc >/dev/null 2>&1 || package_version openssh-server >/dev/null 2>&1; then exit 1; fi
        find "$mountpoint/boot" -maxdepth 1 -type f -name "*.img" -printf "%f\\n" | sort > /inspection/boot-files.txt
        printf "boot.img\ndtbo.img\nvbmeta.img\nvendor_boot.img\n" > /tmp/expected-boot-files.txt
        cmp /tmp/expected-boot-files.txt /inspection/boot-files.txt
        for image in boot.img dtbo.img vbmeta.img vendor_boot.img; do
            cmp "$mountpoint/boot/$image" "/inspection/zip/data/$image"
            (cd "$mountpoint/boot" && sha256sum "$image" | sed "s#  #  boot/#") >> "$report"
        done
    ' 2>&1 | tee "$inspection/inspection.log"
zip_relative=${zip#"$repo_root/"}
[[ $zip_relative != "$zip" ]] || fail 'fastboot zip is outside the worktree'
read -r zip_sha _ < <(sha256sum "$zip")
printf '%s  %s\n' "$zip_sha" "$zip_relative" > "$work/SHA256SUMS"
(cd "$repo_root" && sha256sum -c "$work/SHA256SUMS")
{
    printf 'HOST-ONLY / NOT HIL: generated by the official Droidian image path; never flashed or booted on eqs.\n'
    printf 'droidian_commit=%s\nrootfs_templates_commit=%s\nflashing_template_commit=%s\n' "$DROIDIAN_COMMIT" "$ROOTFS_TEMPLATES_COMMIT" "$FLASHING_TEMPLATE_COMMIT"
    printf 'builder=%s\nrelease=%s\nproduct=%s\ndroidian_version=%s\n' "$BUILDER" "$RELEASE" "$PRODUCT" "$RELEASE"
    (cd "$build" && sha256sum generated/droidian.yaml)
    printf 'local_repository=apt/ with dpkg-scanpackages Packages + Packages.gz\n'
    printf 'reproducibility=Inputs and local .deb/boot files are pinned; upstream genimage includes variable UUID/LVM/timestamps, so ZIP bytes are not promised identical.\n'
    printf 'WARNING=development rootfs; upstream template defaults to PIN 1234. Change it before networking; daily encryption/security is not implemented here.\n'
    printf '\nLOCAL PACKAGES\n'
    cat "$inspection/local-packages.tsv"
    printf '\nROOTFS INSPECTION\n'
    cat "$inspection/ROOTFS-INSPECTION.txt"
    printf '\nINSTALLED PACKAGES\n'
    cat "$inspection/PACKAGES.tsv"
    printf '\nROOTFS ARTIFACTS\n'
    stat -c '%s %n' "$zip"
    cat "$work/SHA256SUMS"
} > "$work/MANIFEST.txt"

printf 'Host-only eqs Droidian Plasma rootfs: %s\n' "$zip"
