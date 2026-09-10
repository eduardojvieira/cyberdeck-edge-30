#!/usr/bin/env python3
"""Host checks only; all system-manager calls are mocked."""
import base64
import configparser
import os
from pathlib import Path
import subprocess
import tempfile

base = Path(__file__).parent
source = (base / 'eqs-capture-once').read_text()
for fail_disarm, fail_adsp, fail_terminal_cleanup, screen, typec_ready in (
    (True, False, False, 'missing', True), (False, False, False, 'missing', False),
    (False, False, False, 'missing', True),
    (False, True, False, 'missing', True), (False, False, True, 'missing', True),
    *((False, False, False, mode, True) for mode in ('ok', 'denied', 'empty', 'invalid', 'timeout')),
):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bindir = root / 'bin'
        bindir.mkdir()
        armed = root / 'etc/systemd/system/multi-user.target.wants/eqs-capture-once.service'
        armed.parent.mkdir(parents=True)
        armed.touch()
        timer = root / 'etc/systemd/system/timers.target.wants/eqs-capture-once.timer'
        timer.parent.mkdir(parents=True)
        timer.touch()
        preview_timer = timer.with_name('eqs-preview.timer')
        preview_timer.touch()
        old_report = root / 'var/log/eqs-bringup/terminal.txt'
        old_report.parent.mkdir(parents=True)
        old_report.write_text('stale proof from another boot')
        old_screen = old_report.with_name('screen.png')
        old_screen.write_bytes(b'stale image from another boot')
        old_screen.with_suffix('.png.partial').write_bytes(b'stale partial image')
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGMQMgkDAAD4AJ3MaiF4AAAAAElFTkSuQmCC')
        fixture = root / 'fixture.png'
        fixture.write_bytes(png)
        for cmd in ('systemctl', 'sleep', 'journalctl', 'sync', 'uname', 'cat', 'ls', 'sha256sum', 'lxc-info', 'lxc-attach', 'runuser', 'dpkg-query'):
            stub = bindir / cmd
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "' + cmd + ' $*" >> "$TRACE"\n')
            stub.chmod(0o755)
        grim = root / 'usr/bin/grim'
        grim.parent.mkdir(parents=True)
        if screen != 'missing':
            grim.touch(mode=0o755)
            with (bindir / 'runuser').open('a') as stub:
                stub.write('case "$*" in *"/grim "*)\n')
                if screen == 'ok':
                    stub.write('/usr/bin/cat "$PNG_FIXTURE"\n')
                elif screen in ('denied', 'timeout'):
                    stub.write('printf "partial PNG"; echo "capture refused or timed out" >&2; exit ' + ('1' if screen == 'denied' else '124') + '\n')
                elif screen == 'invalid':
                    stub.write('printf "not a PNG"\n')
                stub.write(';; esac\n')
        if fail_disarm:
            stub = bindir / 'rm'
            stub.write_text('#!/bin/sh\necho "Read-only file system" >&2\nexit 1\n')
            stub.chmod(0o755)
        adsp = root / 'usr/local/sbin/eqs-adsp-start'
        adsp.parent.mkdir(parents=True)
        adsp.write_text('#!/bin/sh\necho adsp-start >> "$TRACE"\necho ADSP_DIAGNOSTIC\nexit ' + str(int(fail_adsp)) + '\n')
        adsp.chmod(0o755)
        usb = adsp.with_name('eqs-usb-rndis')
        usb.write_text('#!/bin/sh\necho usb-start >> "$TRACE"\n')
        usb.chmod(0o755)
        wait = bindir / 'udevadm'
        wait.write_text('#!/bin/sh\necho "udevadm $*" >> "$TRACE"\nexit ' + str(int(not typec_ready)) + '\n')
        wait.chmod(0o755)
        if fail_terminal_cleanup:
            probe = root / 'usr/local/libexec/eqs-terminal-probe'
            probe.parent.mkdir(parents=True)
            probe.touch(mode=0o755)
            with (bindir / 'runuser').open('a') as stub:
                stub.write('if [ "${4:-}" = rm ]; then echo "user cleanup denied" >&2; exit 1; fi\n')
        script = root / 'capture'
        script.write_text(source.replace('/etc/systemd/', tmp + '/etc/systemd/').replace('/var/log/', tmp + '/var/log/').replace('/dev/kmsg', tmp + '/kmsg').replace('/usr/local/sbin/', tmp + '/usr/local/sbin/').replace('/usr/local/libexec/', tmp + '/usr/local/libexec/').replace('/home/droidian/', tmp + '/home/droidian/').replace('/usr/bin/grim', str(grim)))
        trace = root / 'trace'
        result = subprocess.run(['sh', str(script)], env={**os.environ, 'PATH':str(bindir)+':'+os.environ['PATH'], 'TRACE':str(trace), 'PNG_FIXTURE':str(fixture)}, capture_output=True, text=True, timeout=20)
        assert result.returncode == int(fail_disarm or fail_terminal_cleanup), result
        assert armed.exists() == fail_disarm
        assert timer.exists() == fail_disarm
        assert preview_timer.exists(), 'capture must not disable the separate preview boot timer'
        kmsg = (root / 'kmsg').read_text() if (root / 'kmsg').exists() else ''
        assert 'NATIVE_CAPTURE START' in kmsg, ('no evidence before filesystem failure', fail_disarm)
        if fail_disarm:
            assert 'DISARM FAIL' in kmsg and 'Read-only file system' in kmsg, kmsg
            assert not trace.exists(), trace.read_text()
        elif fail_terminal_cleanup:
            assert 'user cleanup denied' in result.stderr
            assert 'systemd-run' not in trace.read_text(), 'must not reuse stale terminal evidence after failed cleanup'
            assert (root / 'var/log/eqs-bringup/progress.txt').read_text() == 'START\n'
        else:
            lines = trace.read_text().splitlines()
            assert lines.count('adsp-start') == 1
            assert lines.count('usb-start') == int(typec_ready), 'do not bind before Type-C readiness'
            assert 'udevadm wait --timeout=8 --initialized=false /sys/class/typec/port0' in lines
            if typec_ready:
                assert lines.index('adsp-start') < lines.index('usb-start')
            else:
                assert 'EQS USB TYPEC WAIT FAILED' in (root / 'var/log/eqs-bringup/usb.txt').read_text()
            assert not old_report.exists(), 'never reuse old terminal evidence'
            assert (root / 'var/log/eqs-bringup/adsp.txt').read_text() == 'ADSP_DIAGNOSTIC\n'
            assert lines[-2:] == ['journalctl --sync', 'sync '], lines
            assert (root / 'var/log/eqs-bringup/progress.txt').read_text() == 'START\nCAPTURED\n'
            assert (root / 'var/log/eqs-bringup/media.txt').exists()
            assert 'cat /proc/asound/cards /proc/modules' in lines
            assert 'lxc-attach -n android -- /system/bin/dumpsys media.camera' in lines
            assert 'pactl list short sinks' in trace.read_text()
            assert not old_screen.with_suffix('.png.partial').exists(), 'never retain partial screenshots'
            assert old_screen.exists() == (screen == 'ok'), 'never reuse a stale or failed screenshot'
            screen_log = old_screen.with_suffix('.txt').read_text()
            if screen == 'ok':
                assert old_screen.read_bytes() == png
                assert 'SCREEN_CAPTURE_OK' in screen_log
            elif screen == 'missing':
                assert 'SCREEN_CAPTURE_UNAVAILABLE' in screen_log
                assert '/grim ' not in trace.read_text()
            elif screen in ('denied', 'timeout'):
                assert 'SCREEN_CAPTURE_FAILED exit=' + ('1' if screen == 'denied' else '124') in screen_log
                assert 'capture refused or timed out' in screen_log
            else:
                assert 'SCREEN_CAPTURE_INVALID' in screen_log
            if screen != 'missing':
                launch = trace.read_text()
                assert '--user --quiet --pipe --wait --collect' in launch
                assert '--property=RuntimeMaxSec=8' in launch and '--property=TimeoutStopSec=2' in launch
                assert '--property=LimitFSIZE=16M' in launch
                assert '/grim -o HWCOMPOSER-1 -t png -' in launch
unit = (base / 'eqs-capture-once.service').read_text()
assert 'SuccessAction=reboot\n' in unit and 'FailureAction=reboot\n' in unit
assert 'RebootArgument=bootloader\n' in unit
timer = (base / 'eqs-capture-once.timer').read_text()
assert 'OnBootSec=90\n' in timer and 'Unit=eqs-capture-once.service\n' in timer
print('PASS: capture/disarm/ADSP failure evidence; reboot delegated to systemd (host only)')
print('PASS: screenshot unavailable/success/refusal/timeout/invalid/empty and stale cleanup (host mocks only)')

# Preview reuses capture, but must never inherit the returning trial's reboot policy.
preview = configparser.ConfigParser(interpolation=None)
preview.read(base / 'eqs-preview.service')
assert preview['Unit']['SuccessAction'] == preview['Unit']['FailureAction'] == 'none'
assert 'RebootArgument' not in preview['Unit']
assert preview['Service']['ExecStart'] == '/usr/local/sbin/eqs-capture-once'
assert preview['Service']['TimeoutStartSec'] == '180'
preview_timer = configparser.ConfigParser(interpolation=None)
preview_timer.read(base / 'eqs-preview.timer')
assert preview_timer['Timer']['OnBootSec'] == '90'
assert preview_timer['Timer']['Unit'] == 'eqs-preview.service'
assert preview_timer['Install']['WantedBy'] == 'timers.target'
print('PASS: separate opt-in preview timer retained, no automatic reboot (host contract only)')

# Ordinary files model ownership/selection only, not USB enumeration or configfs ABI.
for busy, fail_ip, fail_link, role in (
    (True, False, False, 'none'), (False, False, False, 'none'),
    (False, True, False, 'none'), (False, False, True, 'none'),
    (False, False, False, 'device'), (False, True, False, 'device'),
    (False, False, False, 'host'), (False, False, False, 'unknown'),
):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        udc = root / 'sys/class/udc/a600000.dwc3'
        udc.mkdir(parents=True)
        (udc / 'function').write_text('foreign' if busy else '')
        role_file = root / 'sys/class/usb_role/a600000.ssusb-role-switch/role'
        role_file.parent.mkdir(parents=True)
        role_file.write_text(role + '\n')
        typec = root / 'sys/class/typec/port0/data_role'
        typec.parent.mkdir(parents=True)
        typec.write_text('host [device]\n')
        (root / 'run').mkdir()
        gadget = root / 'sys/kernel/config/usb_gadget/eqs-debug'
        gadget.parent.mkdir(parents=True)
        bindir = root / 'bin'
        bindir.mkdir()
        (bindir / 'id').write_text('#!/bin/sh\necho 0\n')
        (bindir / 'ip').write_text('#!/bin/sh\nprintf "%s\\n" "$*" >>"$TRACE"\nexit ' + str(int(fail_ip)) + '\n')
        # Model the interface name assigned on bind, not a requested fixed name.
        (bindir / 'cat').write_text('''#!/bin/sh
case "$1" in
    */ifname) echo usb7;;
    */function)
        foreign=$(/usr/bin/cat "$1") || exit $?
        if [ -n "$foreign" ]; then echo "$foreign"
        elif [ -f "$ROOT/sys/kernel/config/usb_gadget/eqs-debug/UDC" ] &&
             [ "$(/usr/bin/cat "$ROOT/sys/kernel/config/usb_gadget/eqs-debug/UDC")" = a600000.dwc3 ]; then
            echo eqs-debug
        fi;;
    *) exec /usr/bin/cat "$@";;
esac
''')
        if fail_link:
            (bindir / 'ln').write_text('#!/bin/sh\nexit 1\n')
        for binary in bindir.iterdir():
            binary.chmod(0o755)
        script = root / 'usb'
        script.write_text((base / 'eqs-usb-rndis').read_text().replace('/sys/', tmp + '/sys/').replace('/run/', tmp + '/run/'))
        result = subprocess.run(['sh', str(script)], env={**os.environ, 'PATH':str(bindir)+':'+os.environ['PATH'], 'TRACE':str(root/'trace'), 'ROOT':tmp}, capture_output=True, text=True, timeout=5)
        refused = busy or role not in ('none', 'device')
        assert result.returncode == int(refused or fail_ip or fail_link), result
        assert role_file.read_text().strip() == (role if result.returncode else 'device'), result
        if refused:
            assert not gadget.exists()
        elif fail_link:
            assert not (gadget / 'UDC').exists(), 'must not unbind before binding'
        else:
            assert not (gadget / 'functions/rndis.usb0/ifname').exists(), 'use assigned name; do not write ifname'
            assert (gadget / 'UDC').read_text() == ('\n' if fail_ip else 'a600000.dwc3\n')
            assert (gadget / 'configs/c.1/rndis.usb0').resolve() == gadget / 'functions/rndis.usb0'
            assert 'dev usb7' in (root / 'trace').read_text()
print('PASS: USB controller ownership, exact binding, failure unbind (host files only)')

# Config contract only: namespace visibility and ABI still require target evidence.
entries = [line for line in (base / 'eqs-native-modules.conf').read_text().splitlines()
           if line and not line.startswith('#')]
assert entries == ['lxc.mount.entry = /run/eqs-modules vendor_dlkm/lib/modules none bind,ro 0 0']
print('PASS: required readonly candidate-module LXC mount declaration (host only)')

# No real SSH/network or credentials: validate the direct-link launch boundary.
for role, host_key, interface in (('device', True, 'usb7'), ('host', True, 'usb7'),
                                 ('device', False, 'usb7'), ('device', True, 'usb7:22'),
                                 ('device', True, '7')):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        gadget = root / 'sys/kernel/config/usb_gadget/eqs-debug'
        (gadget / 'functions/rndis.usb0').mkdir(parents=True)
        (gadget / 'UDC').write_text('a600000.dwc3\n')
        (gadget / 'functions/rndis.usb0/ifname').write_text(interface + '\n')
        role_file = root / 'sys/class/usb_role/a600000.ssusb-role-switch/role'
        role_file.parent.mkdir(parents=True)
        role_file.write_text(role + '\n')
        for key in ('etc/dropbear/dropbear_ecdsa_host_key', 'root/.ssh/authorized_keys'):
            path = root / key
            path.parent.mkdir(parents=True)
            if host_key:
                path.write_text('test fixture, not a key\n')
        bindir = root / 'bin'
        bindir.mkdir()
        (bindir / 'id').write_text('#!/bin/sh\necho 0\n')
        for name in ('ip', 'dropbear'):
            (bindir / name).write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$TRACE"\n')
        for path in bindir.iterdir():
            path.chmod(0o755)
        source = (base / 'eqs-usb-shell').read_text()
        for prefix in ('/sys/', '/etc/', '/root/'):
            source = source.replace(prefix, tmp + prefix)
        source = source.replace('/usr/local/libexec/eqs-dropbear-2016.74', str(bindir / 'dropbear'))
        script = root / 'shell'
        script.write_text(source)
        trace = root / 'trace'
        result = subprocess.run(['sh', str(script)], env={**os.environ, 'PATH':str(bindir)+':'+os.environ['PATH'], 'TRACE':str(trace)}, capture_output=True, text=True)
        allowed = role == 'device' and host_key and interface == 'usb7'
        assert (result.returncode == 0) == allowed, result
        assert trace.exists() == allowed, result
        if allowed:
            lines = trace.read_text().splitlines()
            assert lines[0] == '-6 address add fe80::2/64 dev usb7 nodad', lines
            assert '-F -E -s -j -k -I 35 ' in lines[1], lines
            assert '-p [fe80::2%usb7]:22 ' in lines[1] and ' -R ' not in lines[1], lines
print('PASS: USB-only SSH launch, missing-key/role/interface rejection (host mocks only)')

# Fragmented socket reads, EOF and bounded response allocation, without a WM.
import importlib.util
import json
import struct
spec = importlib.util.spec_from_file_location('ipc_snapshot', base / 'eqs-wayfire-state.py')
ipc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ipc)

class FragmentedSocket:
    def __init__(self, payload, expected=None):
        self.payload = bytearray(payload)
        self.expected = expected or {'method': 'window-rules/list-outputs', 'data': {}}
    def sendall(self, request):
        size, = struct.unpack('=I', request[:4])
        assert size == len(request) - 4
        assert json.loads(request[4:]) == self.expected
    def recv(self, size):
        chunk = self.payload[:min(size, 2)]
        del self.payload[:len(chunk)]
        return chunk

payload = json.dumps([{'name': 'HWCOMPOSER-1'}]).encode()
assert ipc.query(FragmentedSocket(struct.pack('=I', len(payload)) + payload), 'window-rules/list-outputs') == [{'name': 'HWCOMPOSER-1'}]
request = {'method': 'wayfire/get-config-option', 'data': {'option': 'autorotate-iio/lock_rotation'}}
response = json.dumps({'value': 'true'}).encode()
assert ipc.query(FragmentedSocket(struct.pack('=I', len(response)) + response, request), request['method'], request['data']) == {'value': 'true'}
for response, error in ((b'\x01', EOFError), (struct.pack('=I', 2**20 + 1), ValueError), (struct.pack('=I', 0), ValueError)):
    try:
        ipc.query(FragmentedSocket(response), 'window-rules/list-outputs')
    except error:
        pass
    else:
        raise AssertionError('invalid IPC frame accepted')
print('PASS: readonly Wayfire IPC framing, partial reads, EOF/size rejection (host only)')
