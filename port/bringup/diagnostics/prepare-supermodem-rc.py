#!/usr/bin/env python3
"""Prepare a readonly LXC overlay, never edit the stock vendor partition."""
import hashlib
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: prepare-supermodem-rc.py STOCK_INIT_MMI_RC NEW_OUTPUT')
source = Path(sys.argv[1]).read_bytes()
if hashlib.sha256(source).hexdigest() != '43ec08f49707ea166fefcb9a2be541715c3e9f100b986149a4d042d4fd635b26':
    raise SystemExit('Requires exact eqs RETAR U1SQS34.52-21-1-16 init.mmi.rc')
context = b' context=u:object_r:firmware_file:s0'
for mount in (
    b'    mount ext4 /dev/block/bootdevice/by-name/modem${ro.boot.slot_suffix} /vendor/super_modem ro nosuid nodev',
    b'    mount ext4 loop@/vendor/super_modem/${ro.vendor.hw.modem_mount_file} /vendor/firmware_mnt ro nosuid nodev',
):
    old = mount + context + b'\n'
    if source.count(old) != 1:
        raise SystemExit('Expected unique readonly super-modem mount directive')
    # No SELinux policy is loaded by Halium; this context token causes EINVAL.
    source = source.replace(old, mount + b'\n')
with Path(sys.argv[2]).open('xb') as output:
    output.write(source)
