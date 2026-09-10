#!/usr/bin/env python3
"""Read-only acceptance of the actual mounted image, not just its recipe."""
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root, assets = map(Path, sys.argv[1:3])
inputs = json.loads((assets / 'INPUTS.json').read_text())
version = subprocess.check_output(['dpkg-query', '--admindir=' + str(root / 'var/lib/dpkg'),
    '-W', '-f=${Version}', 'plasma-mobile-wf'], text=True)
assert version == '6.3.3-1~git20250414214107.69444e6.next.upgrade.6.3+eqs4', version
config = configparser.ConfigParser(interpolation=None)
config.read(root / 'home/droidian/.config/plasma-mobile-wf/wayfire.ini')
for group, key, value in [('core', 'transaction_timeout', '1000'), ('place', 'mode', 'maximize'),
    ('output:HWCOMPOSER-1', 'scale', '2.0'), ('output:HWCOMPOSER-1', 'transform', '270'),
    ('autorotate-iio', 'lock_rotation', 'true'), ('input', 'edge_swipe_section_length', '0'),
    ('scale', 'toggle_all', 'edge-swipe left 1'), ('command', 'binding_eqs_home', 'edge-swipe up 1')]:
    assert config[group][key] == value, (group, key)
assert (root / 'home/droidian/.config/startkderc').read_text().strip() == '[General]\nsystemdBoot=false'
for name, path in {
    'camera-qt5.so': 'home/droidian/.local/opt/eqs-camera-qt5-5.15.15/lib/libQt5WaylandClient.so.5.15.15',
    'hci_vhci.ko': 'usr/local/lib/eqs-h29-bluetooth/hci_vhci.ko',
    'bnep.ko': 'usr/local/lib/eqs-h29-bluetooth/bnep.ko',
    'eqs-init.mmi.rc': 'etc/lxc/eqs-init.mmi.rc',
    **{f'candidate-{name}.img': f'boot/{name}.img' for name in ('boot', 'vendor_boot', 'dtbo', 'vbmeta')},
    **{name: f'usr/lib/firmware/{name}' for name in ('a730_sqe.fw','a730_zap.b00','a730_zap.b01',
                                                  'a730_zap.b02','a730_zap.mdt','gmu_gen70000.bin')},
}.items():
    with (root / path).open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == inputs[name]['sha256'], path
assert (root / 'usr/lib/droid-vendor-overlay/etc/media_profiles_vendor.xml').readlink() == Path('media_profiles_cape.xml')
lxc = (root / 'var/lib/lxc/android/config').read_text()
for name in ('eqs-native-modules.conf', 'eqs-supermodem.conf'):
    assert lxc.count('lxc.include = /etc/lxc/' + name) == 1
    assert lxc.index(name) > lxc.index('/vendor_dlkm vendor_dlkm')
assert 'msm-eva\n' in (root / 'usr/lib/modules-load.d/motorola-eqs-media.conf').read_text()
for rel in ('home/droidian/.local/bin/osk', 'home/droidian/.local/bin/droidian-camera',
            'usr/bin/droid/droid-get-bt-address.sh', 'usr/local/libexec/eqs-plasma-start',
            'usr/local/libexec/eqs-wayfire-session'):
    assert (root / rel).stat().st_mode & 0o111, rel
assert 'syncLockWallpaper()' in (root / 'home/droidian/.local/share/plasma/wallpapers/org.kde.image/contents/ui/main.qml').read_text()
assert 'current' in (root / 'etc/apt/apt.conf.d/90-droidian-snapshot').read_text()
assert (root / 'etc/flash-bootimage/01prevent-flashing').read_text() == 'FLASH_BOOTIMAGE=no\n'
profile = (root / 'etc/eqs-image-profile').read_text()
touch = root / 'etc/udev/rules.d/99-eqs-replacement-touch-calibration.rules'
if 'touch=replacement\n' in profile:
    assert 'LIBINPUT_CALIBRATION_MATRIX}="2 0 0 0 2 0"' in touch.read_text()
else:
    assert 'touch=stock\n' in profile and not touch.exists()
here = Path(__file__).resolve().parent
for source, destination in (
    ('eqs-h29-bluetooth-modules.service', 'etc/systemd/system/eqs-h29-bluetooth-modules.service'),
    ('30-eqs-h29-modules.conf', 'etc/systemd/system/bluebinder.service.d/30-eqs-h29-modules.conf'),
    ('motorola-eqs-media.conf', 'usr/lib/modules-load.d/motorola-eqs-media.conf'),
):
    assert (here / source).read_bytes() == (root / destination).read_bytes(), destination
assert not (root / 'etc/machine-id').read_text()
for pattern in ('home/*/.ssh/*', 'root/.ssh/*', 'etc/ssh/ssh_host_*',
                'home/*/.codex', 'home/*/.pi', 'etc/NetworkManager/system-connections/*'):
    assert not list(root.glob(pattern)), f'private identity/configuration: {pattern}'
for rel in ('var/lib/halium/requires-lvm-resize',
            'etc/systemd/system/timers.target.wants/eqs-preview.timer',
            'etc/systemd/system/multi-user.target.wants/eqs-usb-host-test.service'):
    assert not (root / rel).exists() and not (root / rel).is_symlink(), rel
print('PASS: image contains cumulative H29/Plasma/rotation/camera/Bluetooth/OSK fixes and clean identities')
