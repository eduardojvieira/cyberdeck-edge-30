#!/usr/bin/env python3
"""Patch the pinned, extracted Halium initramfs for eqs LVM-only bring-up."""
import hashlib
import shutil
from pathlib import Path
import sys

HASHES = {
    'scripts/halium': 'e8e44b9293d7bcf182d967c6089c350e1efa0adae74afaec88c04b08b8bca166',
    'init': 'cda3570b6edc38c6aebf8a058bf75f5ada94e63a32b27da4d2f1eabf2200d0dc',
}


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f'upstream anchor changed: {before[:70]}')
    return text.replace(before, after, 1)


def prepare(root, candidate):
    if not candidate or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-.' for c in candidate):
        raise ValueError('invalid candidate identifier')
    texts = {}
    for name, digest in HASHES.items():
        data = (root / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f'unexpected upstream input: {name}')
        texts[name] = data.decode()
    halium = texts['scripts/halium']
    helpers = '''# eqs diagnostic policy: never repair userdata or resize an existing LVM.
eqs_mark() {
    printf '<3>%s\\n' "EQS CANDIDATE=$EQS_CANDIDATE $*" >/dev/kmsg || true
    printf '%s\\n' "EQS CANDIDATE=$EQS_CANDIDATE $*" >>/run/initramfs/eqs.log || true
}
eqs_stop() {
    eqs_mark "FAIL $*"
    # panic may return after the debugging shell exits; never fall through.
    while :; do halium_panic "$*"; sleep 5; done
}
eqs_require_lvm() {
    [ "$use_lvm" = yes ] && [ -n "$_syspart" ] || eqs_stop "LVM root missing; no userdata repair"
}
eqs_mounts() {
    while read -r eqs_dev eqs_target eqs_type eqs_options eqs_rest; do
        case "$eqs_target" in
            /halium-system|/root|/android-rootfs|/android-system|/root/android|/root/var/lib/lxc/android/rootfs)
                eqs_mark "MOUNT $1 $eqs_dev $eqs_target $eqs_type $eqs_options" ;;
        esac
    done </proc/mounts
}

'''
    halium = replace_once(halium, '\nmountroot() {', '\n' + helpers + 'mountroot() {\n\teqs_mark "MOUNTROOT BEGIN"')
    halium = replace_once(halium, '\tload_kernel_modules\n', '\teqs_mark "MODULES BEGIN"\n\tload_kernel_modules\n\teqs_mark "MODULES END (inspect per-module results)"\n')
    halium = replace_once(halium, '\t\t\tmodprobe -a "$1"', '\t\t\tif modprobe -a "$1"; then eqs_mark "MODULE OK $1"; else eqs_mark "MODULE FAIL $1 rc=$?"; fi')
    halium = replace_once(halium, '\tudevadm settle\n', '\teqs_mark "UDEV BEGIN"\n\tudevadm settle --timeout=30 || eqs_stop "udev settle timeout"\n\teqs_mark "UDEV END"\n')
    halium = replace_once(halium, '\t\thalium_panic "Couldn\'t find data partition."', '\t\teqs_stop "Could not find data partition"')
    halium = replace_once(halium, '\tmount_vendor_partitions "$ab_slot_suffix"', '\teqs_mark "UFS FOUND $path slot=$ab_slot_suffix"\n\teqs_mark "VENDOR BEGIN"\n\tmount_vendor_partitions "$ab_slot_suffix"\n\teqs_mark "VENDOR END"')
    halium = replace_once(halium, '\tuse_lvm="yes"', '\teqs_mark "LVM BEGIN"\n\tuse_lvm="yes"')
    start = halium.index('\tif [ "${use_lvm}" != "yes" ]; then\n\t\ttell_kmsg "checking filesystem integrity')
    end = halium.index('\n\t# If both $imagefile', start)
    halium = halium[:start] + '\teqs_require_lvm\n\teqs_mark "LVM END $_syspart"\n' + halium[end:]
    halium = replace_once(halium, '\t\tmount -o rw $_syspart /halium-system', '\t\teqs_mark "ROOT BEGIN $_syspart"\n\t\tmount -o rw $_syspart /halium-system || eqs_stop "root mount failed"\n\t\teqs_mark "ROOT END"')
    halium = replace_once(halium, '\t\t[ "${use_lvm}" == "yes" ] && resize_lvm_if_needed "${path}" "${vg}" "${root_lv}"', '\t\teqs_mark "RESIZE DISABLED"')
    halium = replace_once(halium, '\tidentify_boot_mode\n', '\tidentify_boot_mode\n\teqs_mark "BOOTMODE $BOOT_MODE"\n\t[ "$BOOT_MODE" = halium ] || eqs_stop "unexpected boot mode $BOOT_MODE"')
    # Keep exactly this kernel's modules available to native userspace, not stock ones.
    halium = replace_once(halium, '\t[ -e ${rootmnt}/android/system/lib/modules ] && mount --bind ${rootmnt}/android/system/lib/modules ${rootmnt}/lib/modules', '\tmkdir -p /run/eqs-modules "${rootmnt}/lib/modules"\n\tcp -a /lib/modules/. /run/eqs-modules/ || eqs_stop "native module copy failed"\n\tmount --bind /run/eqs-modules "${rootmnt}/lib/modules" || eqs_stop "native module bind failed"')
    # Locate the observed RW-to-RO transition; do not blindly remount or repair.
    for anchor, stage in (
        ('\t\teqs_mark "ROOT END"', 'ROOT_MOUNT'),
        ('\tidentify_boot_mode', 'ANDROID_MOUNT'),
        ('\t\tmount --move /halium-system ${rootmnt}', 'ROOT_MOVE'),
        ('\t\tmount --move /android-rootfs ${rootmnt}/var/lib/lxc/android/rootfs', 'ANDROID_MOVE'),
        ('\t\t[ $ANDROID_IMAGE_MODE = "rootfs" ] && mount -o bind ${rootmnt}/var/lib/lxc/android/rootfs ${rootmnt}/android', 'ANDROID_BIND'),
    ):
        halium = replace_once(halium, anchor + '\n', anchor + '\n\t\teqs_mounts ' + stage + '\n')
    init = texts['init']
    init = replace_once(init, 'mkdir -m 0755 /run/initramfs', 'mkdir -m 0755 /run/initramfs\nexport EQS_CANDIDATE=' + candidate + '\nprintf "%s\\n" "EQS CANDIDATE=$EQS_CANDIDATE INIT EARLY_FS END" >/dev/kmsg\nprintf "%s\\n" "EQS CANDIDATE=$EQS_CANDIDATE INIT EARLY_FS END" >/run/initramfs/eqs.log')
    # Bootloader appends quiet on this device; unprefixed kmsg messages are
    # priority 4 and disappear from the console-backed pstore at quiet level 4.
    init = init.replace('printf "%s\\n" "EQS CANDIDATE=', 'printf "<3>%s\\n" "EQS CANDIDATE=')
    for command, stage in (
        ('run_scripts /scripts/init-top', 'INIT_TOP'),
        ('load_modules', 'GENERIC_MODULES'),
        ('run_scripts /scripts/init-premount', 'INIT_PREMOUNT'),
        ('. /scripts/${BOOT}', 'SOURCE_BOOT'),
        ('mount_top', 'MOUNT_TOP'),
        ('mount_premount', 'MOUNT_PREMOUNT'),
        ('mountroot', 'MOUNTROOT_CALL'),
        ('mount_bottom', 'MOUNT_BOTTOM'),
        ('nfs_bottom', 'NFS_BOTTOM'),
        ('local_bottom', 'LOCAL_BOTTOM'),
        ('run_scripts /scripts/init-bottom', 'INIT_BOTTOM'),
        ('mount -n -o move /run ${rootmnt}/run', 'MOVE_RUN'),
    ):
        marker = 'printf "<3>EQS CANDIDATE=$EQS_CANDIDATE ' + stage
        before = marker + ' BEGIN\\n" >/dev/kmsg'
        after = marker + ' END rc=$?\\n" >/dev/kmsg'
        init = replace_once(init, '\n' + command + '\n', '\n' + before + '\n' + command + '\n' + after + '\n')
    init = replace_once(init, '# Move virtual filesystems over to the real filesystem', 'printf "%s\\n" "EQS CANDIDATE=$EQS_CANDIDATE HANDOFF init=$init root=$rootmnt" >/dev/kmsg\nprintf "%s\\n" "EQS CANDIDATE=$EQS_CANDIDATE HANDOFF init=$init root=$rootmnt" >>${rootmnt}/run/initramfs/eqs.log\n\n# Move virtual filesystems over to the real filesystem')
    init = init.replace('printf "%s\\n" "EQS CANDIDATE=', 'printf "<3>%s\\n" "EQS CANDIDATE=')
    init = replace_once(init, '\trun-init -n "${rootmnt}" "${1}"', '\trun-init -n "${rootmnt}" "${1}"\n\tstatus=$?\n\tprintf "<3>EQS VALIDATE_INIT path=%s rc=%s\\n" "$1" "$status" >/dev/kmsg\n\treturn "$status"')
    init = replace_once(init, 'export EQS_CANDIDATE=', 'echo 8 >/proc/sys/kernel/printk\nexport EQS_CANDIDATE=')
    # HWC-only eqs currently has no usable /dev/console. Do not mistake that
    # for a missing init executable; systemd logging is explicitly sent to kmsg.
    init = replace_once(init, '\trun-init -n "${rootmnt}" "${1}"', '\trun-init -n -c /dev/null "${rootmnt}" "${1}"')
    init = replace_once(init, 'exec run-init ${drop_caps} ${rootmnt} ${init} "$@" <${rootmnt}/dev/console >${rootmnt}/dev/console 2>&1', 'exec run-init -c /dev/null ${drop_caps} ${rootmnt} ${init} "$@"')
    (root / 'scripts/halium').write_text(halium)
    (root / 'init').write_text(init)
    # The generic image ships pre-generated Dropbear identity material. This
    # candidate uses only its explicit USB panic channel, never those identities.
    (root / 'scripts/init-premount/dropbear').unlink(missing_ok=True)
    if (root / 'etc/dropbear').exists():
        shutil.rmtree(root / 'etc/dropbear')
    for directory in root.glob('root*/.ssh'):
        shutil.rmtree(directory)



if __name__ == '__main__':
    try:
        if len(sys.argv) != 3:
            raise ValueError('usage: prepare-bringup-initramfs.py EXTRACTED_ROOT CANDIDATE')
        prepare(Path(sys.argv[1]), sys.argv[2])
    except (ValueError, OSError) as error:
        sys.exit(str(error))
