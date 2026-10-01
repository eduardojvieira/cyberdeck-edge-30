#!/usr/bin/env python3
"""Host-safe launcher checks: no GUI, device access, or downloads."""
import os
import configparser
from pathlib import Path
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='eqs engineering ') as directory:
    home = Path(directory)
    binary = home / 'mock'
    binary.write_text('#!/bin/sh\nprintf "%s\\0" "${LD_PRELOAD+set}" '
                      '"${QT_PLUGIN_PATH+set}" "${QT_QPA_PLATFORMTHEME+set}" '
                      '"$QT_QPA_PLATFORM" "$FONTCONFIG_FILE" "$FLATPAK_GL_DRIVERS" "$LD_LIBRARY_PATH" "$@"\n')
    binary.chmod(0o700)
    env = os.environ | {'HOME': directory, 'LD_PRELOAD': '', 'QT_PLUGIN_PATH': 'bad',
                        'QT_QPA_PLATFORMTHEME': 'bad', 'QT_QPA_PLATFORM': 'wayland',
                        'FONTCONFIG_FILE': 'global-fonts', 'FLATPAK_GL_DRIVERS': 'hybris',
                        'LD_LIBRARY_PATH': 'inherited-vendor-libs'}
    args = ['file with spaces.sm', '--literal']
    prefix = directory + '/.local/opt/smath-studio-1.5.0.9678'
    targets = {
        'siyuan': ('/usr/bin/siyuan', ['', 'set', 'set', 'wayland', 'global-fonts', 'hybris',
                                      'inherited-vendor-libs', '--ozone-platform=x11', '--disable-gpu']),
        'smath-studio': ('/usr/bin/mono', ['', 'set', 'set', 'wayland',
                                         prefix + '/fonts.conf', 'hybris', '/home/linuxbrew/.linuxbrew/lib',
                                         '--config', prefix + '/mono.config', prefix + '/Solver.exe']),
        'fritzing': ('/usr/bin/fritzing', ['', '', '', 'xcb', 'global-fonts', 'hybris', 'inherited-vendor-libs']),
        'kicad': ('/usr/bin/flatpak.real', ['', 'set', 'set', 'wayland', 'global-fonts', 'default',
                                           'inherited-vendor-libs', 'run', '--env=LIBGL_ALWAYS_SOFTWARE=1',
                                           '--env=GALLIUM_DRIVER=softpipe', 'org.kicad.KiCad']),
    }
    for name, (target, expected) in targets.items():
        candidate = home / name
        candidate.write_text((root / name).read_text().replace(target, shlex.quote(str(binary))))
        subprocess.run(['sh', '-n', str(candidate)], check=True)
        result = subprocess.run(['sh', str(candidate), *args], env=env,
                                capture_output=True, check=True, timeout=5)
        assert result.stdout.split(b'\0') == [s.encode() for s in expected + args] + [b''], (name, result)
        assert not result.stderr, result
web_apps = {
    'engineeringpaper': 'https://engineeringpaper.xyz/',
    'calcpad': 'https://calcpad.eu/Ide',
    'excalidraw': 'https://excalidraw.com/',
    'affine-web': 'https://app.affine.pro/',
    'appflowy-web': 'https://appflowy.com/app/',
}
for name, url in web_apps.items():
    desktop = configparser.ConfigParser(interpolation=None)
    desktop.read(root / (name + '.desktop'))
    entry = desktop['Desktop Entry']
    assert shlex.split(entry['Exec']) == ['/usr/bin/chromium', '--app=' + url]
    assert entry['TryExec'] == '/usr/bin/chromium' and entry['Terminal'] == 'false'
    assert entry['Type'] == 'Application'
fonts = ET.parse(root / 'smath-fonts.conf').getroot()
assert not fonts.findall('include')  # Keep user/global font rules outside this app.
assert [(n.attrib, n.text) for n in fonts.findall('dir')] == [({}, '/usr/share/fonts')]
assert [(n.attrib, n.text) for n in fonts.findall('cachedir')] == [({'prefix': 'xdg'}, 'smath-fontconfig')]
print('PASS: five official web launchers, SiYuan X11/software rendering, quoted argv, private SMath fonts, native Qt5 and KiCad-only software GL; mocks, no GUI/hardware')
