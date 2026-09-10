#!/usr/bin/env python3
"""Real owned Unix socket checks, fake compositor/D-Bus commands; host only."""
import os
from pathlib import Path
import socket
import subprocess
import tempfile

base = Path(__file__).parent
for case in ('ok', 'missing-bus', 'systemd-boot', 'missing-display', 'split-bus', 'sync-fails'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        runtime, home, bin = root / 'run', root / 'home', root / 'bin'
        for directory in (runtime, bin, home / '.config/plasma-mobile-wf'):
            directory.mkdir(parents=True)
        (home / '.config/plasma-mobile-wf/wayfire.ini').touch()
        config = (base / 'startkderc').read_text()
        (home / '.config/startkderc').write_text(config.replace('false', 'true') if case == 'systemd-boot' else config)
        sockets = []
        try:
            for name, missing in (('bus', 'missing-bus'), ('wayland-0', 'missing-display')):
                if case != missing:
                    sock = socket.socket(socket.AF_UNIX)
                    sock.bind(str(runtime / name))
                    sockets.append(sock)
            for name in ('wayfire', 'dbus-update-activation-environment', 'startplasmamobile'):
                command = bin / name
                command.write_text('#!/bin/sh\nprintf "%s|%s|%s|%s|%s\\n" "' + name + ' $*" "$DBUS_SESSION_BUS_ADDRESS" "$KDE_NO_KWIN" "$QT_QPA_PLATFORM" "$WAYLAND_DISPLAY" >> "$TRACE"\n' + ('exit 1\n' if case == 'sync-fails' and name == 'dbus-update-activation-environment' else ''))
                command.chmod(0o755)
            env = {**os.environ, 'HOME': str(home), 'XDG_RUNTIME_DIR': str(runtime),
                   'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/wrong', 'TRACE': str(root / 'trace'),
                   'WAYLAND_DISPLAY': 'wayland-0'}
            for name in ('eqs-wayfire-session', 'eqs-plasma-start'):
                script = (base / name).read_text().replace('/usr/bin/wayfire', str(bin / 'wayfire')).replace('/usr/bin/dbus-update-activation-environment', str(bin / 'dbus-update-activation-environment')).replace('/usr/bin/startplasmamobile', str(bin / 'startplasmamobile'))
                path = root / name
                path.write_text(script)
                if name == 'eqs-plasma-start':
                    if case in ('missing-bus', 'systemd-boot'):
                        continue
                    env.update(KDE_NO_KWIN='1', DBUS_SESSION_BUS_ADDRESS='unix:path=/wrong' if case == 'split-bus' else f'unix:path={runtime}/bus')
                result = subprocess.run(['sh', str(path)], env=env, capture_output=True, text=True)
                valid = case not in (('missing-bus', 'systemd-boot') if name == 'eqs-wayfire-session' else ('missing-display', 'split-bus', 'sync-fails'))
                assert (result.returncode == 0) == valid, (case, name, result)
            lines = (root / 'trace').read_text().splitlines() if (root / 'trace').exists() else []
            if case in ('missing-bus', 'systemd-boot'):
                assert lines == []
            else:
                assert lines[0].startswith('wayfire -c ') and f'|unix:path={runtime}/bus|1|' in lines[0]
            if case == 'ok':
                assert len(lines) == 3 and lines[1].startswith('dbus-update-activation-environment --systemd ')
                assert '--all' not in lines[1] and lines[1].endswith('|1|wayland|wayland-0')
                assert lines[2].startswith('startplasmamobile ')
            elif case == 'sync-fails':
                assert len(lines) == 2, 'must not launch Plasma after failed environment sync'
            else:
                assert not any(line.startswith('startplasmamobile ') for line in lines)
        finally:
            for sock in sockets:
                sock.close()
print('PASS: one user bus, explicit classic boot, pre-service GUI env, missing socket and sync failure rejection (host only)')
