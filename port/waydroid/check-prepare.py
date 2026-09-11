#!/usr/bin/python3
"""PHONE/ROOT ONLY: prepare Waydroid and verify native Binder/KGSL are untouched."""
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import sys

if os.geteuid() != 0 or not Path("/dev/binderfs/binder-control").is_char_device():
    raise SystemExit("Run only on the authorized eqs phone as root, after installing the helper")

sys.path.insert(0, "/usr/lib/waydroid")
from tools.helpers.drivers import setupBinderNodes

def identity(name):
    path = Path("/dev") / name
    st = path.stat()
    return path.resolve(), st.st_dev, st.st_ino, st.st_rdev, st.st_mode, st.st_uid, st.st_gid

native = ("binder", "hwbinder", "vndbinder", "binderfs/binder-control")
before = [identity(name) for name in native]
dedicated = ("anbox-binder", "anbox-hwbinder", "anbox-vndbinder")
subprocess.run(["/usr/local/sbin/eqs-waydroid-binder"], check=True)
first = [identity(name) for name in dedicated]
subprocess.run(["/usr/local/sbin/eqs-waydroid-binder"], check=True)
assert first == [identity(name) for name in dedicated], "Not idempotent"
assert before == [identity(name) for name in native], "Native binder changed"
assert len({item[3] for item in first + before}) == 7, "Binder device IDs overlap"
args = SimpleNamespace(vendor_type="HALIUM_12")
setupBinderNodes(args)
assert (args.BINDER_DRIVER, args.HWBINDER_DRIVER, args.VNDBINDER_DRIVER) == dedicated
print("PASS: separate binder devices, idempotent setup, native Halium binder unchanged")

gpu_before = identity("kgsl-3d0")
config = Path("/var/lib/waydroid/lxc/waydroid/config")
for _ in range(2):
    subprocess.run(["/usr/local/sbin/eqs-waydroid-gpu"], check=True)
assert identity("kgsl-3d0") == gpu_before, "Native KGSL changed"
private = identity("eqs-waydroid/kgsl-3d0")
assert private[3] == gpu_before[3] and private[2] != gpu_before[2]
assert private[4] & 0o777 == 0o666
directory = Path("/dev/eqs-waydroid").stat()
assert directory.st_uid == 0 and directory.st_mode & 0o777 == 0o700
assert config.read_text().count("lxc.mount.entry = /dev/eqs-waydroid/kgsl-3d0 ") == 1
print("PASS: private KGSL mapping is idempotent; host owner/mode/device unchanged")
