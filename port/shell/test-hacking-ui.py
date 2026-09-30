#!/usr/bin/env python3
"""Headless TUI checks; actions are mocked, never touch a target."""
import asyncio
from contextlib import nullcontext
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from eqs_hacking_ui import ToolboxApp, ToolHelp
from textual.app import SuspendNotSupported
from textual.widgets import Button, Input, OptionList, Select

loader = importlib.machinery.SourceFileLoader('eqs_hacking', str(Path(__file__).with_name('eqs-hacking')))
spec = importlib.util.spec_from_loader(loader.name, loader)
menu = importlib.util.module_from_spec(spec)
loader.exec_module(menu)


async def checks():
    with patch.object(menu, 'action') as execute:
        app = ToolboxApp(menu.TOOLS, menu.GUIDES, menu.action)
        async with app.run_test(size=(140, 38)) as pilot:
            await pilot.pause()
            assert app.native_ansi_color, 'Colors must be terminal palette slots, not RGB'
            assert app.theme == 'ansi-dark', 'Use Ghostty colors rather than a separate application theme'
            listing = app.query_one('#tools', OptionList)
            assert listing.option_count == len(menu.TOOLS)
            assert app.selected == 'network'
            await pilot.press('ctrl+f')
            app.query_one('#search', Input).value = 'pcap'
            await pilot.pause()
            assert 0 < listing.option_count < len(menu.TOOLS)
            assert app.selected == 'pcap-info'
            await pilot.press('enter', 'enter')
            await pilot.pause()
            assert isinstance(app.screen, ToolHelp)
            execute.assert_not_called()  # Enter reads details, not a scan.
            await pilot.press('escape')
            app.query_one('#search', Input).value = 'no-such-tool-xyz'
            await pilot.pause()
            assert listing.option_count == 0 and app.selected is None
            assert app.query_one('#run', Button).disabled
            assert app.query_one('#empty').display
            await pilot.press('ctrl+r')
            execute.assert_not_called()
            await pilot.press('escape')
            await pilot.pause()
            assert listing.option_count == len(menu.TOOLS)
            app.query_one('#search', Input).value = 'subred'
            await pilot.pause()
            assert app.selected == 'subnet'
            with patch.object(app, 'suspend', return_value=nullcontext()), patch('builtins.input', return_value=''):
                await pilot.click('#run')
                await pilot.pause()
            execute.assert_called_once_with('subnet')
            assert app.selected == 'subnet'
            for failure in (KeyboardInterrupt(), EOFError(), ValueError('Prueba de entrada inválida'), OSError('Prueba de comando ausente')):
                execute.reset_mock()
                execute.side_effect = failure
                with patch.object(app, 'suspend', return_value=nullcontext()), patch('builtins.input', return_value=''):
                    await pilot.press('ctrl+r')
                    await pilot.pause()
                execute.assert_called_once_with('subnet')
                assert app.selected == 'subnet'
            execute.reset_mock()
            with patch.object(app, 'suspend', side_effect=SuspendNotSupported):
                await pilot.press('ctrl+r')
                await pilot.pause()
            execute.assert_not_called()

    for size in ((100, 28), (80, 24), (56, 20)):
        with patch.object(menu, 'action') as execute:
            app = ToolboxApp(menu.TOOLS, menu.GUIDES, menu.action)
            async with app.run_test(size=size) as pilot:
                await pilot.pause()
                assert app.query_one('#tools').size.height >= 3, size
                for selector in ('#search', '#run', '#help'):
                    region = app.query_one(selector).region
                    assert region.width > 0 and region.bottom <= size[1], (size, selector, region)
                if size[0] < 110:
                    app.query_one('#category', Select).value = 'USB'
                    await pilot.pause()
                    assert app.selected == 'usb'
                    assert app.query_one('#tools', OptionList).option_count == 1
                await pilot.click('#help')
                await pilot.pause()
                assert isinstance(app.screen, ToolHelp)
                await pilot.resize_terminal(140, 38)
                await pilot.pause()
                await pilot.press('escape')
                assert app.query_one('#categories').display
                execute.assert_not_called()

    with patch('eqs_hacking_ui.shutil.which', return_value=None), patch.object(menu, 'action') as execute:
        app = ToolboxApp(menu.TOOLS, menu.GUIDES, menu.action)
        async with app.run_test() as pilot:
            app.query_one('#search', Input).value = 'GNU Units'
            await pilot.pause()
            assert app.selected == 'units-help'
            assert app.query_one('#run', Button).disabled
            await pilot.press('ctrl+r')
            execute.assert_not_called()

    # Reuse the frontend for field toolboxes without changing hacking defaults.
    tools = {'calc': ('Circuitos', 'Ohm', 'Sólo cálculo offline.'),
             'app': ('Aplicaciones', 'App ausente', 'No instalar automáticamente.')}
    with patch.object(menu, 'action') as execute:
        app = ToolboxApp(tools, {}, execute, title='EQS Electrónica',
                         boundary='Sin conexiones ni escrituras en equipos.',
                         modes={'calc': ('OFFLINE', 'green'), 'app': ('APP', 'green')},
                         available=lambda key: key != 'app')
        async with app.run_test(size=(100, 28)) as pilot:
            await pilot.pause()
            assert app.title == 'EQS Electrónica'
            assert str(app.query_one('#brand').render()).find('EQS Electrónica') >= 0
            assert app.entry_mode('calc') == ('OFFLINE', 'green')
            app.query_one('#search', Input).value = 'ausente'
            await pilot.pause()
            assert app.selected == 'app' and app.query_one('#run', Button).disabled
            await pilot.press('ctrl+r', 'f1')
            await pilot.pause()
            assert isinstance(app.screen, ToolHelp)
            execute.assert_not_called()


asyncio.run(checks())
print('PASS: Textual browsing/search, empty/missing states, compact layouts, explicit execution and terminal handoff')
