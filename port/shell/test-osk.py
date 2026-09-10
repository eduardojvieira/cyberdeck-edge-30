#!/usr/bin/env python3
"""Exercise the real gsettings CLI with an isolated keyfile backend."""
import configparser
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
SCHEMA = "org.maliit.keyboard.maliit"
assert (ROOT / "osk").is_file(), "Missing touch-accessible keyboard control"

with tempfile.TemporaryDirectory(prefix="eqs-osk-") as temporary:
    home = Path(temporary)
    (home / "test.gschema.xml").write_text(f'''<schemalist>
      <schema id="{SCHEMA}" path="/org/maliit/keyboard/maliit/">
        <key name="stay-hidden" type="b"><default>false</default></key>
      </schema></schemalist>''')
    env = {"PATH": os.environ["PATH"], "HOME": temporary, "LC_ALL": "C.UTF-8",
           "XDG_CONFIG_HOME": temporary, "GSETTINGS_SCHEMA_DIR": temporary,
           "GSETTINGS_BACKEND": "keyfile", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent"}

    def run(*args):
        return subprocess.run(args, env=env, capture_output=True, text=True, timeout=5)

    assert run("glib-compile-schemas", temporary).returncode == 0
    assert run("sh", "-n", str(ROOT / "osk")).returncode == 0

    def state():
        result = run("gsettings", "get", SCHEMA, "stay-hidden")
        assert result.returncode == 0, result
        return result.stdout.strip()

    for args, expected in [(('off',), 'true'), (('off',), 'true'),
                           ((), 'false'), (('toggle',), 'true'), (('on',), 'false')]:
        result = run("sh", str(ROOT / "osk"), *args)
        assert result.returncode == 0 and state() == expected, result
    print("PASS: off/on, idempotence and both toggle directions")
    for args in [("invalid",), ("off", "extra")]:
        result = run("sh", str(ROOT / "osk"), *args)
        assert result.returncode != 0 and state() == "false", result
    print("PASS: invalid arguments do not change settings")

    run("gsettings", "set", SCHEMA, "stay-hidden", "true").check_returncode()
    desktop = configparser.ConfigParser(interpolation=None)
    desktop.read(ROOT / "eqs-osk-reset.desktop")
    result = run(*shlex.split(desktop["Desktop Entry"]["Exec"]))
    assert result.returncode == 0 and state() == "false", result
    print("PASS: exact autostart command restores touch keyboard availability")
