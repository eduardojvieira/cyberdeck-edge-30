#!/usr/bin/env python3
"""Read-only native check; run in the Edge's graphical D-Bus session."""
import os
from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit
import gi

gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

os.environ.setdefault('DBUS_SESSION_BUS_ADDRESS', f'unix:path=/run/user/{os.getuid()}/bus')
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
wallpaper = bus.call_sync('org.kde.plasmashell', '/PlasmaShell',
    'org.kde.PlasmaShell', 'wallpaper', GLib.Variant('(u)', (0,)),
    GLib.VariantType.new('(a{sv})'), Gio.DBusCallFlags.NONE, 3000, None).unpack()[0]
uri = urlsplit(wallpaper['Image'])
assert uri.scheme == 'file' and uri.netloc in ('', 'localhost'), 'Expected local image wallpaper'
desktop = Path(unquote(uri.path))
lock = subprocess.check_output(['kreadconfig6', '--file', 'plasma-sessionlockrc',
    '--group', 'General', '--key', 'wallpaperFile'], text=True).strip()
lock = Path(unquote(urlsplit('file:' + lock).path))
assert lock.is_file(), 'Lock image does not exist'
if desktop.is_dir():
    assert (desktop / 'contents').resolve() in lock.resolve().parents, 'Lock is not from the selected package'
else:
    assert desktop.resolve() == lock.resolve(), 'Desktop and lock wallpaper differ'
print('PASS: desktop and lock refer to the same image/package')
