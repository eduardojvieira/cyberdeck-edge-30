#!/usr/bin/env python3
"""Fake sysfs boundary checks, never boot a processor on the host."""
import os
from pathlib import Path
import subprocess
import tempfile

source = Path(__file__).with_name('eqs-adsp-start').read_text()
for case in ('offline', 'running', 'crashed', 'missing', 'duplicate', 'owner',
             'variant', 'wrong-hardware', 'wrong-firmware', 'bad-hash', 'start-failed'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        def put(path, value):
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(value)
            return p
        base = 'sys/class/remoteproc/remoteproc7'
        put(base + '/name', '3000000.remoteproc-adsp' if case != 'missing' else 'other')
        state = put(base + '/state', case if case in ('running', 'crashed') else 'offline')
        put(base + '/firmware', 'other.mdt' if case == 'wrong-firmware' else 'adsp.mdt')
        put(base + '/device/of_node/compatible', 'other' if case == 'wrong-hardware' else 'qcom,cape-adsp-pas\0')
        (root / 'proc/device-tree/soc/qcom,msm-adsp-loader').mkdir(parents=True)
        if case == 'variant':
            put('proc/device-tree/soc/qcom,msm-adsp-loader/adsp-fw-name', 'other.mdt')
        if case == 'owner':
            put('sys/kernel/boot_adsp/boot', '')
        if case == 'duplicate':
            put('sys/class/remoteproc/remoteproc8/name', '3000000.remoteproc-adsp')
        put('bin/id', '#!/bin/sh\necho 0\n').chmod(0o755)
        put('bin/sha256sum', '#!/bin/sh\ncat >/dev/null\nexit ' + str(int(case == 'bad-hash')) + '\n').chmod(0o755)
        # Model the kernel's synchronous state transition only for this fake file.
        put('bin/cat', '#!/bin/sh\nif [ "$1" = "$STATE" ] && [ "$(/usr/bin/cat "$1")" = start ] && [ "$CASE" != start-failed ]; then echo running; else exec /usr/bin/cat "$@"; fi\n').chmod(0o755)
        script = source
        for prefix in ('/sys/', '/proc/', '/android/'):
            script = script.replace(prefix, tmp + prefix)
        path = put('start-adsp', script)
        result = subprocess.run(['sh', str(path)], capture_output=True, text=True,
                                env={**os.environ, 'PATH': str(root / 'bin') + ':' + os.environ['PATH'], 'STATE': str(state), 'CASE': case})
        assert (result.returncode == 0) == (case in ('offline', 'running')), (case, result)
        if case in ('offline', 'start-failed'):
            assert state.read_text() == 'start\n'
        else:
            assert state.read_text() == (case if case in ('running', 'crashed') else 'offline'), case
print('PASS: exact ADSP/default firmware/owner/state guards, idempotence and failed-start rejection (host files only)')
