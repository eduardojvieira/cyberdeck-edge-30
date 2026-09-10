#!/usr/bin/env python3
"""Stage only the frozen, non-personal image inputs; never copy a live rootfs."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

base = Path(__file__).resolve().parent
repo = base.parent.parent
if len(sys.argv) != 2:
    sys.exit('usage: stage-inputs.py NEW_INPUT_DIRECTORY')
output = Path(sys.argv[1]).resolve()
if output.exists():
    sys.exit('output must not exist')
inputs = json.loads((base / 'inputs.json').read_text())
for name, entry in inputs.items():
    assert Path(name).name == name and name not in ('.', '..'), name
    source = (repo / entry['path']).resolve(strict=True)
    assert source.is_relative_to(repo), source
    with source.open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == entry['sha256'], name
output.mkdir(parents=True)
for name, entry in inputs.items():
    shutil.copyfile(repo / entry['path'], output / name)
shutil.copyfile(base / 'inputs.json', output / 'INPUTS.json')
(output / 'SHA256SUMS').write_text(''.join(
    f"{entry['sha256']}  {name}\n" for name, entry in inputs.items()))
print(f'PASS: {len(inputs)} frozen inputs staged at {output}; no device access')
