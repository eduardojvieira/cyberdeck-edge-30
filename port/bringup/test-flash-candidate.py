#!/usr/bin/env python3
"""Fake-fastboot contract tests; no phone access."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import tempfile

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    shutil.copyfile(Path(__file__).with_name('flash-candidate.sh'), root / 'flash-candidate.sh')
    for folder, names in [('candidate', ['boot','vendor_boot','dtbo','vbmeta']), ('rescue', ['boot','vendor_boot','dtbo','vbmeta','recovery'])]:
        (root / folder).mkdir()
        for name in names:
            (root / folder / (name + '.img')).write_bytes(b'fixture')
    (root / 'SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}\n' for p in sorted(root.rglob('*.img'))))
    binary = root / 'bin'
    binary.mkdir()
    (binary / 'fastboot').write_text('''#!/bin/bash
printf '%s\\n' "$*" >>"$CALLS"
[[ $1 == -s && $2 == test-device ]] || exit 99
shift 2
if [[ $1 == set_active ]]; then
 [[ $2 == a ]] || exit 99
 [[ ${FAIL_ACTIVE:-no} == no ]] || exit 1
 touch "$ACTIVE"
 exit 0
fi
if [[ $1 == getvar ]]; then
 case $2 in
 product) echo "product: ${PRODUCT:-eqs}";;
 current-slot) if [[ -f $ACTIVE && ${RESET_OK:-yes} == yes ]]; then echo 'current-slot: a'; else echo "current-slot: ${SLOT:-a}"; fi;;
 securestate) echo "securestate: ${SECURESTATE:-flashing_unlocked}";;
 is-userspace) echo "is-userspace: ${USERSPACE:-no}";;
 slot-unbootable:a) if [[ -f $ACTIVE ]]; then echo 'slot-unbootable:a: no'; else echo "slot-unbootable:a: ${UNBOOTABLE:-no}"; fi;;
 slot-retry-count:a) if [[ -f $ACTIVE && ${RESET_OK:-yes} == yes ]]; then echo 'slot-retry-count:a: 7'; else echo "slot-retry-count:a: ${RETRIES:-0}"; fi;;
 version-bootloader)
 echo '(bootloader) version-bootloader[0]: MBM-3.0-eqs-c66ed235df0-250323-U1SQS'
 echo "(bootloader) version-bootloader[1]: ${BASE_END:-34.52-21-1-16-5b71b0}"
 echo 'version-bootloader: Done';;
 *) exit 99;; esac
elif [[ $1 == flash ]]; then
 [[ $2 != "${FAIL_PART:-none}" ]] || exit 1
else exit 99; fi
''')
    (binary / 'fastboot').chmod(0o755)
    calls = root / 'calls'
    active = root / 'active'
    env = dict(os.environ, PATH=f'{binary}:{os.environ["PATH"]}', CALLS=str(calls), ACTIVE=str(active))
    def run(args, **extra):
        calls.write_text('')
        active.unlink(missing_ok=True)
        result = subprocess.run(['bash', str(root / 'flash-candidate.sh'), *args], env=dict(env, **extra), capture_output=True, text=True, timeout=10)
        return result.returncode, calls.read_text().splitlines()
    code, log = run(['--check'])
    assert code == 0 and not log
    code, log = run(['--flash-a', 'test-device'])
    assert code == 0, log
    assert [line for line in log if ' flash ' in line] == [f'-s test-device flash {p}_a candidate/{p}.img' for p in ['vbmeta','dtbo','vendor_boot','boot']]
    assert log[-4:] == ['-s test-device set_active a', '-s test-device getvar current-slot', '-s test-device getvar slot-unbootable:a', '-s test-device getvar slot-retry-count:a']
    code, log = run(['--rescue-a', 'test-device'], SLOT='b', UNBOOTABLE='yes')
    assert code == 0, log
    assert [line for line in log if ' flash ' in line] == [f'-s test-device flash {p}_a rescue/{p}.img' for p in ['vbmeta','dtbo','vendor_boot','boot','recovery']]
    assert log[-4] == '-s test-device set_active a'
    code, log = run(['--flash-a', 'test-device'], RESET_OK='no')
    assert code != 0 and log[-1] == '-s test-device getvar slot-retry-count:a'
    for extra in ({'PRODUCT':'bronco'}, {'SLOT':'b'}, {'SECURESTATE':'locked'}, {'USERSPACE':'yes'}, {'RETRIES':'bad'}, {'UNBOOTABLE':'bad'}, {'BASE_END':'34.52-21-1-160-5b71b0'}):
        code, log = run(['--flash-a', 'test-device'], **extra)
        assert code != 0 and not any(' flash ' in line or ' set_active ' in line for line in log)
    code, log = run(['--flash-a', 'test-device'], FAIL_PART='dtbo_a')
    assert code != 0 and log[-1] == '-s test-device flash dtbo_a candidate/dtbo.img'
    code, log = run(['--rescue-a', 'test-device'], SLOT='b', FAIL_PART='recovery_a')
    assert code != 0 and log[-1] == '-s test-device flash recovery_a rescue/recovery.img'
    code, log = run(['--flash-a', 'test-device'], FAIL_ACTIVE='yes')
    assert code != 0 and log[-1] == '-s test-device set_active a'
    checksums = (root / 'SHA256SUMS').read_text()
    for invalid in (checksums + checksums.splitlines()[0] + '\n', '\n'.join(checksums.splitlines()[1:]) + '\n'):
        (root / 'SHA256SUMS').write_text(invalid)
        code, log = run(['--flash-a', 'test-device'])
        assert code != 0 and not log
    (root / 'SHA256SUMS').write_text(checksums)
    (root / 'candidate/boot.img').write_bytes(b'tampered')
    code, log = run(['--flash-a', 'test-device'])
    assert code != 0 and not log
print('PASS: integrity; Motorola fragmented bootloader; A-only writes; B-active rescue; slot reset/verification; failclosed preflight and partial failure')
