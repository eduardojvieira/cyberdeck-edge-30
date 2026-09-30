#!/usr/bin/env python3
"""Run the exact Geany single-file C commands in a disposable directory."""
import configparser
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parent
cfg = configparser.ConfigParser(interpolation=None)
cfg.read(root / 'geany-filetypes.c')
settings = configparser.ConfigParser(interpolation=None)
settings.read(root / 'geany.conf')
assert settings['tools']['terminal_cmd'].endswith(' -e /bin/sh %c')
assert settings['VTE'].getboolean('run_in_vte') is False
with tempfile.TemporaryDirectory(prefix='eqs c test ') as directory:
    folder = Path(directory)
    (folder / 'hola test.c').write_bytes((root / 'hola.c').read_bytes())
    def command(key):
        return cfg['build-menu'][key].replace('%f', 'hola test.c').replace('%e', 'hola test')
    for key in ('FT_00_CM', 'FT_01_CM'):
        subprocess.run(['/bin/sh', '-c', command(key)], cwd=folder, check=True, timeout=30)
    for value, code in [('42\n', 0), ('bad\n', 1)]:
        result = subprocess.run(['/bin/sh', '-c', command('EX_00_CM')], cwd=folder,
                                input=value, capture_output=True, text=True, timeout=30)
        assert result.returncode == code, result
        if code == 0:
            assert 'Escribiste 42' in result.stdout, result
        else:
            assert 'Entrada inválida' in result.stderr, result
print('PASS: Geany compile/build/run, paths with spaces, stdin and invalid-input exit status')
