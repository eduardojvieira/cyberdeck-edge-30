#!/usr/bin/env python3
"""Apply the reviewed cumulative H29 fixes to an OFFLINE clean Droidian root."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PORT = HERE.parent


def install(root, source, destination, mode=0o644):
    target = root / destination.lstrip('/')
    # Refuse a symlink escape from an otherwise trusted image tree.
    if not target.resolve().is_relative_to(root):
        raise ValueError(f'path escapes image: {destination}')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    target.chmod(mode)


def configure_wayfire(source, destination):
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config.read(source)
    assert {'ipc', 'ipc-rules', 'wm-actions', 'scale'} <= set(config['core']['plugins'].split())
    changes = {
        'autostart': {'plasma': 'exec /usr/local/libexec/eqs-plasma-start'},
        'core': {'transaction_timeout': '1000', 'vwidth': '4', 'vheight': '1', 'xwayland': 'true'},
        'output:HWCOMPOSER-1': {'scale': '2.0', 'mode': 'auto', 'transform': '270'},
        'autorotate-iio': {'lock_rotation': 'true'},
        'place': {'mode': 'maximize'},
        'input': {'tap_to_click': 'true', 'edge_swipe_section_length': '0'},
        'command': {
            'command_eqs_home': '/usr/bin/busctl --user --timeout=2 call org.kde.plasmashell /Mobile org.kde.plasmashell openHomeScreen',
            'binding_eqs_home': 'edge-swipe up 1'},
        'scale': {'toggle': 'none', 'toggle_all': 'edge-swipe left 1'},
        'cube': {'activate': 'none', 'rotate_left': 'none', 'rotate_right': 'none'},
    }
    for group, values in changes.items():
        if group not in config:
            config.add_section(group)
        config[group].update(values)
    with destination.open('w') as f:
        config.write(f)


def apply(root, assets, touch):
    root = root.resolve(strict=True)
    if root == Path('/') or not (root / 'etc/os-release').is_file():
        raise ValueError('requires an offline image root, never /')
    assert 'ID=droidian\n' in (root / 'etc/os-release').read_text()
    assert touch in ('stock', 'replacement')
    # All assets were checked before the build; verify the two ABI-sensitive additions again.
    inputs = json.loads((assets / 'INPUTS.json').read_text())
    for name in ('camera-qt5.so', 'hci_vhci.ko', 'bnep.ko'):
        assert hashlib.sha256((assets / name).read_bytes()).hexdigest() == inputs[name]['sha256']

    for source in (PORT / 'adaptation-motorola-eqs').rglob('*'):
        rel = source.relative_to(PORT / 'adaptation-motorola-eqs')
        if rel.parts[0] not in ('etc', 'usr'):
            continue
        if source.is_symlink():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.unlink(missing_ok=True)
            target.symlink_to(os.readlink(source))
        elif source.is_file():
            install(root, source, str(rel), source.stat().st_mode & 0o777)
    diagnostics = PORT / 'bringup/diagnostics'
    for name in ('eqs-wayfire-session', 'eqs-plasma-start'):
        install(root, diagnostics / name, f'usr/local/libexec/{name}', 0o755)
    install(root, diagnostics / '60-eqs-session-bus.conf',
            'etc/systemd/system/plasma-mobile-wf.service.d/60-eqs-session-bus.conf')
    for name in ('eqs-native-modules.conf', 'eqs-supermodem.conf'):
        install(root, diagnostics / name, f'etc/lxc/{name}')
    install(root, assets / 'eqs-init.mmi.rc', 'etc/lxc/eqs-init.mmi.rc')
    lxc = root / 'var/lib/lxc/android/config'
    text = lxc.read_text()
    assert 'lxc.mount.entry = /vendor_dlkm vendor_dlkm ' in text
    for name in ('eqs-native-modules.conf', 'eqs-supermodem.conf'):
        assert name not in text, 'expected clean base, not an already patched/private root'
        text += f'\nlxc.include = /etc/lxc/{name}\n'
    lxc.write_text(text)
    for name in ('a730_sqe.fw', 'a730_zap.b00', 'a730_zap.b01', 'a730_zap.b02',
                 'a730_zap.mdt', 'gmu_gen70000.bin'):
        install(root, assets / name, f'usr/lib/firmware/{name}')
    for name in ('motorola-eqs-dev.conf', 'motorola-eqs-media.conf'):
        install(root, HERE / name, f'usr/lib/modules-load.d/{name}')
    bt = 'usr/local/lib/eqs-h29-bluetooth'
    for name in ('hci_vhci.ko', 'bnep.ko'):
        install(root, assets / name, f'{bt}/{name}')
    (root / bt / 'SHA256SUMS').write_text(''.join(
        f"{inputs[n]['sha256']}  {n}\n" for n in ('hci_vhci.ko', 'bnep.ko')))
    install(root, HERE / 'eqs-h29-bluetooth-modules.service',
            'etc/systemd/system/eqs-h29-bluetooth-modules.service')
    install(root, HERE / '30-eqs-h29-modules.conf',
            'etc/systemd/system/bluebinder.service.d/30-eqs-h29-modules.conf')

    home = root / 'home/droidian'
    (home / '.config/plasma-mobile-wf').mkdir(parents=True, exist_ok=True)
    configure_wayfire(root / 'usr/share/plasma-mobile-wf/wayfire.ini',
                      home / '.config/plasma-mobile-wf/wayfire.ini')
    install(root, diagnostics / 'startkderc', 'home/droidian/.config/startkderc')
    camera = 'home/droidian/.local/opt/eqs-camera-qt5-5.15.15'
    install(root, assets / 'camera-qt5.so', f'{camera}/lib/libQt5WaylandClient.so.5.15.15', 0o755)
    (root / camera / 'lib/libQt5WaylandClient.so.5').symlink_to('libQt5WaylandClient.so.5.15.15')
    install(root, assets / 'qt-LICENSE.LGPL3', f'{camera}/LICENSE.LGPL3')
    install(root, PORT / 'qt5-wayland/fix-native-orientation.patch', f'{camera}/fix-native-orientation.patch')
    install(root, PORT / 'qt5-wayland/droidian-camera', 'home/droidian/.local/bin/droidian-camera', 0o755)
    install(root, PORT / 'qt5-wayland/droidian-camera.desktop',
            'home/droidian/.local/share/applications/droidian-camera.desktop')
    for name, target, mode in (
        ('osk', '.local/bin/osk', 0o755),
        ('eqs-osk.desktop', '.local/share/applications/eqs-osk.desktop', 0o644),
        ('eqs-osk-reset.desktop', '.config/autostart/eqs-osk-reset.desktop', 0o644),
    ):
        install(root, PORT / 'shell' / name, f'home/droidian/{target}', mode)
    wallpaper = home / '.local/share/plasma/wallpapers/org.kde.image'
    shutil.copytree(root / 'usr/share/plasma/wallpapers/org.kde.image', wallpaper)
    subprocess.run(['patch', '-p1', '--batch', '--fuzz=0', '-i',
                    str(PORT / 'plasma-mobile-wf/follow-desktop-wallpaper.patch')], cwd=wallpaper, check=True)
    if touch == 'replacement':
        install(root, HERE / 'replacement-touch.rules',
                'etc/udev/rules.d/99-eqs-replacement-touch-calibration.rules')
    (root / 'etc/eqs-image-profile').write_text(f'preview=20260910\ntouch={touch}\nboot=H29\n')
    # Snapshot is the BUILD input, not a permanent lock on the running distro.
    (root / 'etc/apt/apt.conf.d/90-droidian-snapshot').write_text('Acquire::Droidian::Version "current";\n')
    install(root, diagnostics / '90-eqs-dev.conf', 'etc/systemd/journald.conf.d/90-eqs-dev.conf')
    # A future package trigger must not silently replace the frozen working boot set.
    (root / 'etc/flash-bootimage').mkdir(exist_ok=True)
    (root / 'etc/flash-bootimage/01prevent-flashing').write_text('FLASH_BOOTIMAGE=no\n')
    # Size is established OFFLINE. No repair/PV/filesystem resizing at phone startup.
    (root / 'var/lib/halium/requires-lvm-resize').unlink(missing_ok=True)
    # Fresh identity at first boot; no live-phone configuration/credential directories copied.
    (root / 'etc/machine-id').write_text('')
    for f in (root / 'etc/ssh').glob('ssh_host_*'):
        f.unlink()
    for f in (root / 'var/lib/dbus/machine-id', root / 'var/lib/systemd/random-seed'):
        f.unlink(missing_ok=True)
    uid, gid = [int(v) for v in next(line for line in (root / 'etc/passwd').read_text().splitlines()
                                    if line.startswith('droidian:')).split(':')[2:4]]
    if os.geteuid() == 0:
        for path in [home, *home.rglob('*')]:
            os.chown(path, uid, gid, follow_symlinks=False)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit('usage: apply-fixes.py OFFLINE_ROOT INPUT_DIRECTORY stock|replacement')
    apply(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])
    print('PASS: cumulative offline fixes applied; no camera/hardware/service started')
