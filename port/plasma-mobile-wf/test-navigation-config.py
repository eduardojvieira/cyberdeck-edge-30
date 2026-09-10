#!/usr/bin/env python3
"""Check session configuration; no compositor, touch input or phone access."""
import configparser
from pathlib import Path
import subprocess
import sys
import tempfile

base = Path(__file__).resolve().parent


def check(path):
    config = configparser.ConfigParser(interpolation=None)
    config.read(path)
    assert config['core'].getint('transaction_timeout') == 1000, 'resize transaction expires before slow clients commit'
    assert config['command'].get('binding_eqs_home') == 'edge-swipe up 1', 'Home gesture missing'
    assert config['command']['command_eqs_home'] == (
        '/usr/bin/busctl --user --timeout=2 call org.kde.plasmashell '
        '/Mobile org.kde.plasmashell openHomeScreen')
    assert config['scale']['toggle'] == 'none'
    assert config['scale']['toggle_all'] == 'edge-swipe left 1'
    assert config['input']['edge_swipe_section_length'] == '0'
    assert all(config['cube'][key] == 'none' for key in ('activate', 'rotate_left', 'rotate_right'))
    assert not any(key.startswith('always_binding') for key in config['command'])
    return config


if len(sys.argv) == 2:
    check(Path(sys.argv[1]))
else:
    with tempfile.TemporaryDirectory(prefix='eqs gestures ') as temp:
        source, result = Path(temp) / 'before.ini', Path(temp) / 'after.ini'
        source.write_text('[core]\nplugins=command scale ipc ipc-rules wm-actions\n'
                          'transaction_timeout=100\n'
                          'background_color=\\#1A1A1AFF\n'
                          '[autostart]\nplasma=preserve-existing-session\n'
                          '[input]\nedge_swipe_threshold=20\n'
                          '[command]\ncommand_volume_up=preserve-volume\n'
                          '[scale]\ntoggle=edge-swipe left 1\n'
                          '[output:HWCOMPOSER-1]\nscale=3.0\n')
        original = source.read_bytes()
        command = [sys.executable, str(base / 'prepare-navigation-config.py'), str(source), str(result)]
        subprocess.run(command, check=True, timeout=15)
        config = check(result)
        assert config['autostart']['plasma'] == 'preserve-existing-session'
        assert config['command']['command_volume_up'] == 'preserve-volume'
        assert config['output:HWCOMPOSER-1']['scale'] == '3.0'
        assert config['input']['edge_swipe_threshold'] == '20'
        assert config['core']['background_color'] == r'\#1A1A1AFF', 'unrelated Wayfire escaping changed'
        assert source.read_bytes() == original
        saved = result.read_bytes()
        assert subprocess.run(command, capture_output=True, timeout=15).returncode != 0
        assert result.read_bytes() == saved
        second = Path(temp) / 'second.ini'
        subprocess.run(command[:-2] + [str(result), str(second)], check=True, timeout=15)
        assert second.read_bytes() == saved, 'configuration must be idempotent'
    print('PASS: gesture routing, bounded resize wait, preservation, existing-output refusal and idempotence; host only')
