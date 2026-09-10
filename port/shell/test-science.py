#!/usr/bin/env python3
"""Check scientific launcher argv and graphics isolation with mock binaries."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='eqs science ') as directory:
    home = Path(directory)
    conda = home / '.local/opt/miniforge3/bin/conda'
    conda.parent.mkdir(parents=True)
    conda.write_text('#!/bin/sh\nprintf "%s\\0" "${LD_PRELOAD+set}" '
                     '"${QT_PLUGIN_PATH+set}" "${QML2_IMPORT_PATH+set}" '
                     '"${QT_QPA_PLATFORMTHEME+set}" "$QT_QPA_PLATFORM" "$@"\n')
    conda.chmod(0o700)
    env = os.environ | {'HOME': str(home), 'LD_PRELOAD': '', 'QT_PLUGIN_PATH': 'native',
                        'QML2_IMPORT_PATH': 'native', 'QT_QPA_PLATFORMTHEME': 'KDE',
                        'QT_QPA_PLATFORM': 'wayland'}
    for launcher, command in [('sage', ['sage']), ('science-python', ['python']),
                              ('spyder', ['spyder']),
                              ('jupyter-lab', ['jupyter', 'lab', '--ServerApp.ip=127.0.0.1'])]:
        subprocess.run(['sh', '-n', str(root / launcher)], check=True)
        args = ['path with spaces', '--literal']
        result = subprocess.run(['sh', str(root / launcher), *args], env=env,
                                capture_output=True, timeout=5)
        assert result.returncode == 0 and not result.stderr, result
        graphical = ['', '', '', '', 'xcb'] if launcher == 'spyder' else ['set'] * 4 + ['wayland']
        expected = graphical + ['run', '--no-capture-output', '-n', 'science'] + command + args
        assert result.stdout.split(b'\0') == [x.encode() for x in expected] + [b''], result
    command = shlex.split(next(line[5:] for line in (root / 'jupyterlab.desktop').read_text().splitlines()
                              if line.startswith('Exec=')))
    assert command[:2] == ['/home/droidian/.local/bin/ghostty', '-e']
    assert command[-1] == '/home/droidian/.local/bin/jupyter-lab'
    overrides = dict.fromkeys(('__EGL_VENDOR_LIBRARY_FILENAMES', 'LIBGL_ALWAYS_SOFTWARE',
                               'GDK_BACKEND', 'GSK_RENDERER'), 'TEST_ONLY')
    result = subprocess.run([*command[2:-1], '/usr/bin/env'], env=env | overrides,
                            capture_output=True, timeout=5, check=True)
    assert not any(line.split(b'=', 1)[0].decode() in overrides for line in result.stdout.splitlines())
print('PASS: science launcher argv, loopback default, and Spyder-only Qt isolation; mock binaries, no GUI')

# Replace only the fixed Brew prefix in a temporary copy: no test-only setting
# or dependency injection is added to the installed launchers.
with tempfile.TemporaryDirectory(prefix='eqs brew science ') as directory:
    prefix = Path(directory)
    for name, formula, extra in [('octave', 'octave', []), ('octave-cli', 'octave', []),
                                  ('maxima', 'maxima', []),
                                  ('wxmaxima', 'wxmaxima', ['--maxima=PREFIX/opt/maxima/bin/maxima'])]:
        target = prefix / 'opt' / formula / 'bin' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('#!/bin/sh\nprintf "%s\\0" "${LD_PRELOAD+set}" '
                          '"${QT_PLUGIN_PATH+set}" "${QML2_IMPORT_PATH+set}" '
                          '"${QT_QPA_PLATFORMTHEME+set}" "$LIBGL_ALWAYS_SOFTWARE" '
                          '"$GALLIUM_DRIVER" "${PATH%%:*}" "$@"\n')
        target.chmod(0o700)
        launcher = prefix / name
        launcher.write_text((root / name).read_text().replace('/home/linuxbrew/.linuxbrew', str(prefix)))
        subprocess.run(['sh', '-n', str(launcher)], check=True)
        env = os.environ | {'LD_PRELOAD': '', 'QT_PLUGIN_PATH': 'native',
                            'QML2_IMPORT_PATH': 'native', 'QT_QPA_PLATFORMTHEME': 'KDE', 'GALLIUM_DRIVER': ''}
        result = subprocess.run(['sh', str(launcher), 'path with spaces', '--literal'], env=env,
                                capture_output=True, timeout=5, check=True)
        expected = ['', '', '', '', '1', 'softpipe' if name.startswith('octave') else '',
                    str(prefix / 'opt/gnuplot/bin')]
        expected += [a.replace('PREFIX', str(prefix)) for a in extra] + ['path with spaces', '--literal']
        assert not result.stderr and result.stdout.split(b'\0') == [x.encode() for x in expected] + [b''], result
print('PASS: Brew science argv, exact Maxima backend and process-only library isolation; mock binaries, no GUI')

with tempfile.TemporaryDirectory(prefix='eqs scilab ') as directory:
    home = Path(directory)
    system = home / 'apt-scilab'
    candidate = home / '.local/opt/scilab-2026.1.0/run-scilab'
    candidate.parent.mkdir(parents=True)
    mock = '#!/bin/sh\nprintf "%s\\0" "$0" "$@"\n'
    system.write_text(mock)
    system.chmod(0o700)
    launcher = home / 'scilab'
    launcher.write_text((root / 'scilab').read_text()
                       .replace('/usr/bin/scilab', shlex.quote(str(system)))
                       .replace('/home/droidian/.local/opt/scilab-2026.1.0/run-scilab', shlex.quote(str(candidate))))
    launcher.chmod(0o700)
    env = os.environ | {'HOME': str(home)}
    args = ['path with spaces', '--literal']
    result = subprocess.run([str(launcher), *args], env=env, capture_output=True, timeout=5)
    assert result.returncode != 0 and not result.stdout, result  # No silent 2024 fallback.
    candidate.write_text(mock)
    candidate.chmod(0o700)
    result = subprocess.run([str(launcher), *args], env=env, capture_output=True,
                            timeout=5, check=True)
    assert result.stdout.split(b'\0') == [str(candidate).encode(), *[a.encode() for a in args], b''], result
    cli = home / 'scilab-cli'
    cli.write_text((root / 'scilab-cli').read_text())
    result = subprocess.run(['sh', str(cli), *args], env=env, capture_output=True,
                            timeout=5, check=True)
    assert result.stdout.split(b'\0') == [str(candidate).encode(), b'-nwni', *[a.encode() for a in args], b''], result
desktop = dict(line.split('=', 1) for line in (root / 'scilab.desktop').read_text().splitlines() if '=' in line)
prefix = '/home/droidian/.local/opt/scilab-2026.1.0'
assert desktop['TryExec'] == prefix + '/run-scilab'
assert desktop['Icon'] == prefix + '/share/icons/hicolor/256x256/apps/scilab.png'
print('PASS: Scilab 2026-only launchers, missing-runtime failure, matching CLI argv and independent desktop entry')
