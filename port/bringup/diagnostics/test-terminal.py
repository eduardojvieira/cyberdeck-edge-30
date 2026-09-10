#!/usr/bin/env python3
"""Exercise PTY gate; mocked identity/version never count as target evidence."""
import os
from pathlib import Path
import pty
import subprocess
import tempfile

probe = Path(__file__).with_name('eqs-terminal-probe')
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    bin = root / 'bin'
    bin.mkdir()
    for name, body in {
        'id': 'echo droidian',
        'cat': 'if [ "$1" = /proc/1/comm ]; then echo systemd; else exec /usr/bin/cat "$@"; fi',
        'tmux': 'echo "tmux host-test"',
        'sleep': ':',
    }.items():
        path = bin / name
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)
    env = {**os.environ, 'HOME': tmp, 'PATH': str(bin) + ':' + os.environ['PATH'], 'TERM': 'xterm-256color'}
    result = subprocess.run(['sh', str(probe)], env=env, capture_output=True)
    assert result.returncode != 0
    report = root / '.local/state/eqs-bringup/terminal.txt'
    assert not report.exists(), 'pipe must not produce PTY evidence'
    master, slave = pty.openpty()
    try:
        result = subprocess.run(['sh', str(probe)], env=env, stdin=slave, stdout=slave, stderr=slave, timeout=5)
        assert result.returncode == 0
    finally:
        os.close(master)
        os.close(slave)
    data = report.read_text()
    assert 'NATIVE_TERMINAL_PTY_OK' in data and '/dev/pts/' in data and 'TERM=xterm-256color' in data
    assert report.stat().st_mode & 0o777 == 0o600
    (bin / 'tmux').write_text('#!/bin/sh\nexit 1\n')
    master, slave = pty.openpty()
    try:
        result = subprocess.run(['sh', str(probe)], env=env, stdin=slave, stdout=slave, stderr=slave, timeout=5)
        assert result.returncode != 0
    finally:
        os.close(master)
        os.close(slave)
    assert 'NATIVE_TERMINAL_PTY_OK' not in report.read_text(), 'partial output is not successful evidence'
print('PASS: pipe rejection, real host PTY gate, private report (identity/version mocked)')
