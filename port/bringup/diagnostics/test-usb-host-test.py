#!/usr/bin/env python3
"""Host file/command simulation: not proof of USB enumeration or electrical state."""
import configparser
import fcntl
import os
from pathlib import Path
import re
import subprocess
import tempfile

base = Path(__file__).parent
source = (base / 'eqs-usb-host-test').read_text()
cases = ('capture', 'no-host', 'typec-device', 'signal', 'concurrent',
         'wrong-kernel', 'unprivileged', 'no-root', 'duplicate-root',
         'removed', 'replaced', 'host-gone', 'invalid-bus', 'read-failed', 'read-timeout',
         'incomplete-status')
for case in cases:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        parent = root / 'sys/bus/platform/devices/a600000.ssusb'
        controller = parent / 'a600000.dwc3/xhci-hcd.2.auto'
        hub = controller / 'usb2'
        dummy = root / 'sys/devices/dummy_hcd/usb1'
        devices = (parent, parent / 'a600000.dwc3', controller, hub, controller / 'usb3', dummy)
        for device in devices:
            (device / 'power').mkdir(parents=True, exist_ok=True)
            (device / 'power/control').write_text('auto\n')
            (device / 'power/runtime_status').write_text('suspended\n')
        for device, product in ((hub, '0002'), (controller / 'usb3', '0003'), (dummy, '0002')):
            (device / 'idVendor').write_text('1d6b\n')
            (device / 'idProduct').write_text(product + '\n')
        (hub / 'busnum').write_text('2:3\n' if case == 'invalid-bus' else '2\n')
        (hub / 'devnum').write_text('1\n')
        if case == 'no-root':
            (hub / 'idVendor').write_text('1234\n')
        if case == 'duplicate-root':
            duplicate = controller / 'usb4'
            duplicate.mkdir()
            (duplicate / 'idVendor').write_text('1d6b\n')
            (duplicate / 'idProduct').write_text('0002\n')
        role = root / 'sys/class/usb_role/a600000.ssusb-role-switch/role'
        role.parent.mkdir(parents=True)
        role.write_text('none\n' if case == 'no-host' else 'host\n')
        typec = root / 'sys/class/typec/port0/data_role'
        typec.parent.mkdir(parents=True)
        typec.write_text('host [device]\n' if case == 'typec-device' else '[host] device\n')
        (root / 'run/eqs-modules').mkdir(parents=True)
        (root / 'run/eqs-modules/phy-msm-snps-eusb2.ko').write_text('not a module; hash fixture\n')
        (root / 'proc/sys/kernel/random').mkdir(parents=True)
        (root / 'proc/sys/kernel/random/boot_id').write_text('test-boot-id\n')
        (root / 'proc/interrupts').write_text('4: 0 xhci-hcd:usb2\n')
        bindir = root / 'bin'
        bindir.mkdir()
        stubs = {
            'id': 'echo 1000' if case == 'unprivileged' else 'echo 0',
            'uname': 'echo ' + ('wrong-kernel' if case == 'wrong-kernel' else '5.10.209-android13-0-gbd42a1bb7281'),
            'lsusb': '''printf '%s\\n' "$*" >> "$TRACE"
[ "$(cat "$HUB/power/control")" = auto ] || exit 9
if [ "$1" = -v ]; then
  case "$CASE" in
    read-failed) exit 1;; read-timeout) exit 124;;
    incomplete-status) echo 'cannot read port 1 status' >&2; exit 0;;
  esac
  printf ' Hub Port Status:\\n   Port 1: 0000.0101 power connect\\n'
fi''',
            'sleep': '''[ "$1" = 10 ] || exit 0
case "$CASE" in
  signal) kill -TERM "$PPID";;
  removed) rm -r "$HUB";;
  replaced) mv "$HUB" "$HUB.old"; mkdir -p "$HUB/power"; echo auto > "$HUB/power/control";;
  host-gone) echo none > "$ROLE";;
esac''',
        }
        for name, body in stubs.items():
            path = bindir / name
            path.write_text('#!/bin/sh\n' + body + '\n')
            path.chmod(0o755)
        script = root / 'trial'
        modified = re.sub(r'/(?:sys|run|proc)/', lambda match: tmp + match[0], source)
        script.write_text(modified)
        trace = root / 'trace'
        with (root / 'run/eqs-usb-host-test.lock').open('w') as lock:
            if case == 'concurrent':
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(['sh', str(script)], text=True, capture_output=True, timeout=10,
                                    env={**os.environ, 'PATH':str(bindir)+':'+os.environ['PATH'],
                                         'HUB':str(hub), 'ROLE':str(role), 'CASE':case, 'TRACE':str(trace)})
        for device in devices:
            policy = device / 'power/control'
            if policy.exists():
                assert policy.read_text() == 'auto\n', (case, device, result)
        assert role.read_text() == ('none\n' if case in ('no-host', 'host-gone') else 'host\n'), result
        assert typec.read_text() == ('host [device]\n' if case == 'typec-device' else '[host] device\n'), result
        assert 'APPLIED' not in result.stdout, (case, result)
        requests = trace.read_text().splitlines() if trace.exists() else []
        status_reads = [line for line in requests if line.startswith('-v')]
        active = case in ('capture', 'signal', 'removed', 'replaced', 'host-gone', 'read-failed', 'read-timeout', 'incomplete-status')
        assert bool(status_reads) == active, (case, result, requests)
        assert all(line == '-v -d 1d6b:0002 -s 2:1' for line in status_reads), requests
        assert len(status_reads) == (13 if case == 'capture' else 1 if active else 0), (case, requests)
        if case == 'capture':
            assert 'Hub Port Status:' in result.stdout and 'test-boot-id' in result.stdout, result
        if case in ('read-failed', 'read-timeout'):
            assert 'PORT_STATUS_FAILED' in result.stdout, result
        if case == 'incomplete-status':
            assert 'PORT_STATUS_INCOMPLETE' in result.stdout, result
        if case in ('removed', 'replaced', 'host-gone'):
            assert 'HOST_OR_ROOT_GONE' in result.stdout, result
        rejected = case in ('signal', 'concurrent', 'wrong-kernel', 'unprivileged',
                            'no-root', 'duplicate-root', 'invalid-bus', 'read-failed', 'read-timeout', 'incomplete-status')
        assert (result.returncode != 0) == rejected, (case, result)
        print('PASS:', case)

unit = configparser.ConfigParser(interpolation=None)
unit.read(base / 'eqs-usb-host-test.service')
assert unit['Unit']['ConditionPathExists'] == '/etc/eqs-usb-host-test.once'
assert unit['Service']['ExecStartPre'] == '/usr/bin/rm -f /etc/eqs-usb-host-test.once'
assert unit['Service']['Type'] == 'simple'
assert unit['Service']['RuntimeMaxSec'] == '20min'
assert unit['Service']['TimeoutStopSec'] == '10'
assert not any('action' in key or 'reboot' in key for key in unit['Unit'])
print('PASS: opt-in capture, no PM/role writes, no reboot (host only)')
