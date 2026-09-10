#!/usr/bin/env python3
"""Check camera-only library selection, argument preservation and upgrade fallback."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='camera orientation ') as tmp:
    home = Path(tmp)
    library = home / '.local/opt/eqs-camera-qt5-5.15.15/lib'
    library.mkdir(parents=True)
    binary = home / 'camera'
    binary.write_text('#!/bin/sh\nprintf "%s\\0" "$LD_LIBRARY_PATH" "$@"\n')
    binary.chmod(0o700)
    dpkg = home / 'dpkg-query'
    dpkg.write_text('#!/bin/sh\nprintf "%s" "$TEST_QT_VERSION"\n')
    dpkg.chmod(0o700)
    launcher = home / 'launch'
    launcher.write_text((root / 'droidian-camera').read_text().replace(
        'exec /usr/bin/droidian-camera', 'exec ' + shlex.quote(str(binary))))
    env = os.environ | {'HOME': tmp, 'PATH': tmp + ':' + os.environ['PATH'],
                       'LD_LIBRARY_PATH': '/original/libs', 'TEST_QT_VERSION': '5.15.15-3'}
    args = ['a path with spaces', '--literal']
    for present, version in [(False, '5.15.15-3'), (True, '5.15.15-3'),
                             (True, '5.15.15-4'), (True, '5.15.16-1')]:
        if present:
            (library / 'libQt5WaylandClient.so.5').touch()
        result = subprocess.run(['sh', str(launcher), *args], env=env | {'TEST_QT_VERSION': version},
                                capture_output=True, timeout=5, check=True)
        selected = present and version == '5.15.15-3'
        expected = (str(library) + ':' if selected else '') + '/original/libs'
        assert result.stdout.split(b'\0') == [expected.encode(), *[a.encode() for a in args], b''], result
        assert (b'needs rebuilding' in result.stderr) != selected, result
    assert env['LD_LIBRARY_PATH'] == '/original/libs'
print('PASS: camera-scoped library, argv, missing-library and Qt-update fallback')
