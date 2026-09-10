#!/usr/bin/env bash
# Build reproducible, host-only eqs-dev binary packages and boot artifacts.
set -euo pipefail

readonly IMAGE=cyberdeck-edge30/kernel-build:local
readonly VERSION=5.10.209+git20240821.bd42a1bb-1~eqsdev3
readonly RELEASE=5.10.209-android13-0-gbd42a1bb7281
readonly EPOCH=1724258646
readonly INITRAMFS_VERSION=2025.04.11.0+git20250411210410.e515727.next.production
readonly INITRAMFS_SHA256=bcabeda8d27c28c8694e3e174533af46205e9f68dda4b5ae3bba8fb78b7a8594
fail() { printf 'build-dev-packages: %s\n' "$*" >&2; exit 1; }

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel) || fail 'must run from the worktree'
worktree=$(readlink -m -- "${EQS_KERNEL_WORKDIR:-$repo_root/.work/eqs-kernel}")
artifacts="$worktree/eqs-dev-packages"
for tool in python3 docker git sha256sum cmp find grep stat; do command -v "$tool" >/dev/null || fail "missing host tool: $tool"; done

# dt-images must run first: the functional ThinLTO gate owns the final ABI config.
case "${1:-}" in
  '') "$script_dir/build-host-artifacts.sh" dt-images-dev; "$script_dir/build-host-artifacts.sh" modules-dev-functional ;;
  --reuse-gates) [[ -s "$worktree/dt-images-dev/dtb.img" && -s "$worktree/dt-images-dev/dtbo.img" && -s "$worktree/out/arch/arm64/boot/Image" ]] || fail 'missing prior host gates' ;;
  *) fail 'usage: build-dev-packages.sh [--reuse-gates]' ;;
esac
bash "$script_dir/resolve-eqs-config.sh" --check "$worktree/out/.config" thinlto
python3 "$script_dir/check-module-inventory.py" "$worktree"
docker image inspect "$IMAGE" >/dev/null || fail "local build image unavailable; build port/kernel/Dockerfile explicitly before retrying"
rm -rf "$artifacts"; mkdir -p "$artifacts/runs"

for run in one two; do
  stage="$artifacts/runs/$run"
  mkdir -p "$stage"
  docker run --rm --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$worktree,dst=/build" \
    --mount "type=bind,src=$script_dir,dst=/scripts,readonly" \
    --mount "type=bind,src=$repo_root/reference/repos/eqs-development/android_device_motorola_sm8475-common,dst=/common,readonly" \
    --mount "type=bind,src=$stage,dst=/package" \
    --env SOURCE_DATE_EPOCH="$EPOCH" --env TZ=UTC --env LC_ALL=C \
    --workdir /build "$IMAGE" /bin/bash -euo pipefail -c '
      version=$1 release=$2 initramfs_version=$3 initramfs_sha=$4
      out=/build/out modules=/build/modules-dev-functional dt=/build/dt-images-dev
      root=/package/root image_root=$root/image boot_root=$root/bootimage boot_dir=/package/images
      rm -rf "$root" /package/vendor /package/vendor-meta "$boot_dir"; mkdir -p "$image_root" "$boot_root/boot" "$boot_dir" /package/vendor/lib/modules /package/vendor-meta/lib/modules/"$release"
      image=$out/arch/arm64/boot/Image
      [[ -s "$image" && -s "$dt/dtb.img" && -s "$dt/dtbo.img" ]] || { echo missing-kernel-or-dt >&2; exit 1; }
      grep -Fx CONFIG_LTO_CLANG_THIN=y "$out/.config"; grep -Fx CONFIG_CFI_CLANG=y "$out/.config"
      python3 /scripts/check-module-inventory.py /build
      bash /build/kernel/scripts/extract-ikconfig "$image" > /package/embedded.config
      cmp "$out/.config" /package/embedded.config
      module_count=$(( $(wc -l < "$out/modules.order") + $(find "$modules" -type f -name "*.ko" | wc -l) ))
      make -j1 -C /build/kernel O="$out" ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu- STRIP=aarch64-linux-gnu-strip INSTALL_MOD_PATH="$image_root" modules_install
      module_dir=$image_root/lib/modules/$release; [[ -d "$module_dir" ]] || exit 1
      find "$modules" -type f -name "*.ko" -print0 | while IFS= read -r -d "" module; do install -D -m 0644 "$module" "$module_dir/extra/$(basename "$module")"; done
      find "$module_dir" -type f -name "*.ko" -exec aarch64-linux-gnu-strip --strip-debug {} +
      cat "$out/Module.symvers" > /package/all.symvers
      find "$modules" -type f -name Module.symvers -exec cat {} + >> /package/all.symvers
      depmod -n -e -E /package/all.symvers -b "$image_root" "$release" >/dev/null 2>/package/module-abi.log
      [[ ! -s /package/module-abi.log ]] || { cat /package/module-abi.log >&2; exit 1; }
      depmod -b "$image_root" "$release"
      [[ $(find "$module_dir" -type f -name "*.ko" | wc -l) == "$module_count" ]] || { echo wrong-module-count >&2; exit 1; }
      find "$module_dir" -type f -name "*.ko" -print0 | while IFS= read -r -d "" module; do [[ "$(modinfo -F vermagic "$module")" == "5.10.209-android13-0-gbd42a1bb7281 SMP preempt mod_unload modversions aarch64" ]] || exit 1; done
      mkdir -p "$image_root/usr/lib/modules-load.d" "$image_root/boot"
      printf "%s\\n" msm-mmrm msm_drm mmi_annotate mmi_info mmi_relay sensors_class touchscreen_mmi goodix_brl_mmi qca_cld3_qca6490 bm_adsp_ulog mmi_charger qti_glink_charger qpnp_adaptive_charge utags > "$image_root/usr/lib/modules-load.d/motorola-eqs-dev.conf"
      # Load media after mounting the native root, not in the early initramfs.
      find "$modules/qcom/opensource/audio-kernel" "$modules/qcom/opensource/camera-kernel" "$modules/qcom/opensource/eva-kernel" "$modules/motorola/drivers/regulator/wl2868c" -type f -name "*.ko" -printf "%f\\n" | sed "s/\\.ko$//" | sort > "$image_root/usr/lib/modules-load.d/motorola-eqs-media.conf"
      cp "$image" "$image_root/boot/Image-$release"; cp "$out/.config" "$image_root/boot/config-$release"; cp "$out/System.map" "$image_root/boot/System.map-$release"
      cp "$dt/dtbo.img" "$boot_dir/dtbo.img"; cp "$dt/dtb.img" /package/dtb.img
      [[ $(wc -l < /common/modules.load.recovery) == 333 ]]
      [[ $(sort -u /common/modules.load.recovery | wc -l) == 331 ]]
      [[ $(find "$module_dir" -type f -name "*.ko" | wc -l) == "$module_count" ]]
      find "$module_dir" -type f -name "*.ko" -printf "%f\\n" | sort -u > /package/built-modules.list
      [[ $(wc -l < /package/built-modules.list) == "$module_count" ]]
      comm -23 <(sort -u /common/modules.load.recovery) /package/built-modules.list > /package/recovery-modules-missing.list
      [[ ! -s /package/recovery-modules-missing.list ]] || { cat /package/recovery-modules-missing.list >&2; exit 1; }
      # Preserve the working 325-entry early boot list; media loads in systemd.
      awk "NR==FNR { built[\$1]=1; next } built[\$0] && !seen[\$0]++" /package/built-modules.list /common/modules.load.recovery | grep -Ev "^(adsp_loader_dlkm|gpr_dlkm|q6_notifier_dlkm|q6_pdr_dlkm|snd_event_dlkm|spf_core_dlkm)\\.ko$" > /package/vendor/lib/modules/modules.load
      [[ $(wc -l < /package/vendor/lib/modules/modules.load) == 325 ]]
      [[ $(sort -u /package/vendor/lib/modules/modules.load | wc -l) == 325 ]]
      for name in dwc3-msm.ko phy-msm-ssusb-qmp.ko phy-msm-snps-hs.ko phy-msm-snps-eusb2.ko ssusb-redriver-ps5169.ko usb_f_gsi.ko ucsi_glink.ko; do grep -Fx "$name" /package/vendor/lib/modules/modules.load || { echo "vendor-usb-module-missing:$name" >&2; exit 1; }; done
      find "$module_dir" -type f -name "*.ko" -print0 | while IFS= read -r -d "" module; do name=${module##*/}; install -m 0644 "$module" "/package/vendor/lib/modules/$name"; install -m 0644 "$module" "/package/vendor-meta/lib/modules/$release/$name"; done
      cp "$module_dir"/modules.{order,builtin,builtin.modinfo} /package/vendor-meta/lib/modules/"$release"/
      depmod -b /package/vendor-meta "$release"
      cp /package/vendor-meta/lib/modules/"$release"/modules.{dep,alias,softdep,symbols,builtin,builtin.modinfo,order,alias.bin,builtin.alias.bin,builtin.bin,dep.bin,symbols.bin} /package/vendor/lib/modules/
      [[ $(find /package/vendor/lib/modules -maxdepth 1 -name "*.ko" | wc -l) == "$module_count" ]]
      find /package/vendor/lib/modules -maxdepth 1 -name "*.ko" -print0 | while IFS= read -r -d "" module; do [[ "$(modinfo -F vermagic "$module")" == "5.10.209-android13-0-gbd42a1bb7281 SMP preempt mod_unload modversions aarch64" ]] || exit 1; done
      ! find /package/vendor/lib/modules -mindepth 1 -type d -print -quit | grep .
      find /package/vendor -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
      (cd /package/vendor && find . -print0 | sort -z | cpio --null -o -H newc --reproducible --owner=0:0) | lz4 -l -q > /package/vendor-ramdisk.lz4
      initramfs=$(dpkg -L linux-initramfs-halium-generic | grep "/initrd.img-halium-generic.lz4$"); [[ -s "$initramfs" ]]
      initramfs_deb=/var/cache/apt/archives/linux-initramfs-halium-generic_${initramfs_version}_arm64.deb
      [[ $(sha256sum "$initramfs_deb" | cut -d" " -f1) == "$initramfs_sha" ]]; [[ $(dpkg-query -W -f="\${Version}" linux-initramfs-halium-generic) == "$initramfs_version" ]]
      mkdir -p /package/initramfs
      lz4 -d -q -c "$initramfs" | cpio -idmu --quiet -D /package/initramfs
      candidate=eqs-halium2-$(sha256sum "$out/.config" | cut -c1-12)
      python3 /scripts/test-bringup-initramfs.py /package/initramfs
      python3 /scripts/prepare-bringup-initramfs.py /package/initramfs "$candidate"
      find /package/initramfs -exec touch -h -d "@$SOURCE_DATE_EPOCH" {} +
      (cd /package/initramfs && find . -print0 | sort -z | cpio --null -o -H newc --reproducible --owner=0:0) | lz4 -l -q > /package/initramfs-eqs.lz4
      initramfs=/package/initramfs-eqs.lz4
      mkbootimg --header_version 4 --pagesize 4096 --kernel "$image" --ramdisk "$initramfs" --cmdline "console=tty0 loglevel=7 printk.devkmsg=on firmware_class.path=/data/vendor/param/firmware systemd.log_target=kmsg" --output "$boot_dir/boot.img"
      avbtool add_hash_footer --image "$boot_dir/boot.img" --partition_name boot --partition_size 100663296 --salt 0000000000000000000000000000000000000000000000000000000000000000
      printf "%s\\n" androidboot.hardware=qcom androidboot.memcg=1 androidboot.usbcontroller=a600000.dwc3 > /package/vendor_bootconfig
      mkbootimg --header_version 4 --pagesize 4096 --base 0x00000000 --kernel_offset 0x00008000 --ramdisk_offset 0x01000000 --tags_offset 0x00000100 --dtb_offset 0x0000000001f00000 --dtb /package/dtb.img --vendor_cmdline "video=vfb:640x400,bpp=32,memsize=3072000 printk.devkmsg=on firmware_class.path=/data/vendor/param/firmware bootconfig" --vendor_bootconfig /package/vendor_bootconfig --ramdisk_type platform --ramdisk_name "" --vendor_ramdisk_fragment /package/vendor-ramdisk.lz4 --vendor_boot "$boot_dir/vendor_boot.img"
      avbtool make_vbmeta_image --output "$boot_dir/vbmeta.img" --flags 3 --padding_size 4096
      cp "$boot_dir"/{boot.img,vendor_boot.img,dtbo.img,vbmeta.img} "$boot_root/boot/"
      for image in "$boot_dir"/*.img; do (( $(stat -c %s "$image") <= 100663296 )) || exit 1; done; (( $(stat -c %s "$boot_dir/dtbo.img") < 25165824 ))
      mkdir -p "$image_root/DEBIAN" "$boot_root/DEBIAN" "$boot_root/usr/lib/flash-bootimage"
      printf "Package: linux-image-motorola-eqs\\nVersion: %s\\nArchitecture: arm64\\nMaintainer: cyberdeck-edge-30\\nDescription: Droidian eqs development kernel modules\\n" "$version" > "$image_root/DEBIAN/control"
      printf "Package: linux-bootimage-motorola-eqs\\nVersion: %s\\nArchitecture: arm64\\nDepends: linux-image-motorola-eqs (= %s), flash-bootimage\\nMaintainer: cyberdeck-edge-30\\nDescription: Droidian eqs development boot artifacts\\n" "$version" "$version" > "$boot_root/DEBIAN/control"
      cat > "$boot_root/usr/lib/flash-bootimage/boot.img.conf" <<"CONFIG"
FLASH_ENABLED=no
DEVICE_HAS_VENDORBOOT_PARTITION=yes
USERDATA_FLASHING_METHOD=telnet
EXTRA_INFO_DEVICE_IDS="eqs"
CONFIG
      dpkg-deb --root-owner-group -Zxz --uniform-compression --build "$image_root" "/package/linux-image-motorola-eqs_${version}_arm64.deb"
      dpkg-deb --root-owner-group -Zxz --uniform-compression --build "$boot_root" "/package/linux-bootimage-motorola-eqs_${version}_arm64.deb"
      cp "$boot_dir"/{boot.img,vendor_boot.img,dtbo.img,vbmeta.img} /package/
      [[ $(find "$module_dir" -type f -name "*.ko" -printf "%f\\n" | sort -u | wc -l) == "$module_count" ]]
      rm -rf /package/unpack-boot /package/unpack-vendor /package/extracted-vendor
      unpack_bootimg --out /package/unpack-boot --boot_img "$boot_dir/boot.img" | grep -Fx "boot image header version: 4"
      unpack_bootimg --out /package/unpack-boot --boot_img "$boot_dir/boot.img" | grep -Fx "command line args: console=tty0 loglevel=7 printk.devkmsg=on firmware_class.path=/data/vendor/param/firmware systemd.log_target=kmsg"
      cmp "$out/arch/arm64/boot/Image" /package/unpack-boot/kernel
      cmp "$initramfs" /package/unpack-boot/ramdisk
      head -c 8 "$boot_dir/vendor_boot.img" | grep -Fx VNDRBOOT
      unpack_bootimg --out /package/unpack-vendor --boot_img "$boot_dir/vendor_boot.img" > /package/vendor-unpack.txt
      grep -Fx "vendor boot image header version: 4" /package/vendor-unpack.txt
      grep -Fx "page size: 0x00001000" /package/vendor-unpack.txt
      grep -Fx "kernel load address: 0x00008000" /package/vendor-unpack.txt
      grep -Fx "ramdisk load address: 0x01000000" /package/vendor-unpack.txt
      grep -Fx "kernel tags load address: 0x00000100" /package/vendor-unpack.txt
      grep -Fx "dtb address: 0x0000000001f00000" /package/vendor-unpack.txt
      grep -Fx "vendor command line args: video=vfb:640x400,bpp=32,memsize=3072000 printk.devkmsg=on firmware_class.path=/data/vendor/param/firmware bootconfig" /package/vendor-unpack.txt
      cmp /package/dtb.img /package/unpack-vendor/dtb
      cmp /package/vendor_bootconfig /package/unpack-vendor/bootconfig
      cmp /package/vendor-ramdisk.lz4 /package/unpack-vendor/vendor_ramdisk00
      mkdir -p /package/extracted-vendor
      lz4 -d -q -c /package/unpack-vendor/vendor_ramdisk00 | cpio -idmu --quiet -D /package/extracted-vendor
      ln -s . /package/extracted-vendor/lib/modules/"$release"
      while IFS= read -r name; do modprobe -d /package/extracted-vendor -S "$release" --show-depends "${name%.ko}" >/dev/null; done < <(sort -u /package/extracted-vendor/lib/modules/modules.load)
      grep -Fx androidboot.hardware=qcom /package/vendor_bootconfig
      grep -Fx androidboot.memcg=1 /package/vendor_bootconfig
      grep -Fx androidboot.usbcontroller=a600000.dwc3 /package/vendor_bootconfig
      lz4 -d -q -c /package/vendor-ramdisk.lz4 | cpio -it | sed "s#^\\./##" | grep -Fx lib/modules/modules.load
      for name in dwc3-msm.ko phy-msm-ssusb-qmp.ko phy-msm-snps-hs.ko phy-msm-snps-eusb2.ko ssusb-redriver-ps5169.ko usb_f_gsi.ko ucsi_glink.ko; do lz4 -d -q -c /package/vendor-ramdisk.lz4 | cpio -it | sed "s#^\\./##" | grep -Fx "lib/modules/$name"; done
      avbtool info_image --image "$boot_dir/boot.img" | grep -E "Partition Name:.*boot$"
      avbtool info_image --image "$boot_dir/vbmeta.img" | grep -E "Flags:.*3$"
      [[ $(stat -c %s "$boot_dir/vbmeta.img") == 4096 ]]
      [[ $(python3 /usr/lib/mkdtboimg/mkdtboimg.py dump "$boot_dir/dtbo.img" | grep -c "dt_table_entry\[") == 8 ]]
      dpkg-deb -c /package/linux-image-motorola-eqs_*.deb > /package/image.list
      dpkg-deb -c /package/linux-bootimage-motorola-eqs_*.deb > /package/bootimage.list
      grep -F ./boot/Image- /package/image.list
      ! grep -E "boot/(boot|vendor_boot|dtbo|vbmeta)\\.img" /package/image.list
      grep -F ./boot/boot.img /package/bootimage.list
      dpkg-deb -f /package/linux-bootimage-motorola-eqs_*.deb Depends | grep -F "linux-image-motorola-eqs (= $version), flash-bootimage"
      dpkg-deb -e /package/linux-bootimage-motorola-eqs_*.deb /package/control
      [[ $(find /package/control -type f | wc -l) == 1 && -f /package/control/control ]]
      boot_image=$(find "$boot_root/boot" -maxdepth 1 -type f -name boot.img)
      config="$boot_root/usr/lib/flash-bootimage/$(basename "$boot_image").conf"
      [[ -f "$config" ]]
      grep -Fx FLASH_ENABLED=no "$config"
      grep -Fx DEVICE_HAS_VENDORBOOT_PARTITION=yes "$config"
      grep -Fx USERDATA_FLASHING_METHOD=telnet "$config"
      grep -Fx "EXTRA_INFO_DEVICE_IDS=\"eqs\"" "$config"
    ' bash "$VERSION" "$RELEASE" "$INITRAMFS_VERSION" "$INITRAMFS_SHA256"
done
for name in boot.img vendor_boot.img dtbo.img vbmeta.img linux-image-motorola-eqs_${VERSION}_arm64.deb linux-bootimage-motorola-eqs_${VERSION}_arm64.deb; do
  cmp "$artifacts/runs/one/$name" "$artifacts/runs/two/$name" || fail "non-reproducible artifact: $name"
  cp "$artifacts/runs/one/$name" "$artifacts/$name"
done
(cd "$artifacts" && sha256sum boot.img vendor_boot.img dtbo.img vbmeta.img *.deb > SHA256SUMS)
{
  printf 'HOST-ONLY / NOT HIL: these artifacts were not flashed or booted on eqs.\n'
  printf 'version=%s\nrelease=%s\nsource_date_epoch=%s\n' "$VERSION" "$RELEASE" "$EPOCH"
  printf 'kernel_commit=%s\n' "$(git -C "$worktree/kernel" rev-parse HEAD)"
  printf 'devicetrees_commit=%s\n' "$(git -C "$worktree/sm8475-devicetrees" rev-parse HEAD)"
  printf 'modules_commit=%s\n' "$(git -C "$worktree/sm8475-modules" rev-parse HEAD)"
  printf 'initramfs_version=%s\ninitramfs_deb_sha256=%s\n' "$INITRAMFS_VERSION" "$INITRAMFS_SHA256"
  printf 'config=ThinLTO+CFI\n'
  python3 "$script_dir/check-module-inventory.py" "$worktree"
  sha256sum "$worktree/out/.config" "$worktree/out/modules.order" "$worktree/out/Module.symvers"
  printf 'vendor_modules.load=working-early-set:325; media modules present and deferred to native systemd modules-load\n'
  printf 'vendor_boot_addresses=base:0x00000000,kernel:0x00008000,ramdisk:0x01000000,tags:0x00000100,dtb:0x0000000001f00000\n'
  printf 'cmdline=console=tty0 loglevel=7 printk.devkmsg=on firmware_class.path=/data/vendor/param/firmware systemd.log_target=kmsg\n'
  printf 'initramfs_policy=eqs-halium2 LVM-only no-auto-repair no-resize stage-markers native-module-bind\n'
  sha256sum "$script_dir/prepare-bringup-initramfs.py"
  printf 'bootconfig=androidboot.hardware=qcom androidboot.memcg=1 androidboot.usbcontroller=a600000.dwc3\n'
  cat "$artifacts/SHA256SUMS"
} > "$artifacts/MANIFEST.txt"
printf 'Host-only eqs-dev artifacts: %s\nNo flash or hardware action was performed.\n' "$artifacts"
