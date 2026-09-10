#!/usr/bin/env python3
"""Check the small launcher contract without starting Hollywood or real tmux."""
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent
subprocess.run(['sh', '-n', str(root / 'hollywood')], check=True)
with tempfile.TemporaryDirectory(prefix='eqs hollywood ') as directory:
    home = Path(directory)
    tmux = home / 'tmux'
    tmux.write_text('#!/bin/sh\n[ -z "${TMUX+x}" ] || exit 42\n'
                    'printf "%s\\0" "$@"\n')
    tmux.chmod(0o700)
    env = os.environ | {'HOME': str(home), 'PATH': f'{home}:/usr/bin:/bin',
                        'TMUX': '/working-session/do-not-touch,1,0'}
    expected = ['-L', 'eqs-hollywood', '-f', str(home / '.config/hollywood/tmux.conf'),
                'new-session', '-A', '-s', 'hollywood', '-n', 'controller',
                str(home / '.local/opt/hollywood/bin/hollywood'),
                '-s', '4', '-d', '30']
    for args in ([], ['--splits', '3', '--delay', '60'], ['--help']):
        result = subprocess.run(['sh', str(root / 'hollywood'), *args], env=env,
                                capture_output=True, timeout=5)
        assert result.returncode == 0 and not result.stderr, result
        assert result.stdout.split(b'\0') == [x.encode() for x in expected + args] + [b'']
    config = (root / 'hollywood.tmux.conf').read_text()
    assert 'set -g default-terminal tmux-256color\n' in config
    assert 'set -g status off\n' in config
    assert 'bind-key -n C-c kill-server\n' in config
    assert 'set -g destroy-unattached on\n' in config
print('PASS: private tmux server, split/delay forwarding, inherited-session isolation and cleanup config; host only')
