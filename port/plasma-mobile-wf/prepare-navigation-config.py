#!/usr/bin/env python3
"""Prepare a new Wayfire INI; never change or reload the live session."""
import configparser
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: prepare-navigation-config.py EXISTING_INI NEW_INI')
config = configparser.ConfigParser(interpolation=None)
config.optionxform = str
with Path(sys.argv[1]).open() as source:
    config.read_file(source)
required = {'command', 'scale', 'ipc', 'ipc-rules', 'wm-actions'}
if not required <= set(config['core']['plugins'].split()):
    raise SystemExit('required navigation plugins missing')
changes = {
    # Software-rendered clients can miss 100ms and commit stale, undersized buffers.
    # ponytail: stalls beyond 1s still need upstream transaction handling.
    'core': {'transaction_timeout': '1000'},
    'command': {
        'command_eqs_home': '/usr/bin/busctl --user --timeout=2 call org.kde.plasmashell /Mobile org.kde.plasmashell openHomeScreen',
        # Regular commands respect the compositor lock grab; not always/repeatable.
        'binding_eqs_home': 'edge-swipe up 1',
    },
    'scale': {'toggle': 'none', 'toggle_all': 'edge-swipe left 1'},
    # Whole edges instead of Droidian's three independent sections.
    'input': {'edge_swipe_section_length': '0'},
    'cube': {'activate': 'none', 'rotate_left': 'none', 'rotate_right': 'none'},
}
for group, values in changes.items():
    if not config.has_section(group):
        config.add_section(group)
    config[group].update(values)
# Exclusive create rejects an existing file/dangling symlink without truncation.
with Path(sys.argv[2]).open('x') as result:
    config.write(result)
