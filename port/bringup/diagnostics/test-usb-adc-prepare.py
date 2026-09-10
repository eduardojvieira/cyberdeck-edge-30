#!/usr/bin/env python3
"""Exercise the actual one-boot helper on host files, not a phone or kernel."""
import configparser
import fcntl
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

base = Path(__file__).parent
source = (base / 'eqs-usb-adc-prepare').read_text()
old, new = b'H29 fixture\n', b'diagnostic fixture\n'
sha = lambda value: hashlib.sha256(value).hexdigest()
cases = ('apply', 'unarmed', 'wrong-marker', 'wrong-kernel', 'loaded',
         'not-tmpfs', 'wrong-bind', 'bad-baseline', 'bad-candidate',
         'copy-failed', 'sync-failed', 'late-load', 'unprivileged', 'concurrent')
for case in cases:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        state = root / 'var/lib/eqs-usb-adc'
        modules = root / 'run/eqs-modules'
        sysmodules = root / 'sys/module'
        for path in (state, modules, sysmodules, root / 'lib', root / 'bin'):
            path.mkdir(parents=True, exist_ok=True)
        native = root / 'lib/modules'
        if case == 'wrong-bind':
            native.mkdir()
        else:
            native.symlink_to(modules)
        current, replacement = modules / 'qti_glink_charger.ko', state / 'qti_glink_charger.ko'
        current.write_bytes(old if case != 'bad-baseline' else b'wrong baseline')
        replacement.write_bytes(new if case != 'bad-candidate' else b'wrong candidate')
        initial = current.read_bytes()
        marker = state / 'armed'
        if case != 'unarmed':
            marker.write_text(('wrong' if case == 'wrong-marker' else sha(new)) + '\n')
        if case == 'loaded':
            (sysmodules / 'qti_glink_charger').mkdir()
        bootid = root / 'proc/sys/kernel/random/boot_id'
        bootid.parent.mkdir(parents=True)
        bootid.write_text('fixture-boot\n')
        stubs = {
            'id': 'echo ' + ('1000' if case == 'unprivileged' else '0'),
            'uname': 'echo ' + ('wrong' if case == 'wrong-kernel' else '5.10.209-android13-0-gbd42a1bb7281'),
            'findmnt': 'echo ' + ('ext4' if case == 'not-tmpfs' else 'tmpfs'),
            'sync': 'echo sync >> "$TRACE"; ' + ('exit 1' if case == 'sync-failed' else 'exit 0'),
            'install': 'echo install >> "$TRACE"\n'
                       '[ ! -e "$STATE/armed" ] && grep -qx sync "$TRACE" || exit 11\n' +
                       ('exit 1' if case == 'copy-failed' else
                        f'{subprocess.check_output(["which", "install"], text=True).strip()} "$@"') +
                       ('\nmkdir "$SYSMODULES/qti_glink_charger"' if case == 'late-load' else ''),
        }
        for name, body in stubs.items():
            path = root / 'bin' / name
            path.write_text('#!/bin/sh\n' + body + '\n')
            path.chmod(0o755)
        # Same path-rewrite pattern as the existing USB host test; no test-only
        # root override or power-control path is added to the production helper.
        script = re.sub(r'/(?:sys|run|proc|var|lib)/', lambda m: tmp + m[0], source)
        script = re.sub(r'(?m)^baseline=.*$', 'baseline=' + sha(old), script)
        script = re.sub(r'(?m)^candidate=.*$', 'candidate=' + sha(new), script)
        helper = root / 'helper'
        helper.write_text(script)
        env = {**os.environ, 'PATH': str(root / 'bin') + ':' + os.environ['PATH'],
               'TRACE': str(root / 'trace'), 'STATE': str(state), 'SYSMODULES': str(sysmodules)}
        with (root / 'run/eqs-usb-adc.lock').open('w') as lock:
            if case == 'concurrent':
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(['sh', str(helper)], env=env, capture_output=True, text=True, timeout=5)
        assert (result.returncode == 0) == (case in ('apply', 'unarmed')), (case, result)
        assert current.read_bytes() == (new if case == 'apply' else initial), (case, result)
        assert not list(modules.glob('.eqs-adc.*')), (case, result)
        assert marker.exists() == (case in ('unprivileged', 'concurrent')), (case, result)
        if case == 'apply':
            assert 'APPLIED boot=fixture-boot' in result.stdout, result
            # Simulate the next initramfs restoring modules from unchanged boot.
            current.write_bytes(old)
            again = subprocess.run(['sh', str(helper)], env=env, capture_output=True, text=True, timeout=5)
            assert again.returncode == 0 and current.read_bytes() == old, again
        print('PASS:', case)

unit = configparser.ConfigParser(interpolation=None)
unit.read(base / 'eqs-usb-adc-prepare.service')
assert unit['Unit']['DefaultDependencies'] == 'no'
assert {'systemd-modules-load.service', 'systemd-udevd.service', 'systemd-udev-trigger.service',
        'sysinit.target'} <= set(unit['Unit']['Before'].split())
assert unit['Service']['ExecStart'] == '/usr/local/sbin/eqs-usb-adc-prepare'
assert unit['Service']['TimeoutStartSec'] == '15s'
assert unit['Unit']['ConditionPathExists'] == '/var/lib/eqs-usb-adc/armed'
assert unit['Install']['WantedBy'] == 'sysinit.target'
assert not re.search(r'\b(rmmod|insmod|modprobe|reboot|fastboot|dd)\b', source)
print('PASS: one-boot file replacement, fail-closed guards; host only')
