#!/usr/bin/env bash
# Shared eqs configuration path; --check needs no Docker or hardware access.
set -euo pipefail

fail() { printf 'resolve-eqs-config: %s\n' "$*" >&2; exit 1; }
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

check_config() {
    local config=$1 profile=$2 expected key other
    [[ -s "$config" && -s "$script_dir/eqs-halium.config" ]] || fail 'missing configuration or Halium fragment'
    case "$profile" in
        thinlto) other=CONFIG_LTO_CLANG_FULL ;;
        full) other=CONFIG_LTO_CLANG_THIN ;;
        *) fail "unknown profile: $profile" ;;
    esac
    while IFS= read -r expected; do
        key=${expected%%=*}
        grep -Fxq "$expected" "$config" || fail "missing expected configuration: $expected"
        [[ $(grep -Ec "^($key=|# $key is not set$)" "$config") == 1 ]] || fail "duplicate configuration: $key"
    done < <(
        printf '%s\n' CONFIG_EQS_DTB=y CONFIG_SCSI_UFS_HID=y CONFIG_ZRAM_WRITEBACK=y \
            CONFIG_KEYBOARD_GPIO_SWAP=m CONFIG_RICHTAP_FOR_PMIC_ENABLE=y
        grep '^CONFIG_' "$script_dir/eqs-halium.config"
        if [[ $profile == thinlto ]]; then printf '%s\n' CONFIG_LTO_CLANG_THIN=y; else printf '%s\n' CONFIG_LTO_CLANG_FULL=y; fi
    )
    ! grep -Eq "^$other=[ym]$" "$config" || fail "conflicting LTO configuration: $other"
}

case "${1:-}" in
    --check)
        [[ $# == 3 ]] || fail 'usage: --check CONFIG thinlto|full'
        check_config "$2" "$3"
        printf 'eqs Halium configuration checks passed (%s): %s\n' "$3" "$2"
        exit 0
        ;;
    --resolve)
        [[ $# == 4 ]] || fail 'usage: --resolve KERNEL OUTPUT thinlto|full (inside build container)'
        kernel=$(readlink -f -- "$2")
        out=$(readlink -m -- "$3")
        profile=$4
        [[ -d "$kernel" && "$out" != "$kernel" && "$out" != / ]] || fail 'invalid kernel/output directory'
        case "$profile" in thinlto|full) ;; *) fail "unknown profile: $profile" ;; esac
        toolchain=/usr/lib/llvm-android-12.0-r416183b/bin
        [[ -x "$toolchain/clang" && -x "$toolchain/ld.lld" ]] || fail 'pinned Android Clang 12 toolchain missing; use the build container'
        export PATH="$toolchain:$PATH"
        [[ $(git -C "$kernel" rev-parse HEAD) == bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582 ]] || fail 'unexpected eqs kernel commit'
        fragments=(
            "$kernel/arch/arm64/configs/vendor/waipio_GKI.config"
            "$kernel/arch/arm64/configs/vendor/ext_config/moto-waipio.config"
            "$kernel/arch/arm64/configs/vendor/ext_config/moto-waipio-gki.config"
            "$kernel/arch/arm64/configs/vendor/ext_config/moto-waipio-eqs.config"
            "$script_dir/eqs-halium.config"
        )
        [[ $profile != thinlto ]] || fragments+=("$script_dir/eqs-dev-thinlto.config")
        for fragment in "${fragments[@]}"; do [[ -s "$fragment" ]] || fail "missing fragment: $fragment"; done
        tempdir=$(mktemp -d "${TMPDIR:-/tmp}/eqs-kconfig.XXXXXX")
        trap 'rm -rf -- "$tempdir"' EXIT
        common=(ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-
            PYTHON=/opt/android/prebuilts/python/2.7.5/bin/python2.7)
        make -C "$kernel" O="$tempdir" "${common[@]}" gki_defconfig
        (
            cd "$tempdir"
            KCONFIG_CONFIG="$tempdir/.config" "$kernel/scripts/kconfig/merge_config.sh" -m -O "$tempdir" \
                "$tempdir/.config" "${fragments[@]}"
        )
        make -C "$kernel" O="$tempdir" "${common[@]}" olddefconfig
        check_config "$tempdir/.config" "$profile"
        # Never overwrite evidence or reuse objects from a different effective config.
        if [[ -d "$out" && -n $(find "$out" -mindepth 1 -maxdepth 1 -print -quit) ]]; then
            [[ -f "$out/.config" ]] && cmp -s "$tempdir/.config" "$out/.config" || \
                fail 'output contains another configuration; preserve it and choose a fresh EQS_KERNEL_WORKDIR'
        fi
        mkdir -p -- "$out"
        cp -- "$tempdir/.config" "$out/.config"
        printf 'Resolved eqs Halium profile: %s\n' "$profile"
        "$toolchain/clang" --version
        sha256sum "$out/.config"
        exit 0
        ;;
    '') ;;
    *) fail 'usage: resolve-eqs-config.sh [--check CONFIG thinlto|full | --resolve KERNEL OUTPUT thinlto|full]' ;;
esac

# Standalone check uses the same compiler and resolver as the real build.
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
kernel_source=${EQS_KERNEL_SOURCE:-"$repo_root/reference/repos/eqs-development/android_kernel_motorola_sm8475"}
kernel_source=$(readlink -f -- "$kernel_source")
[[ -d "$kernel_source" ]] || fail "kernel source is missing: $kernel_source"
image=cyberdeck-edge30/kernel-build:local
docker image inspect "$image" >/dev/null || fail 'build image unavailable or Docker access denied; no configuration was generated'
mkdir -p "$repo_root/.work"
output=$(mktemp -d "$repo_root/.work/eqs-config.XXXXXX")
docker run --rm --pull never --network none --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$kernel_source,dst=/kernel,readonly" \
    --mount "type=bind,src=$script_dir,dst=/scripts,readonly" \
    --mount "type=bind,src=$output,dst=/output" \
    "$image" bash /scripts/resolve-eqs-config.sh --resolve /kernel /output thinlto
printf 'Host-only resolved configuration: %s/.config\nNo kernel was built and no hardware was touched.\n' "$output"
