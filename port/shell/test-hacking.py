#!/usr/bin/env python3
"""Host-safe checks: never scan networks, capture traffic or access hardware."""
import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

path = Path(__file__).with_name('eqs-hacking')
assert path.is_file(), 'Missing hacking menu'
loader = importlib.machinery.SourceFileLoader('eqs_hacking', str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
menu = importlib.util.module_from_spec(spec)
loader.exec_module(menu)

assert len(menu.TOOLS) >= 45, 'Toolbox still limited to the original 13 actions'
assert {'Web y TLS', 'Capturas offline', 'Forense y binarios', 'Auditoría local',
        'Contraseñas (laboratorio)', 'Industrial y electrónica'} <= {row[0] for row in menu.TOOLS.values()}
assert '/usr/sbin' in menu.TOOL_PATH.split(':'), 'Unprivileged SSH PATH hides installed tools'
for answer in ('', '1', '2'):
    with patch('builtins.input', return_value=answer):
        assert menu.choose([('lo', 'lo'), ('wlan0', 'wlan0')], 'Interfaz') == {'': None, '1': 'lo', '2': 'wlan0'}[answer]
for answer in ('0', '3', '-1', 'lo', '1; touch /tmp/no'):
    with patch('builtins.input', return_value=answer):
        try:
            menu.choose([('lo', 'lo'), ('wlan0', 'wlan0')], 'Interfaz')
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted invalid interface choice: ' + answer)
with patch.object(menu.subprocess, 'run') as execute, patch.dict(menu.os.environ, {'PAGER': 'less'}):
    execute.return_value.returncode = 0
    menu.run(['iw', '--version'])
    assert '/usr/sbin' in execute.call_args.kwargs['env']['PATH'].split(':')
    assert execute.call_args.kwargs['env']['PAGER'] == 'cat', 'Tool help must not trap input in another pager'
for key, row in menu.GUIDES.items():
    with patch.object(menu, 'run') as run, patch('builtins.input', side_effect=AssertionError('Help requested a target')):
        menu.action(key)
        run.assert_called_once_with(row[3])
    assert row[3][0] not in ('sudo', 'sh', 'bash', 'eval'), key

for key in menu.TOOLS:
    result = subprocess.run([str(path), '--help', key], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0 and menu.TOOLS[key][1] in result.stdout, result
assert subprocess.run([str(path), '--help', 'unknown'], capture_output=True).returncode == 2
for value in ('--script=exploit', '127.0.0.1;touch /tmp/no', '10.0.0.0/8', ''):
    with patch('builtins.input', return_value=value), patch.object(menu, 'run') as run:
        try:
            menu.action('ports')
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted invalid single-IP target: ' + value)
        run.assert_not_called()
for answer in ('no', ''):
    with patch('builtins.input', side_effect=['127.0.0.1', answer]), patch.object(menu, 'run') as run:
        menu.action('ports')
        run.assert_not_called()
with patch('builtins.input', side_effect=['127.0.0.1', 'si']), patch.object(menu, 'run') as run:
    menu.action('ports')
    run.assert_called_once_with(['nmap', '-sT', '-Pn', '--top-ports', '100',
                                '--max-retries', '1', '--host-timeout', '30s', '127.0.0.1'])
with patch('builtins.input', side_effect=['::1', 'si']), patch.object(menu, 'run') as run:
    menu.action('ports')
    assert run.call_args.args[0][1] == '-6'
with patch('builtins.input', return_value='no'), patch.object(menu, 'choose', return_value='lo'), patch.object(menu, 'run') as run:
    menu.action('capture')
    run.assert_not_called()
with tempfile.TemporaryDirectory() as directory:
    (Path(directory) / 'Documents/EQS-Capturas').mkdir(parents=True, mode=0o755)
    with patch.object(menu.Path, 'home', return_value=Path(directory)), patch('builtins.input', return_value='si'), patch.object(menu, 'choose', return_value='lo'), patch.object(menu, 'run', return_value=124) as run:
        menu.action('capture')
        args = run.call_args.args[0]
        assert args[:12] == ['sudo', 'timeout', '60', 'tcpdump', '-i', 'lo', '-nn', '-s', '128', '-c', '200', '-Z']
        assert Path(args[-1]).stat().st_mode & 0o777 == 0o600
        assert Path(args[-1]).parent.stat().st_mode & 0o777 == 0o700
with patch('builtins.input', return_value='-bad..domain'), patch.object(menu, 'run') as run:
    try:
        menu.action('dns')
    except ValueError:
        pass
    else:
        raise AssertionError('Accepted malformed DNS name')
    run.assert_not_called()
for key in ('route', 'http'):
    with patch('builtins.input', side_effect=['127.0.0.1' if key == 'route' else 'example.com', 'no']), patch.object(menu, 'run') as run:
        menu.action(key)
        run.assert_not_called()
for value in ('https://example.com/', '-bad', 'a;echo hi', 'example.com:443', 'user@example.com', '[::1]', ''):
    with patch('builtins.input', return_value=value), patch.object(menu, 'run') as run:
        try:
            menu.action('http')
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted invalid HTTPS domain: ' + value)
        run.assert_not_called()
with patch('builtins.input', side_effect=['example.com', 'si']), patch.object(menu, 'run') as run:
    menu.action('http')
    run.assert_called_once_with(['curl', '--head', '--connect-timeout', '5', '--max-time', '15', '--proto', '=https', '--url', 'https://example.com/'])
with patch('builtins.input', side_effect=['::1', 'si']), patch.object(menu, 'run') as run:
    menu.action('route')
    run.assert_called_once_with(['traceroute', '-6', '-n', '-q', '1', '-m', '12', '-w', '1', '::1'])
with tempfile.TemporaryDirectory() as directory:
    sample = Path(directory) / 'sample with spaces.pcap'
    sample.write_bytes(b'not a real capture')
    with patch('builtins.input', return_value=str(sample)), patch.object(menu, 'run') as run:
        menu.action('pcap-read')
        run.assert_called_once_with(['tshark', '-n', '-c', '100', '-r', str(sample)])
    for bad in (directory, str(Path(directory) / 'missing')):
        with patch('builtins.input', return_value=bad), patch.object(menu, 'run') as run:
            try:
                menu.action('filetype')
            except (ValueError, OSError):
                pass
            else:
                raise AssertionError('Accepted nonregular/missing input')
            run.assert_not_called()
with patch('builtins.input', return_value='192.168.1.12/24'), patch.object(menu, 'run') as run, patch('builtins.print') as out:
    menu.action('subnet')
    run.assert_not_called()
    assert '192.168.1.0/24' in out.call_args.args[0] and '256' in out.call_args.args[0]
print('PASS: expanded help-only catalogue, input validation, cancellation, offline files and bounded network commands')
