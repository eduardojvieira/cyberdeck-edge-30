#!/usr/bin/env python3
"""Exercise the patched pinned ramdisk on host; never mount a block device."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('prepare', Path(__file__).with_name('prepare-bringup-initramfs.py'))
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
source = Path(sys.argv[1])
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    (root / 'scripts').mkdir()
    for name in patch.HASHES:
        shutil.copyfile(source / name, root / name)
    patch.prepare(root, 'eqs-host-test')
    text = (root / 'scripts/halium').read_text()
    mountroot = text.split('\nmountroot() {', 1)[1]
    assert 'e2fsck' not in mountroot
    assert 'resize_lvm_if_needed' not in mountroot
    assert 'resize_userdata_if_needed' not in mountroot
    assert 'mount --bind /run/eqs-modules' in text
    assert 'cp -a /lib/modules/. /run/eqs-modules/' in text
    helpers = text.split('# eqs diagnostic policy:', 1)[1].split('mountroot() {', 1)[0]
    helpers = helpers[helpers.index('eqs_mark()'):]
    mounts = root / 'mounts'
    mounts.write_text('/dev/fake /root ext4 ro,relatime 0 0\nnone /unrelated tmpfs rw 0 0\n')
    probe = helpers.replace('/proc/mounts', str(mounts)) + '\neqs_mark() { printf "%s\\n" "$*"; }\neqs_mounts TEST\n'
    result = subprocess.run(['bash', '-c', probe], capture_output=True, text=True, check=True)
    assert result.stdout == 'MOUNT TEST /dev/fake /root ext4 ro,relatime\n', result.stdout
    for stage in ('ROOT_MOUNT', 'ANDROID_MOUNT', 'ROOT_MOVE', 'ANDROID_MOVE', 'ANDROID_BIND'):
        assert f'eqs_mounts {stage}\n' in text
    for lvm, part, expected in [('yes', '/dev/fake/root', 0), ('yes', '', 81), ('no', '/dev/fake/root', 81)]:
        # panic returns deliberately: the guard must still never continue.
        script = helpers + '''
eqs_mark() { :; }
halium_panic() { printf 'PANIC\n'; }
sleep() { exit 81; }
use_lvm=$1; _syspart=$2
eqs_require_lvm
printf 'CONTINUED\n'
'''
        result = subprocess.run(['bash', '-c', script, 'test', lvm, part], text=True, capture_output=True, timeout=5)
        assert result.returncode == expected, result
        assert ('CONTINUED' in result.stdout) == (expected == 0), result.stdout
    init_text = (root / 'init').read_text()
    validation = 'validate_init() {' + init_text.split('validate_init() {', 1)[1].split('\n}', 1)[0] + '\n}'
    validation = validation.replace('/dev/kmsg', '/dev/null')
    mock = 'run-init() { [ "$1 $2 $3" = "-n -c /dev/null" ] || return 42; [ "$5" = /sbin/init ]; }\n'
    for path, expected in [('/sbin/init', 0), ('/missing/init', 1)]:
        result = subprocess.run(['bash', '-c', mock + validation + '\nrootmnt=/fake; validate_init "$1"', 'test', path], capture_output=True, text=True)
        assert result.returncode == expected, ('console-independent init validation', result.returncode, expected)
    assert 'exec run-init -c /dev/null ' in init_text
    assert '<${rootmnt}/dev/console' not in init_text
    for name in patch.HASHES:
        subprocess.run(['bash', '-n', str(root / name)], check=True)
    try:
        patch.prepare(root, 'eqs-host-test')
    except ValueError:
        pass
    else:
        raise AssertionError('modified upstream accepted')
print('PASS: LVM success, LVM absent/disabled fail-closed even if panic returns; no repair/resize call in mountroot; syntax and upstream guard')
