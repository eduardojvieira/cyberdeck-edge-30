#!/usr/bin/env python3
"""Host-only config/guard regression. Mounted-image acceptance is separate."""
import configparser
import importlib.util
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fixes', here / 'apply-fixes.py')
fixes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixes)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    before, after = root / 'before.ini', root / 'after.ini'
    before.write_text('[core]\nplugins=ipc ipc-rules wm-actions scale session-lock\n'
                      '[custom]\nkeep=100% literal\n'
                      '[output:HWCOMPOSER-1]\nscale=3\ntransform=normal\n')
    original = before.read_bytes()
    fixes.configure_wayfire(before, after)
    c = configparser.ConfigParser(interpolation=None)
    c.read(after)
    assert before.read_bytes() == original
    assert c['custom']['keep'] == '100% literal'
    assert c['core']['transaction_timeout'] == '1000'
    assert c['core']['plugins'].endswith('session-lock')
    assert c['output:HWCOMPOSER-1']['scale'] == '2.0'
    assert c['output:HWCOMPOSER-1']['transform'] == '270'
    assert c['autorotate-iio']['lock_rotation'] == 'true'
    assert c['place']['mode'] == 'maximize'
    assert c['input']['edge_swipe_section_length'] == '0'
    assert c['command']['binding_eqs_home'] == 'edge-swipe up 1'
    assert c['scale']['toggle_all'] == 'edge-swipe left 1'
    before.write_text('[core]\nplugins=session-lock\n')
    try:
        fixes.configure_wayfire(before, after)
        raise RuntimeError('accepted missing navigation IPC')
    except AssertionError:
        pass
    try:
        fixes.apply(Path('/'), root, 'stock')
        raise RuntimeError('accepted host root')
    except ValueError:
        pass
    escape = root / 'escape'
    escape.symlink_to('/etc')
    try:
        fixes.install(root, before, 'escape/eqs-do-not-create')
        raise RuntimeError('accepted escaping destination')
    except ValueError:
        pass
result = subprocess.run(['bash', str(here.parent / 'build-eqs-rootfs.sh')], capture_output=True)
assert result.returncode != 0 and b'--consolidated' in result.stderr
assert b'--historical' in result.stderr
print('PASS: cumulative config, preserved settings, missing plugins, root/path guards, historical-build rejection')
