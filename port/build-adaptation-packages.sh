#!/usr/bin/env bash
# Build and verify the minimal, host-only eqs adaptation packages.
set -euo pipefail

readonly IMAGE='quay.io/droidian/build-essential@sha256:692a6c1d280f08a6c021057fbb42c70c6ef9e0ea15a3d74d7310fa42d4887b6a'
readonly VERSION='0.1.0'
readonly EPOCH='1788264000'
readonly EQS_COMMIT='d2c017af5ae8b1aeda0b3ba5072cb99643cbe8ff'
readonly COMMON_COMMIT='9ef36ec870058f5fe4bb1b1d0213dbac7325a168'
readonly DEVICETREES_COMMIT='f02ca5e3e17fa9f6f8e3167a687f86040d0a0848'

fail() { printf 'build-adaptation-packages: %s\n' "$*" >&2; exit 1; }

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel) || fail 'must run from the worktree'
source_dir="$repo_root/port/adaptation-motorola-eqs"
artifacts="$repo_root/.work/eqs-adaptation"
eqs_source="$repo_root/reference/repos/eqs-development/android_device_motorola_eqs"
common_source="$repo_root/reference/repos/eqs-development/android_device_motorola_sm8475-common"
devicetrees_source="$repo_root/reference/repos/eqs-development/android_kernel_motorola_sm8475-devicetrees"

for tool in cmp docker find git grep mkdir mktemp rm sha256sum sort stat tar; do
    command -v "$tool" >/dev/null 2>&1 || fail "required host tool is unavailable: $tool"
done
[[ -f "$source_dir/debian/control" ]] || fail "source is missing: $source_dir"
for source in "$eqs_source" "$common_source" "$devicetrees_source"; do
    [[ -d "$source/.git" ]] || fail "local reference is missing: $source"
done
[[ $(git -C "$eqs_source" rev-parse HEAD) == "$EQS_COMMIT" ]] || fail 'eqs reference commit differs'
[[ $(git -C "$common_source" rev-parse HEAD) == "$COMMON_COMMIT" ]] || fail 'SM8475 common reference commit differs'
[[ $(git -C "$devicetrees_source" rev-parse HEAD) == "$DEVICETREES_COMMIT" ]] || fail 'SM8475 devicetrees reference commit differs'
# These local eqs/SM8475 sources prove the partition labels retained by the drop-in.
grep -Fq 'mmi,main-utags = "/dev/block/bootdevice/by-name/utags";' "$devicetrees_source/qcom/waipio-moto-common-overlay.dtsi"
grep -Fq 'mmi,backup-utags = "/dev/block/bootdevice/by-name/utagsBackup";' "$devicetrees_source/qcom/waipio-moto-common-overlay.dtsi"
grep -Fq 'mmi,main-utags = "/dev/block/bootdevice/by-name/hw";' "$devicetrees_source/qcom/waipio-moto-common-overlay.dtsi"
grep -Fq 'rootdir/etc/init/hw/' "$eqs_source/device.mk"

# A digest-pinned docker run pulls this exact image on a clean host when needed.
rm -rf -- "$artifacts"
mkdir -p "$artifacts/runs"
source_tree_sha256=$(tar --sort=name --mtime="@$EPOCH" --owner=0 --group=0 --numeric-owner -C "$source_dir" -cf - . | sha256sum | sed "s/ .*//")
stages=()
for run in one two; do
    stage=$(mktemp -d "$artifacts/runs/${run}.XXXXXX")
    stages+=("$stage")
    docker run --rm --user "$(id -u):$(id -g)" \
        --mount "type=bind,src=$source_dir,dst=/source,readonly" \
        --mount "type=bind,src=$stage,dst=/work" \
        --env "SOURCE_DATE_EPOCH=$EPOCH" --env TZ=UTC --env LC_ALL=C \
        "$IMAGE" /bin/sh -euc '
            mkdir /work/source
            tar -C /source -cf - . | tar -C /work/source -xf -
            cd /work/source
            dpkg-buildpackage -a arm64 -us -uc -b
            ! find /work/source -type f -name "*.deb" -print -quit | grep -q .
        '
done

for package in adaptation-motorola-eqs adaptation-motorola-eqs-configs; do
    deb="${package}_${VERSION}_arm64.deb"
    cmp "${stages[0]}/$deb" "${stages[1]}/$deb" || fail "non-reproducible package: $deb"
    cp "${stages[0]}/$deb" "$artifacts/$deb"
done

inspection=$(mktemp -d "$artifacts/inspection.XXXXXX")
docker run --rm --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$source_dir,dst=/source,readonly" \
    --mount "type=bind,src=$artifacts,dst=/artifacts" \
    "$IMAGE" /bin/sh -euc '
        version=$1 inspection=/artifacts/$2
        meta=/artifacts/adaptation-motorola-eqs_${version}_arm64.deb
        configs=/artifacts/adaptation-motorola-eqs-configs_${version}_arm64.deb
        test "$(dpkg-deb -f "$meta" Architecture)" = arm64
        test "$(dpkg-deb -f "$configs" Architecture)" = arm64
        dpkg-deb -f "$meta" Depends | grep -Fxq "adaptation-hybris-api32-phone, adaptation-motorola-eqs-configs, linux-bootimage-motorola-eqs, libdroid-hal-lights"
        mkdir "$inspection/meta-data" "$inspection/configs-data" "$inspection/meta-control" "$inspection/configs-control"
        dpkg-deb -x "$meta" "$inspection/meta-data"
        dpkg-deb -x "$configs" "$inspection/configs-data"
        dpkg-deb -e "$meta" "$inspection/meta-control"
        dpkg-deb -e "$configs" "$inspection/configs-control"
        test -z "$(find "$inspection/meta-data" -mindepth 1 -print -quit)"
        for control in "$inspection/meta-control" "$inspection/configs-control"; do
            test -f "$control/control"
            ! find "$control" -maxdepth 1 -type f \( -name preinst -o -name postinst -o -name prerm -o -name postrm -o -name config -o -name triggers \) -print -quit | grep -q .
        done
        test "$(find "$inspection/configs-data" -type f | wc -l)" = 6
        test "$(find "$inspection/configs-data" -type l | wc -l)" = 1
        test "$(readlink "$inspection/configs-data"/usr/lib/droid-vendor-overlay/etc/media_profiles_vendor.xml)" = media_profiles_cape.xml
        cmp /source/usr/bin/droid/droid-get-bt-address.sh "$inspection/configs-data"/usr/bin/droid/droid-get-bt-address.sh
        test "$(stat -c "%a" "$inspection/configs-data"/usr/bin/droid/droid-get-bt-address.sh)" = 755
        cmp /source/usr/lib/udev/rules.d/80-eqs-bluetooth.rules "$inspection/configs-data"/usr/lib/udev/rules.d/80-eqs-bluetooth.rules
        test "$(stat -c "%a" "$inspection/configs-data"/usr/lib/udev/rules.d/80-eqs-bluetooth.rules)" = 644
        cmp /source/etc/pulse/arm_droid_card_custom.pa "$inspection/configs-data"/etc/pulse/arm_droid_card_custom.pa
        test "$(stat -c "%a" "$inspection/configs-data"/etc/pulse/arm_droid_card_custom.pa)" = 644
        cmp /source/usr/lib/udev/rules.d/80-eqs-gpu.rules "$inspection/configs-data"/usr/lib/udev/rules.d/80-eqs-gpu.rules
        test "$(stat -c "%a" "$inspection/configs-data"/usr/lib/udev/rules.d/80-eqs-gpu.rules)" = 644
        dpkg-deb -c "$configs" | grep -Eq "^-rw-r--r-- root/root +[0-9]+ .* ./etc/systemd/system/android-mount.service.d/30-eqs-utags.conf$"
        dpkg-deb -c "$configs" | grep -Eq "^-rw-r--r-- root/root +[0-9]+ .* ./usr/lib/droidian/device/preferred-hostname$"
        test "$(stat -c "%a" "$inspection/configs-data"/usr/lib/droidian/device/preferred-hostname)" = 644
        test "$(stat -c "%a" "$inspection/configs-data"/etc/systemd/system/android-mount.service.d/30-eqs-utags.conf)" = 644
        test "$(cat "$inspection/configs-data"/usr/lib/droidian/device/preferred-hostname)" = Edge30Ultra
        cmp /source/etc/systemd/system/android-mount.service.d/30-eqs-utags.conf "$inspection/configs-data"/etc/systemd/system/android-mount.service.d/30-eqs-utags.conf
        mkdir -p "$inspection/dpkg-root"/var/lib/dpkg "$inspection/dpkg-root"/var/log "$inspection/dpkg-root"/tmp
        : > "$inspection/dpkg-root"/var/lib/dpkg/status
        dpkg --root="$inspection/dpkg-root" --admindir="$inspection/dpkg-root"/var/lib/dpkg --force-not-root --force-architecture --unpack "$configs" "$meta"
        dpkg --root="$inspection/dpkg-root" --admindir="$inspection/dpkg-root"/var/lib/dpkg --audit | grep -Fq "unpacked but not yet configured"
        test ! -e /etc/systemd/system/android-mount.service.d/30-eqs-utags.conf
    ' sh "$VERSION" "$(basename -- "$inspection")"

(cd "$artifacts" && sha256sum "adaptation-motorola-eqs_${VERSION}_arm64.deb" "adaptation-motorola-eqs-configs_${VERSION}_arm64.deb" > SHA256SUMS)
{
    printf 'HOST-ONLY / NOT HIL: packages were built and inspected, not installed on eqs.\n'
    printf 'version=%s\nsource_date_epoch=%s\n' "$VERSION" "$EPOCH"
    printf 'repository_head=%s\nsource_tree_sha256=%s\n' "$(git -C "$repo_root" rev-parse HEAD)" "$source_tree_sha256"
    printf 'eqs_device_commit=%s\nsm8475_common_commit=%s\nsm8475_devicetrees_commit=%s\n' "$(git -C "$eqs_source" rev-parse HEAD)" "$(git -C "$common_source" rev-parse HEAD)" "$(git -C "$devicetrees_source" rev-parse HEAD)"
    printf 'partlabel_evidence=android_kernel_motorola_sm8475-devicetrees/qcom/waipio-moto-common-overlay.dtsi\n'
    printf 'build_image=%s\n' "$IMAGE"
    printf 'simulation=dpkg --unpack succeeds; configuration remains blocked by intentionally absent Droidian dependencies\n'
    cat "$artifacts/SHA256SUMS"
} > "$artifacts/MANIFEST.txt"
printf 'Host-only eqs adaptation packages: %s\n' "$artifacts"
