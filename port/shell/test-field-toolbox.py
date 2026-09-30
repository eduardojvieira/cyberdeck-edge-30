#!/usr/bin/env python3
"""Offline math and headless profile checks; never connect to field hardware."""
import asyncio
from contextlib import nullcontext
import importlib.machinery
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
loader = importlib.machinery.SourceFileLoader('eqs_field', str(Path(__file__).with_name('eqs-field-toolbox')))
spec = importlib.util.spec_from_loader(loader.name, loader)
menu = importlib.util.module_from_spec(spec)
loader.exec_module(menu)


def calculation(key, answers):
    with patch('builtins.input', side_effect=answers), patch.object(menu.subprocess, 'run') as execute:
        output = menu.calculate(key)
        execute.assert_not_called()
        assert 'Entradas:' in output and 'Modelo:' in output
        return output


def value(output, label):
    return float(next(line.split(': ', 1)[1] for line in output.splitlines() if line.startswith(label + ': ')))


cases = [
    ('ohm', ['12', '100'], {'Corriente [A]': .12, 'Potencia [W]': 1.44}),
    ('divider', ['12', '2000', '1000'], {'Vout sin carga [V]': 4, 'P R1 [W]': .032}),
    ('led', ['5', '2', '20'], {'Resistencia teórica [Ω]': 150, 'Disipación nominal [W]': .06}),
    ('rc', ['1000', '100'], {'Constante de tiempo [s]': .0001, 'Corte [Hz]': 1 / (2 * math.pi * .0001)}),
    ('pwm', ['1000', '25'], {'Período [s]': .001, 'Tiempo alto [s]': .00025, 'Tiempo bajo [s]': .00075}),
    ('framebuffer', ['320', '240', '16', '2'], {'Bytes por fila': 640, 'Bytes totales': 307200}),
    ('scaling', ['12', '4', '20', '0', '100'], {'Valor [UE]': 50}),
    ('scaling', ['12', '20', '4', '0', '100'], {'Valor [UE]': 50}),
    ('scaling', ['2', '4', '20', '0', '100'], {'Valor [UE]': -12.5}),
    ('dosing', ['1000', '1000', '1', '0,8', '1'], {'Volumen [L]': 1, 'Masa [kg]': .8, 'Error [%]': 0}),
    ('repeatability', ['1,0;2,0;3,0'], {'Media [UE]': 2, 'Desvío muestral [UE]': 1, 'CV [%]': 50}),
    ('motion', ['1200', '4', '5', '2000'], {'rpm salida': 300, 'Velocidad [mm/s]': 25, 'Cuentas/mm': 1600}),
    ('motion', ['-1200', '4', '5', '2000'], {'Velocidad [mm/s]': -25}),
    ('torque', ['1', '1500'], {'Torque ideal [N·m]': 60000 / (2 * math.pi * 1500)}),
    ('geometry', ['2', '3', '0,1', '10'], {'Superficie [m²]': 6, 'Volumen [m³]': .6, 'Volumen estimado [m³]': .66}),
]
for key, answers, expected in cases:
    output = calculation(key, answers)
    for label, expected_value in expected.items():
        assert math.isclose(value(output, label), expected_value, rel_tol=1e-9, abs_tol=1e-12), (key, output)
assert 'FUERA DE RANGO' in calculation('scaling', ['21', '4', '20', '0', '100'])
assert 'FUERA de la tolerancia' in calculation('dosing', ['1100', '1000', '1', '1', '2'])
assert 'Dentro de la tolerancia' in calculation('dosing', ['1020', '1000', '1', '1', '2'])
assert 'CV no definido' in calculation('repeatability', ['-1;1'])
assert value(calculation('framebuffer', ['1', '9', '1', '1']), 'Bytes totales') == 9
assert 'HEX RGB: #FF0000' in calculation('rgb', ['255', '0', '0'])
assert 'RGB565: 0xF800' in calculation('rgb', ['255', '0', '0'])
registers = calculation('registers', ['3F 80 00 00'])
assert 'ABCD: UINT32=1065353216; INT32=1065353216; FLOAT32=1.0' in registers
assert all(order + ':' in registers for order in ('ABCD', 'DCBA', 'CDAB', 'BADC'))
assert 'INT32=-1;' in calculation('registers', ['FFFFFFFF'])
assert 'IEEE-754 contiene NaN/Inf' in calculation('registers', ['7F800000'])

invalid = [('ohm', ['1', '0']), ('led', ['2', '3', '20']), ('pwm', ['1000', '101']),
           ('framebuffer', ['10', '10', '7', '2']), ('scaling', ['12', '4', '4', '0', '100']),
           ('dosing', ['1', '1', '0']), ('repeatability', ['1']), ('repeatability', ['1;nan']),
           ('motion', ['100', '0']), ('torque', ['1', '0']), ('registers', ['DE AD BE EF 00']),
           ('rgb', ['256']), ('rc', ['1e-300', '1e-300'])]
for key, answers in invalid:
    try:
        calculation(key, answers)
    except ValueError:
        pass
    else:
        raise AssertionError(('Invalid calculation accepted', key, answers))
for raw, bounds in [('nan', {}), ('inf', {}), ('1e101', {}), ('1' * 65, {}), ('1.000,5', {}),
                    ('1.5', {'integer': True}), ('0.999999999999999999', {'integer': True}),
                    ('1e-999', {}), ('-1', {'positive': True}), ('-1', {'low': 0})]:
    try:
        menu.number(raw, **bounds)
    except ValueError:
        pass
    else:
        raise AssertionError(('Invalid number accepted', raw))
assert menu.number('1,25e2') == 125
assert menu.number('2e3', integer=True) == 2000
try:
    calculation('ohm', [''])
except EOFError:
    pass
else:
    raise AssertionError('Blank input must cancel')

with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'XDG_DATA_HOME': directory, 'XDG_DATA_DIRS': directory}):
    p = Path(directory) / 'applications' / 'field-test.desktop'
    p.parent.mkdir()
    p.write_text('[Desktop Entry]\nType=Application\nName=Test\nExec=true\n')
    assert menu.desktop_path(p.name) == p
    assert menu.desktop_path('field-missing-test.desktop') is None
with patch.object(menu, 'available', return_value=True), patch.object(menu.subprocess, 'run') as execute:
    execute.return_value.returncode = 0
    for key, row in menu.GUIDES.items():
        menu.action(key)
        argv = execute.call_args.args[0]
        assert argv == row[3]
        assert argv[-1] in ('--help', '-VERSion'), argv  # No scan, open, connect or flash.
        assert execute.call_args.kwargs['timeout'] == 30
        assert execute.call_args.kwargs['env']['QT_QPA_PLATFORM'] == 'offscreen'
    with patch.object(menu, 'desktop_path', return_value=Path('/tmp/test app.desktop')):
        menu.action('qalculate')
        assert execute.call_args.args[0] == ['gio', 'launch', '/tmp/test app.desktop']
with patch.object(menu, 'available', return_value=False), patch.object(menu.subprocess, 'run') as execute:
    try:
        menu.action('ngspice')
    except ValueError:
        pass
    else:
        raise AssertionError('Missing tool should be rejected')
    execute.assert_not_called()
for profile, (_, keys) in menu.PROFILES.items():
    assert len(keys) == len(set(keys)) and all(k in menu.TOOLS for k in keys)
    listing = subprocess.run([sys.executable, loader.path, profile, '--list'], capture_output=True, text=True)
    assert listing.returncode == 0 and len(listing.stdout.splitlines()) == len(keys) + 1
for args, status in [(['--help'], 0), (['unknown'], 2), (['electronics'], 2)]:
    r = subprocess.run([sys.executable, loader.path, *args], capture_output=True, text=True)
    assert r.returncode == status, (args, r.stderr)


async def ui_checks():
    from eqs_hacking_ui import ToolboxApp, ToolHelp
    from textual.widgets import Button, Input, OptionList
    for profile, (title, keys) in menu.PROFILES.items():
        for size in ((140, 38), (100, 28), (80, 24), (56, 20)):
            with patch.object(menu, 'action') as execute:
                app = ToolboxApp({k: menu.TOOLS[k] for k in keys}, menu.GUIDES, execute,
                                 title=title, boundary=menu.BOUNDARY,
                                 modes={k: ('OFFLINE', 'green') if k in menu.CALCS else ('APP', 'green') if k in menu.APPS else ('AYUDA', 'cyan') for k in keys},
                                 available=lambda k: True)
                async with app.run_test(size=size) as pilot:
                    await pilot.pause()
                    assert app.title == title and app.native_ansi_color
                    assert app.query_one('#tools', OptionList).option_count == len(keys)
                    assert app.query_one('#tools').size.height >= 3
                    for selector in ('#search', '#run', '#help'):
                        region = app.query_one(selector).region
                        assert region.width > 0 and region.bottom <= size[1], (size, selector, region)
                    await pilot.press('enter')
                    assert isinstance(app.screen, ToolHelp)
                    execute.assert_not_called()
                    await pilot.press('escape', 'ctrl+f')
                    app.query_one('#search', Input).value = 'rgb' if profile == 'electronics' else 'dosificación'
                    await pilot.pause()
                    key = app.selected
                    assert key in menu.CALCS and app.entry_mode(key)[0] == 'OFFLINE'
                    with patch.object(app, 'suspend', return_value=nullcontext()), patch('builtins.input', return_value=''):
                        await pilot.click('#run')
                    execute.assert_called_once_with(key)
                    assert not app.query_one('#run', Button).disabled


asyncio.run(ui_checks())
print('PASS: 14 offline calculators, decimal comma, boundaries/cancellation, help-only commands, app argv and both TUI profiles')
