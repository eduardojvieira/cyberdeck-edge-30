"""Textual frontend; browsing never calls the toolbox action backend."""
import os
import shlex
import shutil
import subprocess
import unicodedata

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult, SuspendNotSupported
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Input, OptionList, Select, Static
from textual.widgets.option_list import Option


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


def mode(key, guides):
    if key in guides and key not in ('radio-info', 'rfkill-info'):
        return 'AYUDA', 'cyan'
    if key in ('ping', 'dns', 'route', 'ports', 'http'):
        return 'RED', 'yellow'
    if key == 'capture':
        return 'CAPTURA', 'yellow'
    if key in ('cyberchef', 'mqtt-explorer', 'convertall'):
        return 'APP', 'green'
    if key in ('hash', 'hex', 'subnet', 'pcap-info', 'pcap-read', 'filetype', 'elf', 'binary-info', 'metadata'):
        return 'OFFLINE', 'green'
    return 'LOCAL', 'green'


class ToolHelp(ModalScreen):
    BINDINGS = [('escape', 'dismiss', 'Volver')]

    def __init__(self, title, description, command):
        super().__init__()
        self.title_text, self.description, self.command = title, description, command

    def compose(self) -> ComposeResult:
        with Vertical(id='help-dialog'):
            yield Static(Text(self.title_text, style='bold'), id='help-title')
            with VerticalScroll():
                yield Static(self.description, markup=False)
                if self.command:
                    yield Static(Text('\n$ ' + self.command, style='cyan'))
            yield Button('Volver · Esc', id='close-help')

    @on(Button.Pressed, '#close-help')
    def close_help(self):
        self.dismiss()


class ToolboxApp(App):
    TITLE = 'EQS Hacking Toolbox'
    ENABLE_COMMAND_PALETTE = False
    AUTO_FOCUS = '#tools'
    BINDINGS = [
        Binding('ctrl+f', 'search', 'Buscar'),
        Binding('f1', 'help', 'Ayuda'),
        Binding('ctrl+r', 'execute', 'Ejecutar'),
        Binding('escape', 'back', 'Volver'),
        Binding('ctrl+q', 'quit', 'Salir'),
    ]
    CSS = """
    Screen { background: ansi_default; color: ansi_default; }
    #masthead { height: 2; padding: 0 1; background: ansi_default; }
    #brand { width: 1fr; color: ansi_green; text-style: bold; }
    #count { width: auto; color: ansi_default; }
    #search { margin: 0 1; border: tall ansi_bright_black; background: ansi_default; }
    #search:focus { border: tall ansi_green; }
    Input > .input--placeholder { color: ansi_default; }
    #category { display: none; margin: 0 1; }
    #workspace { height: 1fr; padding: 0 1; }
    #categories { width: 27; border: none; padding: 0 1 0 0; }
    #list-pane { width: 2fr; min-width: 25; }
    #tools { height: 1fr; border: round ansi_bright_black; background: ansi_default; padding: 0 1; }
    #tools { border-title-color: ansi_default; border-title-background: ansi_default; }
    OptionList > .option-list--option-highlighted { background: ansi_bright_black; color: ansi_default; text-style: bold; }
    OptionList:focus > .option-list--option-highlighted { background: ansi_green; color: ansi_black; }
    OptionList > .option-list--option-hover { text-style: underline; }
    #empty { display: none; height: auto; padding: 1; color: ansi_yellow; }
    #detail { width: 2fr; padding: 0 2; }
    #detail-title { height: auto; color: ansi_default; text-style: bold; margin-bottom: 1; }
    #detail-mode { height: auto; margin-bottom: 1; }
    #description { height: auto; margin-bottom: 1; }
    #command { height: auto; color: ansi_cyan; margin-bottom: 1; }
    #boundary { height: auto; color: ansi_default; }
    #selection { height: 1; padding: 0 2; color: ansi_default; }
    #actions { height: 3; padding: 0 1; }
    Button { margin-right: 1; min-width: 12; border: none; background: ansi_default; color: ansi_default; }
    Button:focus { text-style: bold; border: tall ansi_cyan; }
    Button:hover { text-style: reverse; }
    #run { background: ansi_default; color: ansi_green; text-style: bold reverse; }
    #run:disabled { background: ansi_default; color: ansi_default; }
    Footer { background: ansi_default; color: ansi_default; }
    FooterKey > .footer-key--key { background: ansi_default; color: ansi_green; }
    .compact #categories { display: none; }
    .compact #category { display: block; }
    .narrow #detail { display: none; }
    .narrow #list-pane { width: 1fr; }
    .short #masthead { height: 1; }
    ToolHelp { align: center middle; background: ansi_default; }
    #help-dialog { width: 85%; max-width: 85; height: 85%; border: round ansi_cyan; background: ansi_default; padding: 1 2; }
    #help-title { height: auto; color: ansi_green; margin-bottom: 1; }
    #help-dialog VerticalScroll { height: 1fr; margin-bottom: 1; }
    #close-help { width: 1fr; }
    """

    def __init__(self, tools, guides, execute, *, title=None,
                 boundary='Sólo equipos propios o con permiso.\nNavegar no ejecuta herramientas.',
                 modes=None, available=None):
        super().__init__()
        self.theme = 'ansi-dark'
        self.title = title or self.TITLE
        self.brand = title or 'EQS / TOOLBOX'
        self.boundary, self.entry_modes, self.check_available = boundary, modes or {}, available
        self.tools, self.guides, self.execute = tools, guides, execute
        self.categories = ['Todo'] + list(dict.fromkeys(row[0] for row in tools.values()))
        self.category = 'Todo'
        self.selected = None

    def compose(self) -> ComposeResult:
        with Horizontal(id='masthead'):
            yield Static(self.brand, id='brand')
            yield Static(f'{len(self.tools)} entradas · {len(self.categories) - 1} categorías', id='count')
        yield Input(placeholder='Buscar herramienta, tarea o comando…', id='search')
        yield Select([(name, name) for name in self.categories], value='Todo', allow_blank=False, id='category')
        with Horizontal(id='workspace'):
            yield OptionList(*[
                Option(Text(name.replace(' (laboratorio)', ' (lab.)')), id=name)
                for name in self.categories
            ], id='categories')
            with Vertical(id='list-pane'):
                yield OptionList(id='tools')
                yield Static('Sin coincidencias. Cambiá la búsqueda o presioná Esc.', id='empty')
            with VerticalScroll(id='detail'):
                yield Static(id='detail-title')
                yield Static(id='detail-mode')
                yield Static(id='description', markup=False)
                yield Static(id='command', markup=False)
                yield Static(self.boundary, id='boundary', markup=False)
        yield Static(id='selection', markup=False)
        with Horizontal(id='actions'):
            yield Button('Ejecutar', id='run', disabled=True)
            yield Button('Leer ayuda', id='help', disabled=True)
            yield Button('Salir', id='exit')
        yield Footer()

    def on_mount(self):
        self.query_one('#tools').border_title = 'Herramientas'
        self.refresh_tools()

    def on_resize(self, event):
        base = self.screen_stack[0]
        base.set_class(event.size.width < 110, 'compact')
        base.set_class(event.size.width < 86, 'narrow')
        base.set_class(event.size.height < 22, 'short')

    def available(self, key):
        if self.check_available is not None:
            return self.check_available(key)
        if key not in self.guides:
            return True  # Guided actions report missing dependencies at execution, not fabricated status.
        return shutil.which(self.guides[key][3][0], path=os.environ.get('PATH', os.defpath) + ':/usr/sbin:/sbin') is not None

    def entry_mode(self, key):
        return self.entry_modes.get(key, mode(key, self.guides))

    def refresh_tools(self):
        query = normalized(self.query_one('#search', Input).value).split()
        keys = [key for key, row in self.tools.items()
                if (self.category == 'Todo' or row[0] == self.category)
                and all(word in normalized(' '.join((key, *row))) for word in query)]
        listing = self.query_one('#tools', OptionList)
        previous = self.selected
        listing.clear_options()
        for key in keys:
            row = self.tools[key]
            tag, _ = self.entry_mode(key)
            label = Text(row[1].partition(' [')[0])
            label.append('\n' + tag + (' · no disponible' if not self.available(key) else ''))
            listing.add_option(Option(label, id=key))
        listing.highlighted = keys.index(previous) if previous in keys else (0 if keys else None)
        self.selected = keys[listing.highlighted] if keys else None
        self.query_one('#empty').display = not keys
        self.query_one('#count', Static).update(f'{len(keys)}/{len(self.tools)} entradas')
        self.show_detail()

    def show_detail(self):
        key = self.selected
        enabled = key is not None and self.available(key)
        self.query_one('#run', Button).disabled = not enabled
        self.query_one('#help', Button).disabled = key is None
        if key is None:
            for selector in ('#detail-title', '#detail-mode', '#description', '#command', '#selection'):
                self.query_one(selector, Static).update('')
            return
        category, label, description = self.tools[key]
        tag, color = self.entry_mode(key)
        self.query_one('#detail-title', Static).update(Text(label.partition(' [')[0], style='bold'))
        status = 'No disponible' if not enabled else ('Disponible' if self.check_available is not None else ('Ejecutable disponible' if key in self.guides else 'Acción guiada'))
        self.query_one('#detail-mode', Static).update(Text(f'{tag} · {status}\n{category}', style=color))
        self.query_one('#description', Static).update(description)
        self.query_one('#command', Static).update(Text('$ ' + shlex.join(self.guides[key][3]) if key in self.guides else '', style='cyan'))
        self.query_one('#selection', Static).update(f'{tag} · {label.partition(" [")[0]}')
        self.query_one('#run', Button).label = 'Ver opciones' if tag == 'AYUDA' else ('Abrir app' if tag == 'APP' else 'Ejecutar')

    @on(Input.Changed, '#search')
    def search_changed(self):
        self.refresh_tools()

    @on(Input.Submitted, '#search')
    def search_submitted(self):
        self.query_one('#tools').focus()

    @on(Select.Changed, '#category')
    def category_changed(self, event):
        if isinstance(event.value, str):
            self.category = event.value
            self.refresh_tools()

    @on(OptionList.OptionSelected, '#categories')
    def category_selected(self, event):
        self.query_one('#category', Select).value = event.option_id
        self.query_one('#tools').focus()

    @on(OptionList.OptionHighlighted, '#tools')
    def tool_highlighted(self, event):
        # A queued highlight may belong to options replaced by a search.
        listing = self.query_one('#tools', OptionList)
        if listing.highlighted is not None:
            self.selected = listing.get_option_at_index(listing.highlighted).id
            self.show_detail()

    @on(OptionList.OptionSelected, '#tools')
    def tool_selected(self):
        self.action_help()

    @on(Button.Pressed)
    def button_pressed(self, event):
        if event.button.id == 'run':
            self.action_execute()
        elif event.button.id == 'help':
            self.action_help()
        elif event.button.id == 'exit':
            self.exit()

    def action_search(self):
        self.query_one('#search').focus()

    def action_back(self):
        search = self.query_one('#search', Input)
        if search.value:
            search.value = ''
        elif self.category != 'Todo':
            self.query_one('#category', Select).value = 'Todo'
        else:
            self.query_one('#tools').focus()

    def action_help(self):
        if self.selected:
            _, title, description = self.tools[self.selected]
            command = shlex.join(self.guides[self.selected][3]) if self.selected in self.guides else ''
            self.push_screen(ToolHelp(title, description, command))

    def action_execute(self):
        key = self.selected
        if key is None or not self.available(key):
            return
        # Native terminal owns input/sudo while suspended; no credential capture or shell interpolation.
        try:
            with self.suspend():
                console = Console()
                console.print(Panel(Text(self.tools[key][2]), title=Text(self.tools[key][1]), border_style='green'))
                try:
                    self.execute(key)
                except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                    console.print(Text('No se completó: ' + str(error), style='yellow'))
                except (KeyboardInterrupt, EOFError):
                    console.print('Cancelado. No se vuelve a ejecutar automáticamente.')
                try:
                    input('\nEnter para volver al toolbox… ')
                except (KeyboardInterrupt, EOFError):
                    pass
        except SuspendNotSupported:
            self.notify('Esta terminal no permite ejecutar comandos interactivos. Abrí el toolbox en Ghostty.', severity='warning')
