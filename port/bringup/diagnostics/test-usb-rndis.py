#!/usr/bin/env python3
"""USB lifecycle regression on ordinary host files; never device/configfs evidence."""
import fcntl
import os
from pathlib import Path
import subprocess
import tempfile

source = Path(__file__).with_name('eqs-usb-rndis').read_text()
cases = ('idempotent', 'restart', 'foreign', 'invalid-argument', 'typec-host',
         'typec-unknown', 'role-race', 'typec-race', 'owner-race', 'partial', 'extra-function',
         'changed-identity', 'signal', 'concurrent', 'invalid-interface', 'stop-in-host',
         'owner-unreadable', 'stop-read-error')
failed = []
for case in cases:
    try:
        with tempfile.TemporaryDirectory(prefix='eqs-usb-') as temp:
            root = Path(temp)
            gadget = root / 'sys/kernel/config/usb_gadget/eqs-debug'
            gadget.parent.mkdir(parents=True)
            udc = root / 'sys/class/udc/a600000.dwc3'
            udc.mkdir(parents=True)
            (udc / 'function').write_text('')
            role = root / 'sys/class/usb_role/a600000.ssusb-role-switch/role'
            role.parent.mkdir(parents=True)
            role.write_text('none\n')
            typec = root / 'sys/class/typec/port0/data_role'
            typec.parent.mkdir(parents=True)
            typec.write_text('host [device]\n')
            (root / 'run').mkdir()
            bindir = root / 'bin'
            bindir.mkdir()
            (bindir / 'id').write_text('#!/bin/sh\necho 0\n')
            (bindir / 'cat').write_text('''#!/bin/sh
case "$1" in
    */ifname) printf '%s\n' "${TEST_INTERFACE:-usb7}";;
    */function)
        foreign=$(/usr/bin/cat "$1") || exit $?
        if [ -n "$foreign" ]; then echo "$foreign"
        elif [ -f "$ROOT/sys/kernel/config/usb_gadget/eqs-debug/UDC" ] &&
             [ "$(/usr/bin/cat "$ROOT/sys/kernel/config/usb_gadget/eqs-debug/UDC")" = a600000.dwc3 ]; then
            echo eqs-debug
        fi;;
    */UDC)
        value=$(/usr/bin/cat "$1") || exit $?
        if [ "${FAULT:-}" = unbind-read ] && [ -z "$value" ]; then exit 1; fi
        printf '%s\n' "$value";;
    *) exec /usr/bin/cat "$@";;
esac
''')
            (bindir / 'ip').write_text('''#!/bin/sh
printf '%s\n' "$*" >> "$ROOT/ip.log"
if [ "$1" = address ]; then
    case "${FAULT:-}" in
        role) echo host > "$ROOT/sys/class/usb_role/a600000.ssusb-role-switch/role"; exit 1;;
        typec) echo '[host] device' > "$ROOT/sys/class/typec/port0/data_role"; exit 1;;
        owner) printf '' > "$ROOT/sys/kernel/config/usb_gadget/eqs-debug/UDC";
               echo foreign > "$ROOT/sys/class/udc/a600000.dwc3/function"; exit 1;;
        unreadable) rm "$ROOT/sys/class/udc/a600000.dwc3/function"; exit 1;;
        signal) kill -TERM "$PPID"; exit 1;;
    esac
fi
''')
            for binary in bindir.iterdir():
                binary.chmod(0o755)
            script = root / 'helper'
            script.write_text(source.replace('/sys/', temp + '/sys/').replace('/run/', temp + '/run/'))
            env = {**os.environ, 'PATH':str(bindir)+':'+os.environ['PATH'], 'ROOT':temp}

            def run(*args, **settings):
                return subprocess.run(['sh', str(script), *args], env={**env, **settings},
                                      capture_output=True, text=True, timeout=5)

            if case in ('idempotent', 'restart', 'extra-function', 'changed-identity', 'stop-in-host', 'stop-read-error'):
                first = run()
                assert first.returncode == 0, first.stderr
                bound = gadget / 'UDC'
                if case == 'idempotent':
                    stamp = bound.stat().st_mtime_ns
                    previous = (root / 'ip.log').read_text()
                    result = run()
                    assert result.returncode == 0, result.stderr
                    assert bound.stat().st_mtime_ns == stamp, 'must not rebind a working gadget'
                    assert (root / 'ip.log').read_text() == previous + '-br address show dev usb7\n'
                elif case == 'changed-identity':
                    (gadget / 'idProduct').write_text('0x0001\n')
                    result = run('--stop')
                    assert result.returncode != 0 and bound.read_text().strip() == 'a600000.dwc3'
                elif case == 'stop-read-error':
                    result = run('--stop', FAULT='unbind-read')
                    assert result.returncode != 0, 'an unreadable binding is not a verified stop'
                    assert bound.read_text().strip() == '' and role.read_text().strip() == 'device'
                else:
                    if case == 'stop-in-host':
                        role.write_text('host\n')
                    result = run('--stop')
                    assert result.returncode == 0, result.stderr
                    assert bound.read_text().strip() == '', 'stop must release only our UDC binding'
                    assert role.read_text().strip() == ('host' if case == 'stop-in-host' else 'device')
                    if case == 'restart':
                        assert run('--stop').returncode == 0, 'already stopped must be harmless'
                        assert run('--start').returncode == 0, 'reuse our unbound definition'
                        assert bound.read_text().strip() == 'a600000.dwc3'
                    elif case == 'extra-function':
                        (gadget / 'functions/acm.usb0').mkdir()
                        assert run().returncode != 0, 'do not adopt an altered gadget'
                        assert bound.read_text().strip() == ''
            elif case in ('role-race', 'typec-race', 'owner-race', 'signal', 'invalid-interface', 'owner-unreadable'):
                settings = {'TEST_INTERFACE':'usb7:22'} if case == 'invalid-interface' else {'FAULT':case.split('-')[0]}
                if case == 'owner-unreadable':
                    settings = {'FAULT':'unreadable'}
                result = run(**settings)
                assert result.returncode != 0, result
                binding = 'a600000.dwc3' if case == 'owner-unreadable' else ''
                assert (gadget / 'UDC').read_text().strip() == binding, 'rollback requires confirmed ownership'
                expected = 'host' if case == 'role-race' else ('device' if case in ('owner-race', 'typec-race', 'owner-unreadable') else 'none')
                assert role.read_text().strip() == expected, 'rollback must not overwrite vendor/foreign ownership'
                if case == 'invalid-interface':
                    assert not (root / 'ip.log').exists()
            else:
                args = ()
                if case == 'foreign':
                    (udc / 'function').write_text('foreign\n')
                elif case == 'invalid-argument':
                    args = ('--unexpected',)
                elif case.startswith('typec-'):
                    typec.write_text('[host] device\n' if case == 'typec-host' else '')
                elif case == 'partial':
                    gadget.mkdir()
                with (root / 'run/eqs-usb-rndis.lock').open('w') as lock:
                    if case == 'concurrent':
                        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    result = run(*args)
                assert result.returncode != 0, result
                assert role.read_text().strip() == 'none'
                assert gadget.exists() == (case == 'partial')
                assert not (root / 'ip.log').exists()
        print(f'PASS: {case}', flush=True)
    except AssertionError as error:
        failed.append(case)
        print(f'FAIL: {case}: {error}', flush=True)
assert not failed, failed
print(f'PASS: {len(cases)} USB lifecycle checks; host file model, not HIL')
