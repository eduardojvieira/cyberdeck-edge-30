#!/usr/bin/env bash
# Resolve the initial eqs kernel configuration without modifying source trees.
set -euo pipefail

readonly KERNEL_RELATIVE_PATH='reference/repos/eqs-development/android_kernel_motorola_sm8475'

fail() {
    printf 'resolve-eqs-config: %s\n' "$*" >&2
    exit 1
}

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
for tool in git make mktemp grep sed cat cp rm readlink flex bison cc; do
    command -v "$tool" >/dev/null 2>&1 || fail "required host tool is unavailable: $tool"
done
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null) || \
    fail 'must run from a Git worktree containing this script'
kernel_source=${EQS_KERNEL_SOURCE:-"$repo_root/$KERNEL_RELATIVE_PATH"}

[[ -d "$kernel_source" ]] || fail "kernel source is missing: $kernel_source"

fragments=(
    'arch/arm64/configs/gki_defconfig'
    'arch/arm64/configs/vendor/waipio_GKI.config'
    'arch/arm64/configs/vendor/ext_config/moto-waipio.config'
    'arch/arm64/configs/vendor/ext_config/moto-waipio-gki.config'
    'arch/arm64/configs/vendor/ext_config/moto-waipio-eqs.config'
)

for fragment in "${fragments[@]}"; do
    [[ -f "$kernel_source/$fragment" ]] || fail "kernel fragment is missing: $kernel_source/$fragment"
done

[[ -x "$kernel_source/scripts/kconfig/merge_config.sh" ]] || \
    fail "kernel merge helper is missing: $kernel_source/scripts/kconfig/merge_config.sh"

tempdir=$(mktemp -d "${TMPDIR:-/tmp}/eqs-kconfig.XXXXXX")
trap 'rm -rf -- "$tempdir"' EXIT

printf 'Resolving eqs kernel configuration from: %s\n' "$kernel_source"
printf 'Kernel commit: %s\n' "$(git -C "$kernel_source" rev-parse HEAD 2>/dev/null || printf 'unknown')"

make -C "$kernel_source" O="$tempdir" ARCH=arm64 gki_defconfig
(
    cd "$tempdir"
    KCONFIG_CONFIG="$tempdir/.config" "$kernel_source/scripts/kconfig/merge_config.sh" -m -O "$tempdir" \
        "$tempdir/.config" \
        "$kernel_source/arch/arm64/configs/vendor/waipio_GKI.config" \
        "$kernel_source/arch/arm64/configs/vendor/ext_config/moto-waipio.config" \
        "$kernel_source/arch/arm64/configs/vendor/ext_config/moto-waipio-gki.config" \
        "$kernel_source/arch/arm64/configs/vendor/ext_config/moto-waipio-eqs.config"
)
make -C "$kernel_source" O="$tempdir" ARCH=arm64 olddefconfig

for expected in \
    CONFIG_EQS_DTB=y \
    CONFIG_SCSI_UFS_HID=y \
    CONFIG_ZRAM_WRITEBACK=y \
    CONFIG_KEYBOARD_GPIO_SWAP=m \
    CONFIG_RICHTAP_FOR_PMIC_ENABLE=y; do
    grep -Fxq "$expected" "$tempdir/.config" || fail "missing expected configuration: $expected"
done

printf '%s\n' 'eqs kernel configuration resolved successfully:'
printf '%s\n' '  CONFIG_EQS_DTB=y'
printf '%s\n' '  CONFIG_SCSI_UFS_HID=y'
printf '%s\n' '  CONFIG_ZRAM_WRITEBACK=y'
printf '%s\n' '  CONFIG_KEYBOARD_GPIO_SWAP=m'
printf '%s\n' '  CONFIG_RICHTAP_FOR_PMIC_ENABLE=y'
printf '%s\n' 'Host-only configuration evidence; no kernel image was built and no hardware was touched.'
