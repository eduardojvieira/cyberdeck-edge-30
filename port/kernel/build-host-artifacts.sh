#!/usr/bin/env bash
# Build non-flashable eqs kernel artifacts from isolated local source clones.
set -euo pipefail

readonly IMAGE='cyberdeck-edge30/kernel-build:local'
readonly KERNEL_COMMIT='bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582'
readonly DEVICETREES_COMMIT='f02ca5e3e17fa9f6f8e3167a687f86040d0a0848'
readonly MODULES_COMMIT='9f8d247d457622c08ff547e5498e6fa453e876ed'
readonly COMMON_DEVICE_COMMIT='9ef36ec870058f5fe4bb1b1d0213dbac7325a168'
readonly LINEAGE_VENDOR_COMMIT='85fbbf9a6601ca7af759aa0aa06d32f7a9800b36'
readonly DTC_COMMIT='fd8c8a25dac5f2cc083348f6a3916424b688a508'
readonly LIBUFDT_COMMIT='4cc0d8f7e5d26ed1f7b98aa8f325f51e5bb1dcbd'

fail() {
    printf 'build-host-artifacts: %s\n' "$*" >&2
    exit 1
}

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
for tool in git docker mkdir readlink find grep sort wc readelf modinfo; do
    command -v "$tool" >/dev/null 2>&1 || fail "required host tool is unavailable: $tool"
done
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel 2>/dev/null) || \
    fail 'must run from a Git worktree containing this script'

targets=("$@")
if [[ ${#targets[@]} -eq 0 ]]; then
    targets=(dtbs)
fi
dev_thinlto=1
exact_image=0
display_modules=0
touch_modules=0
functional_modules=0
dt_images=0
build_targets=()
for target in "${targets[@]}"; do
    case "$target" in
        dtbs) build_targets+=("$target") ;;
        Image)
            exact_image=1
            build_targets+=("$target")
            ;;
        Image-dev-thinlto)
            dev_thinlto=1
            build_targets+=(Image)
            ;;
        modules-dev-display)
            dev_thinlto=1
            display_modules=1
            build_targets+=(Image modules)
            ;;
        modules-dev-touch)
            dev_thinlto=1
            touch_modules=1
            build_targets+=(Image modules)
            ;;
        modules-dev-functional)
            dev_thinlto=1
            functional_modules=1
            build_targets+=(Image modules)
            ;;
        dt-images-dev)
            dt_images=1
            build_targets+=(dtbs)
            ;;
        *) fail "unsupported target: $target (supported: dtbs, Image, Image-dev-thinlto, modules-dev-display, modules-dev-touch, modules-dev-functional, dt-images-dev)" ;;
    esac
done
if (( exact_image )); then
    [[ ${#targets[@]} == 1 ]] || fail 'Full LTO Image must be built separately'
    dev_thinlto=0
fi
if (( (display_modules || touch_modules || functional_modules) && ${#targets[@]} != 1 )); then
    fail 'module build targets cannot be combined with other targets'
fi

reference_repos="$repo_root/reference/repos"
references="$reference_repos/eqs-development"
worktree=$(readlink -m -- "${EQS_KERNEL_WORKDIR:-$repo_root/.work/eqs-kernel}")

check_repo() {
    local name=$1 path=$2 commit=$3 actual status
    [[ -d "$path/.git" ]] || fail "$name source is missing: $path"
    actual=$(git -C "$path" rev-parse HEAD) || fail "$name has no HEAD: $path"
    [[ "$actual" == "$commit" ]] || fail "$name commit mismatch: expected $commit, found $actual"
    status=$(git -C "$path" status --porcelain) || fail "cannot inspect $name: $path"
    [[ -z "$status" ]] || fail "$name is not clean: $path"
}

kernel_reference="$references/android_kernel_motorola_sm8475"
devicetrees_reference="$references/android_kernel_motorola_sm8475-devicetrees"
modules_reference="$references/android_kernel_motorola_sm8475-modules"
common_device_reference="$references/android_device_motorola_sm8475-common"
check_repo kernel "$kernel_reference" "$KERNEL_COMMIT"
check_repo devicetrees "$devicetrees_reference" "$DEVICETREES_COMMIT"
check_repo modules "$modules_reference" "$MODULES_COMMIT"
check_repo common-device "$common_device_reference" "$COMMON_DEVICE_COMMIT"

lineage_vendor_reference="$reference_repos/LineageOS/android_vendor_lineage"
dtc_reference="$reference_repos/LineageOS/android_external_dtc"
libufdt_reference="$reference_repos/aosp-mirror/platform_system_libufdt"
if (( dt_images )); then
    check_repo lineage-vendor "$lineage_vendor_reference" "$LINEAGE_VENDOR_COMMIT"
    check_repo external-dtc "$dtc_reference" "$DTC_COMMIT"
    check_repo libufdt "$libufdt_reference" "$LIBUFDT_COMMIT"
fi

if [[ ! -e "$worktree" ]]; then
    mkdir -p "$(dirname -- "$worktree")"
    git clone --shared "$kernel_reference" "$worktree/kernel"
    git clone --shared "$devicetrees_reference" "$worktree/sm8475-devicetrees"
    git clone --shared "$modules_reference" "$worktree/sm8475-modules"
fi

check_repo staged-kernel "$worktree/kernel" "$KERNEL_COMMIT"
check_repo staged-devicetrees "$worktree/sm8475-devicetrees" "$DEVICETREES_COMMIT"
check_repo staged-modules "$worktree/sm8475-modules" "$MODULES_COMMIT"

vendor_link="$worktree/kernel/arch/arm64/boot/dts/vendor"
[[ -L "$vendor_link" ]] || fail "kernel vendor devicetree link is missing: $vendor_link"
[[ "$(readlink "$vendor_link")" == '../../../../../sm8475-devicetrees' ]] || \
    fail "kernel vendor devicetree link differs from the tracked layout: $vendor_link"
[[ "$(readlink -f "$vendor_link")" == "$worktree/sm8475-devicetrees" ]] || \
    fail "kernel vendor devicetree link does not resolve to staged devicetrees"

docker image inspect "$IMAGE" >/dev/null || fail "local build image unavailable; build port/kernel/Dockerfile explicitly before retrying"
mkdir -p "$worktree/out"

docker run --rm \
    --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$worktree,dst=/build" \
    --mount "type=bind,src=$script_dir,dst=/scripts,readonly" \
    --mount "type=bind,src=$reference_repos,dst=/references,readonly" \
    --env "EQS_DEV_THINLTO=$dev_thinlto" \
    --env "EQS_DISPLAY_MODULES=$display_modules" \
    --env "EQS_TOUCH_MODULES=$touch_modules" \
    --env "EQS_FUNCTIONAL_MODULES=$functional_modules" \
    --env "EQS_DT_IMAGES=$dt_images" \
    --workdir /build \
    "$IMAGE" \
    /bin/bash -euc '
        export PATH=/usr/lib/llvm-android-12.0-r416183b/bin:$PATH
        build_epoch=$(LC_ALL=C TZ=UTC git -C /build/kernel show -s --format=%ct HEAD)
        build_timestamp=$(LC_ALL=C TZ=UTC date -u -d "@$build_epoch" "+%a %b %e %T %Y")
        common=(
            ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-
            PYTHON=/opt/android/prebuilts/python/2.7.5/bin/python2.7
            KBUILD_BUILD_VERSION=1 KBUILD_BUILD_USER=cyberdeck KBUILD_BUILD_HOST=eqs-build
            "KBUILD_BUILD_TIMESTAMP=$build_timestamp"
        )
        dtc_includes="/build/sm8475-modules/qcom/opensource/audio-kernel/include /build/sm8475-modules/qcom/opensource/camera-kernel"
        profile=full
        [[ "$EQS_DEV_THINLTO" != 1 ]] || profile=thinlto
        bash /scripts/resolve-eqs-config.sh --resolve /build/kernel /build/out "$profile"
        if [[ "$EQS_DEV_THINLTO" == 1 ]]; then
            rm -f /build/out/arch/arm64/boot/Image
            common+=(LD=/usr/local/bin/ld.lld-single-thread)
        fi
        KBUILD_DTC_INCLUDE="$dtc_includes" make -j1 -C /build/kernel O=/build/out "${common[@]}" "$@"
        if [[ "$EQS_DT_IMAGES" == 1 ]]; then
            tools=/build/host-tools
            stage=/build/dt-images-dev
            rm -rf "$tools" "$stage"
            mkdir -p "$tools/bin" "$stage/base" "$stage/techpacks" "$stage/merged"
            git -C /references/LineageOS/android_external_dtc archive HEAD | tar -x -C "$tools"
            make -j1 -C "$tools" NO_PYTHON=1 EXTRA_CFLAGS=-Wno-error=sign-compare
            install -m 0755 "$tools"/fdtget "$tools"/fdtput "$tools"/fdtoverlay "$tools"/fdtoverlaymerge "$tools/bin/"
            gcc -Wall -Werror \
                -I/references/aosp-mirror/platform_system_libufdt/include \
                -I/references/aosp-mirror/platform_system_libufdt/sysdeps/include \
                -I"$tools/libfdt" \
                /references/aosp-mirror/platform_system_libufdt/tests/src/ufdt_overlay_test_app.c \
                /references/aosp-mirror/platform_system_libufdt/tests/src/util.c \
                /references/aosp-mirror/platform_system_libufdt/ufdt_overlay.c \
                /references/aosp-mirror/platform_system_libufdt/ufdt_convert.c \
                /references/aosp-mirror/platform_system_libufdt/ufdt_node.c \
                /references/aosp-mirror/platform_system_libufdt/ufdt_node_pool.c \
                /references/aosp-mirror/platform_system_libufdt/ufdt_prop_dict.c \
                /references/aosp-mirror/platform_system_libufdt/sysdeps/libufdt_sysdeps_posix.c \
                "$tools/libfdt/libfdt.a" -o "$tools/bin/ufdt_apply_overlay"
            install -m 0755 /references/aosp-mirror/platform_system_libufdt/utils/src/mkdtboimg.py "$tools/bin/mkdtboimg"

            qcom=/build/out/arch/arm64/boot/dts/vendor/qcom
            for dt in "$qcom"/cape-moto-eqs-base.dtb "$qcom"/cape-v2-moto-eqs-base.dtb "$qcom"/cape-eqs-*-overlay.dtbo; do
                cp "$dt" "$stage/base/"
            done
            find "$qcom" -mindepth 2 -type f \( -name "*.dtb" -o -name "*.dtbo" \) -print0 | \
                while IFS= read -r -d "" dt; do
                    cp --parents "$dt" "$stage/techpacks/"
                done
            export PATH="$tools/bin:$PATH"
            export LD_LIBRARY_PATH="$tools/libfdt${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
            python3 /references/LineageOS/android_vendor_lineage/build/tools/merge_dtbs.py \
                "$stage/base" "$stage/techpacks/build/out/arch/arm64/boot/dts/vendor/qcom" "$stage/merged"
            mapfile -t merged_dtbs < <(find "$stage/merged" -type f -name "*.dtb" | sort)
            mapfile -t merged_dtbos < <(find "$stage/merged" -type f -name "*.dtbo" | sort)
            ((${#merged_dtbs[@]} == 2)) || { echo "expected 2 merged eqs DTBs, found ${#merged_dtbs[@]}" >&2; exit 1; }
            ((${#merged_dtbos[@]} == 8)) || { echo "expected 8 merged eqs DTBOs, found ${#merged_dtbos[@]}" >&2; exit 1; }
            for dt in "${merged_dtbs[@]}" "${merged_dtbos[@]}"; do
                [[ $(basename "$dt") == *eqs* ]] || { echo "non-eqs merged output: $dt" >&2; exit 1; }
                fdtget -t i "$dt" / qcom,msm-id >/dev/null
                fdtget -t i "$dt" / qcom,board-id >/dev/null
            done
            cat "${merged_dtbs[@]}" > "$stage/dtb.img"
            "$tools/bin/mkdtboimg" create "$stage/dtbo.img" --page_size=4096 "${merged_dtbos[@]}"
            "$tools/bin/mkdtboimg" dump "$stage/dtbo.img" > "$stage/dtbo.dump"
            (cd "$stage" && sha256sum dtb.img dtbo.img > SHA256SUMS)
        fi
        if [[ "$EQS_DISPLAY_MODULES" == 1 || "$EQS_TOUCH_MODULES" == 1 || "$EQS_FUNCTIONAL_MODULES" == 1 ]]; then
            module_root=/build/modules-dev-display
            if [[ "$EQS_TOUCH_MODULES" == 1 || "$EQS_FUNCTIONAL_MODULES" == 1 ]]; then
                module_root=/build/modules-dev-touch
            fi
            if [[ "$EQS_FUNCTIONAL_MODULES" == 1 ]]; then
                module_root=/build/modules-dev-functional
            fi
            rm -rf "$module_root"
            mkdir -p "$module_root"
            git -C /build/sm8475-modules archive HEAD qcom/opensource/mmrm-driver qcom/opensource/display-drivers | tar -x -C "$module_root"
            mmrm="$module_root/qcom/opensource/mmrm-driver"
            display="$module_root/qcom/opensource/display-drivers"
            make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$mmrm" KERNEL_SRC=/build/kernel MMRM_ROOT="$mmrm" BOARD_PLATFORM=waipio modules
            make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$display" KERNEL_SRC=/build/kernel DISPLAY_ROOT="$display" KBUILD_EXTRA_SYMBOLS="$mmrm/Module.symvers" CONFIG_DRM_MSM=m MODNAME=msm_drm BOARD_PLATFORM=waipio modules
            if [[ "$EQS_TOUCH_MODULES" == 1 || "$EQS_FUNCTIONAL_MODULES" == 1 ]]; then
                git -C /build/sm8475-modules archive HEAD \
                    motorola/drivers/mmi_annotate \
                    motorola/drivers/mmi_info \
                    motorola/drivers/mmi_relay \
                    motorola/drivers/sensors \
                    motorola/drivers/input/touchscreen/touchscreen_mmi \
                    motorola/drivers/input/touchscreen/goodix_berlin_mmi | tar -x -C "$module_root"
                annotate="$module_root/motorola/drivers/mmi_annotate"
                info="$module_root/motorola/drivers/mmi_info"
                relay="$module_root/motorola/drivers/mmi_relay"
                sensors="$module_root/motorola/drivers/sensors"
                touchscreen="$module_root/motorola/drivers/input/touchscreen/touchscreen_mmi"
                goodix="$module_root/motorola/drivers/input/touchscreen/goodix_berlin_mmi"
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$annotate" KERNEL_SRC=/build/kernel modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$info" KERNEL_SRC=/build/kernel KBUILD_EXTRA_SYMBOLS="$annotate/Module.symvers" modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$relay" KERNEL_SRC=/build/kernel modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$sensors" KERNEL_SRC=/build/kernel modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$touchscreen" KERNEL_SRC=/build/kernel KBUILD_EXTRA_SYMBOLS="$sensors/Module.symvers $relay/Module.symvers" CONFIG_DRM_PANEL_EVENT_NOTIFICATIONS=y CONFIG_BOARD_USES_DOUBLE_TAP_CTRL=y modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$goodix" KERNEL_SRC=/build/kernel KBUILD_EXTRA_SYMBOLS="$touchscreen/Module.symvers $info/Module.symvers" CONFIG_INPUT_TOUCHSCREEN_MMI=y CONFIG_DRM_PANEL_EVENT_NOTIFICATIONS=y CONFIG_BOARD_USES_DOUBLE_TAP_CTRL=y TARGET_PRODUCT=eqs modules
            fi
            if [[ "$EQS_FUNCTIONAL_MODULES" == 1 ]]; then
                git -C /build/sm8475-modules archive HEAD \
                    qcom/opensource/wlan/qcacld-3.0 \
                    qcom/opensource/wlan/qca-wifi-host-cmn \
                    qcom/opensource/wlan/fw-api \
                    motorola/drivers/power/bm_adsp_ulog \
                    motorola/drivers/power/mmi_charger \
                    motorola/drivers/power/qti_glink_charger \
                    motorola/drivers/power/qpnp_adaptive_charge \
                    motorola/drivers/misc/utag | tar -x -C "$module_root"
                wlan_root="$module_root/qcom/opensource/wlan"
                wlan="$wlan_root/qcacld-3.0"
                ulog="$module_root/motorola/drivers/power/bm_adsp_ulog"
                charger="$module_root/motorola/drivers/power/mmi_charger"
                glink_charger="$module_root/motorola/drivers/power/qti_glink_charger"
                adaptive_charge="$module_root/motorola/drivers/power/qpnp_adaptive_charge"
                utag="$module_root/motorola/drivers/misc/utag"
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$wlan" WLAN_ROOT="$wlan/.qca6490" WLAN_COMMON_ROOT=cmn WLAN_FW_API="$wlan_root/fw-api" WLAN_PROFILE=qca6490 DYNAMIC_SINGLE_CHIP=qca6490 MODNAME=qca_cld3_qca6490 DEVNAME=qca6490 WLAN_CTRL_NAME=wlan CONFIG_QCA_CLD_WLAN=m BOARD_PLATFORM=waipio modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$ulog" KERNEL_SRC=/build/kernel modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$charger" KERNEL_SRC=/build/kernel KBUILD_EXTRA_SYMBOLS="$info/Module.symvers" modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$glink_charger" KERNEL_SRC=/build/kernel KBUILD_EXTRA_SYMBOLS="$charger/Module.symvers $ulog/Module.symvers" CONFIG_WIRELESS_CPS4035B=m modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$adaptive_charge" KERNEL_SRC=/build/kernel KBUILD_EXTRA_SYMBOLS="$charger/Module.symvers" CONFIG_USE_MMI_CHARGER=y modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$utag" KERNEL_SRC=/build/kernel modules

                # Operational eqs audio/camera, not just the recovery module set.
                git -C /build/sm8475-modules archive HEAD \
                    qcom/opensource/audio-kernel qcom/opensource/camera-kernel qcom/opensource/eva-kernel \
                    motorola/drivers/regulator/wl2868c | tar -x -C "$module_root"
                audio="$module_root/qcom/opensource/audio-kernel"
                camera="$module_root/qcom/opensource/camera-kernel"
                camera_pmic="$module_root/motorola/drivers/regulator/wl2868c"
                eva="$module_root/qcom/opensource/eva-kernel"
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$audio" KERNEL_SRC=/build/kernel AUDIO_ROOT="$audio" MODNAME=audio_dlkm BOARD_PLATFORM=waipio CONFIG_SND_SOC_WAIPIO=m TARGET_PRODUCT=eqs TARGET_BUILD_VARIANT=userdebug modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$camera" KERNEL_SRC=/build/kernel KERNEL_ROOT=/build/kernel CAMERA_KERNEL_ROOT="$camera" MODNAME=camera TARGET_PRODUCT=eqs TARGET_BUILD_VARIANT=userdebug KBUILD_EXTRA_SYMBOLS="$mmrm/Module.symvers" modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$camera_pmic" KERNEL_SRC=/build/kernel modules
                make -j1 -C /build/kernel O=/build/out "${common[@]}" M="$eva" KERNEL_SRC=/build/kernel EVA_ROOT="$eva" KBUILD_EXTRA_SYMBOLS="$mmrm/Module.symvers" modules
            fi
        fi
    ' build-host-artifacts "${build_targets[@]}"

profile=full
(( ! dev_thinlto )) || profile=thinlto
bash "$script_dir/resolve-eqs-config.sh" --check "$worktree/out/.config" "$profile"

if (( display_modules )); then
    [[ -s "$worktree/out/Module.symvers" ]] || fail 'kernel Module.symvers is missing'
    in_tree_modules=$(find "$worktree/out" -type f -name '*.ko' | wc -l)
    (( in_tree_modules > 0 )) || fail 'no in-tree modules were built'
    module_root="$worktree/modules-dev-display/qcom/opensource"
    [[ -s "$module_root/mmrm-driver/Module.symvers" ]] || fail 'MMRM Module.symvers is missing'
    [[ -s "$module_root/display-drivers/Module.symvers" ]] || fail 'display Module.symvers is missing'
    [[ -s "$module_root/mmrm-driver/driver/msm-mmrm.ko" ]] || fail 'msm-mmrm.ko is missing'
    [[ -s "$module_root/display-drivers/msm/msm_drm.ko" ]] || fail 'msm_drm.ko is missing'
    printf 'in-tree modules built: %s\n' "$in_tree_modules"
    printf '%s\n' 'external modules built: msm-mmrm.ko msm_drm.ko'
fi

if (( touch_modules || functional_modules )); then
    [[ -s "$worktree/out/Module.symvers" ]] || fail 'kernel Module.symvers is missing'
    in_tree_modules=$(find "$worktree/out" -type f -name '*.ko' | wc -l)
    (( in_tree_modules > 0 )) || fail 'no in-tree modules were built'
    module_root="$worktree/modules-dev-touch"
    if (( functional_modules )); then
        module_root="$worktree/modules-dev-functional"
    fi
    for symvers in \
        "$module_root/qcom/opensource/mmrm-driver/Module.symvers" \
        "$module_root/qcom/opensource/display-drivers/Module.symvers" \
        "$module_root/motorola/drivers/mmi_annotate/Module.symvers" \
        "$module_root/motorola/drivers/mmi_info/Module.symvers" \
        "$module_root/motorola/drivers/mmi_relay/Module.symvers" \
        "$module_root/motorola/drivers/sensors/Module.symvers" \
        "$module_root/motorola/drivers/input/touchscreen/touchscreen_mmi/Module.symvers"; do
        [[ -s "$symvers" ]] || fail "external Module.symvers is missing: $symvers"
    done
    [[ -e "$module_root/motorola/drivers/input/touchscreen/goodix_berlin_mmi/Module.symvers" ]] || \
        fail 'Goodix Module.symvers is missing'
    for module in \
        "$module_root/qcom/opensource/mmrm-driver/driver/msm-mmrm.ko" \
        "$module_root/qcom/opensource/display-drivers/msm/msm_drm.ko" \
        "$module_root/motorola/drivers/mmi_annotate/mmi_annotate.ko" \
        "$module_root/motorola/drivers/mmi_info/mmi_info.ko" \
        "$module_root/motorola/drivers/mmi_relay/mmi_relay.ko" \
        "$module_root/motorola/drivers/sensors/sensors_class.ko" \
        "$module_root/motorola/drivers/input/touchscreen/touchscreen_mmi/touchscreen_mmi.ko" \
        "$module_root/motorola/drivers/input/touchscreen/goodix_berlin_mmi/goodix_brl_mmi.ko"; do
        [[ -s "$module" ]] || fail "external module is missing: $module"
    done
    printf 'in-tree modules built: %s\n' "$in_tree_modules"
    printf '%s\n' 'external modules built: msm-mmrm.ko msm_drm.ko mmi_annotate.ko mmi_info.ko mmi_relay.ko sensors_class.ko touchscreen_mmi.ko goodix_brl_mmi.ko'
fi

if (( functional_modules )); then
    python3 "$script_dir/check-module-inventory.py" "$worktree"
    for symvers in \
        "$module_root/motorola/drivers/power/bm_adsp_ulog/Module.symvers" \
        "$module_root/motorola/drivers/power/mmi_charger/Module.symvers"; do
        [[ -s "$symvers" ]] || fail "functional producer Module.symvers is missing: $symvers"
    done
    for module in \
        "$module_root/qcom/opensource/wlan/qcacld-3.0/qca_cld3_qca6490.ko" \
        "$module_root/motorola/drivers/power/bm_adsp_ulog/bm_adsp_ulog.ko" \
        "$module_root/motorola/drivers/power/mmi_charger/mmi_charger.ko" \
        "$module_root/motorola/drivers/power/qti_glink_charger/qti_glink_charger.ko" \
        "$module_root/motorola/drivers/power/qpnp_adaptive_charge/qpnp_adaptive_charge.ko" \
        "$module_root/motorola/drivers/misc/utag/utags.ko"; do
        [[ -s "$module" ]] || fail "functional external module is missing: $module"
    done
    for expected in CONFIG_QTI_BATTERY_CHARGER=m CONFIG_UCSI_QTI_GLINK=m CONFIG_CNSS2=m CONFIG_ICNSS2=m; do
        grep -Fxq "$expected" "$worktree/out/.config" || fail "missing functional configuration: $expected"
    done
    external_vermagic=
    while IFS= read -r module; do
        readelf -h "$module" | grep -Fq 'Class:                             ELF64' || fail "external module is not ELF64: $module"
        readelf -h "$module" | grep -Fq 'Type:                              REL (Relocatable file)' || fail "external module is not relocatable: $module"
        readelf -h "$module" | grep -Fq 'Machine:                           AArch64' || fail "external module is not AArch64: $module"
        vermagic=$(modinfo -F vermagic "$module")
        [[ -n "$vermagic" ]] || fail "external module has no vermagic: $module"
        if [[ -z "$external_vermagic" ]]; then
            external_vermagic=$vermagic
        elif [[ "$vermagic" != "$external_vermagic" ]]; then
            fail "external module vermagic differs: $module"
        fi
    done < <(find "$module_root" -type f -name '*.ko' | sort)
    [[ "$(modinfo -F name "$module_root/qcom/opensource/wlan/qcacld-3.0/qca_cld3_qca6490.ko")" == qca_cld3_qca6490 ]] || \
        fail 'qca_cld3_qca6490.ko has an unexpected module name'
    module_list="$common_device_reference/modules.load.vendor_boot"
    vendor_boot_modules=$(sort -u "$module_list")
    vendor_boot_count=$(printf '%s\n' "$vendor_boot_modules" | wc -l)
    while IFS= read -r module; do
        find "$worktree/out" -type f -name "$module" -print -quit | grep -q . || \
            fail "vendor_boot module is missing from in-tree output: $module"
    done <<< "$vendor_boot_modules"
    printf 'vendor_boot module names present in in-tree output: %s\n' "$vendor_boot_count"
    printf '%s\n' 'functional external modules built: qca_cld3_qca6490.ko bm_adsp_ulog.ko mmi_charger.ko qti_glink_charger.ko qpnp_adaptive_charge.ko utags.ko'
fi

if [[ " ${targets[*]} " == *' dtbs '* ]]; then
    artifacts=(
        cape-moto-eqs-base.dtb
        cape-v2-moto-eqs-base.dtb
        cape-eqs-evt1-overlay.dtbo
        cape-eqs-evt2-overlay.dtbo
        cape-eqs-dvt1a1-overlay.dtbo
        cape-eqs-dvt1b1-overlay.dtbo
        cape-eqs-dvt2a1-overlay.dtbo
        cape-eqs-dvt2b1-overlay.dtbo
        cape-eqs-dvt2b3-overlay.dtbo
        cape-eqs-pvt1a-overlay.dtbo
    )
    artifact_dir="$worktree/out/arch/arm64/boot/dts/vendor/qcom"
    for artifact in "${artifacts[@]}"; do
        [[ -f "$artifact_dir/$artifact" ]] || fail "missing eqs DT artifact: $artifact"
    done
    printf 'eqs DT artifacts built: %s\n' "${#artifacts[@]}"
fi

if [[ " ${build_targets[*]} " == *' Image '* ]]; then
    [[ -s "$worktree/out/arch/arm64/boot/Image" ]] || fail 'Image target completed without a non-empty arch/arm64/boot/Image'
fi

if find "$worktree/out" -type f \( -name boot.img -o -name dtbo.img -o -name vendor_boot.img -o -name '*.deb' \) -print -quit | grep -q .; then
    fail 'prohibited flashable or package artifact found in staged output'
fi
if (( dt_images )); then
    dt_image_root="$worktree/dt-images-dev"
    [[ -s "$dt_image_root/dtb.img" ]] || fail 'merged DTB blob is missing'
    [[ -s "$dt_image_root/dtbo.img" ]] || fail 'dtbo image is missing'
    (( $(stat -c %s "$dt_image_root/dtbo.img") < 25165824 )) || fail 'dtbo image exceeds the eqs partition size'
    [[ -s "$dt_image_root/dtbo.dump" ]] || fail 'mkdtboimg dump is missing'
    [[ -s "$dt_image_root/SHA256SUMS" ]] || fail 'DT image checksums are missing'
    grep -Fxq 'dtb.img' < <(awk '{print $2}' "$dt_image_root/SHA256SUMS") || fail 'DTB checksum manifest entry is missing or non-portable'
    grep -Fxq 'dtbo.img' < <(awk '{print $2}' "$dt_image_root/SHA256SUMS") || fail 'DTBO checksum manifest entry is missing or non-portable'
    if find "$dt_image_root" -type f \( -name boot.img -o -name vendor_boot.img -o -name vbmeta.img -o -name '*.deb' \) -print -quit | grep -q .; then
        fail 'prohibited flashable or package artifact found in DT image staging'
    fi
    merged_dtb_count=$(find "$dt_image_root/merged" -type f -name '*.dtb' | wc -l)
    merged_dtbo_count=$(find "$dt_image_root/merged" -type f -name '*.dtbo' | wc -l)
    [[ "$merged_dtb_count" == 2 ]] || fail "expected 2 merged eqs DTBs, found $merged_dtb_count"
    [[ "$merged_dtbo_count" == 8 ]] || fail "expected 8 merged eqs DTBOs, found $merged_dtbo_count"
    printf 'merged eqs DTBs: %s\n' "$merged_dtb_count"
    printf 'merged eqs DTBOs: %s\n' "$merged_dtbo_count"
    printf 'merged DTB blob bytes: %s\n' "$(stat -c %s "$dt_image_root/dtb.img")"
    printf 'DTBO image bytes: %s\n' "$(stat -c %s "$dt_image_root/dtbo.img")"
    cat "$dt_image_root/SHA256SUMS"
fi

printf 'Host-only kernel artifacts completed for: %s\n' "${targets[*]}"
printf 'Staging directory: %s\n' "$worktree"
if (( dt_images )); then
    printf '%s\n' 'No boot image, vendor_boot image, Debian package, flash, or hardware action was produced.'
else
    printf '%s\n' 'No boot image, dtbo image, vendor_boot image, Debian package, flash, or hardware action was produced.'
fi
