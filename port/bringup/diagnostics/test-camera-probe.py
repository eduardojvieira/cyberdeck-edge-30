#!/usr/bin/env python3
"""Host-only safety boundaries. Does not load libhybris or touch a camera."""
import importlib.machinery
import importlib.util
from pathlib import Path
from unittest.mock import patch

p = Path(__file__).with_name('eqs-camera-probe.py')
spec = importlib.util.spec_from_loader('probe', importlib.machinery.SourceFileLoader('probe', str(p)))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
for uid, cid in ((0, '0'), (32011, '-1'), (32011, '8')):
    with patch.object(probe.os, 'geteuid', return_value=uid), patch.object(probe.sys, 'argv', [str(p), cid]), patch.object(probe.C, 'CDLL') as lib:
        try:
            probe.main()
            raise AssertionError('unsafe probe accepted')
        except SystemExit as error:
            assert str(error) == 'Refusing root or out-of-range camera ID'
        lib.assert_not_called()
with patch.object(probe.os, 'geteuid', return_value=32011), patch.object(probe.sys, 'argv', [str(p), '0']), patch.object(probe.os.path, 'exists', return_value=False), patch.object(probe.C, 'CDLL') as lib:
    try:
        probe.main()
        raise AssertionError('recovery probe accepted')
    except SystemExit as error:
        assert 'not recovery' in str(error)
    lib.assert_not_called()
print('PASS: camera probe rejects root, invalid IDs and non-native runtime before loading libhybris (host mocks only)')
alias = Path(__file__).resolve().parents[2] / 'adaptation-motorola-eqs/usr/lib/droid-vendor-overlay/etc/media_profiles_vendor.xml'
assert alias.is_symlink() and alias.readlink() == Path('media_profiles_cape.xml')
print('PASS: camera profile alias stays relative and points at the stock eqs cape profile')
