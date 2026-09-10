#!/usr/bin/env python3
"""Host transformation checks against the exact private stock file, not HIL."""
from pathlib import Path
import subprocess
import sys
import tempfile

source = Path(sys.argv[1]).read_bytes()
builder = Path(__file__).with_name('prepare-supermodem-rc.py')
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    stock, output = root / 'stock.rc', root / 'overlay.rc'
    stock.write_bytes(source)
    def run():
        return subprocess.run([sys.executable, str(builder), str(stock), str(output)], capture_output=True)
    result = run()
    assert result.returncode == 0, result.stderr
    original, patched = source.splitlines(), output.read_bytes().splitlines()
    assert len(original) == len(patched)
    changes = [(a, b) for a, b in zip(original, patched) if a != b]
    assert len(changes) == 2
    for before, after in changes:
        assert b'/vendor/super_modem' in before
        assert before == after + b' context=u:object_r:firmware_file:s0'
        assert after.endswith(b' ro nosuid nodev')
    existing = output.read_bytes()
    assert run().returncode != 0, 'must not overwrite an existing output'
    assert output.read_bytes() == existing
    output.unlink()
    stock.write_bytes(source + b'\n')
    assert run().returncode != 0 and not output.exists(), 'unknown firmware must fail closed'
print('PASS: exactly two context removals, readonly/slot/selector retained, unknown input and overwrite rejected')
