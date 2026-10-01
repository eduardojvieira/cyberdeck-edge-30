# EQS field toolbox (live phone, 2026-09-29)

This is **installed on Eduardo's test phone**, not baked into either rootfs
recipe. It did not change H29, Wayfire, Plasma or the 258 held port packages.
No firmware flash or reboot was performed. The applications below are tools
for manual work, **not** validated interfaces to an industrial installation.

## Installed

| Source | Tools |
|---|---|
| Droidian/Debian APT | `qalculate-qt`, `qalc`, `mosquitto-clients`, `tio`, `python3-pymodbus`, `visidata`, `miller`, `lnav`, `hurl`, `jid`, `jq`, `xournalpp`, `converseen`, `krename`, `libimage-exiftool-perl`, `filelight`, `kid3`, `ffmpeg`, `mediainfo`, `zint`, `zint-qt`, `kcharselect`, `iperf3`, `nmap`, `qpdf`, `srecord`, `dfu-util`, `pandoc`, `smartmontools`, `socat`, `pulseview`, `sigrok-cli`, `ipcalc`, `mtr-tiny`, `tshark`, `arp-scan`, `zbar-tools`, `ngspice`, `f3` |
| Flathub ARM64 | [Dev Toolbox](https://flathub.org/apps/me.iepure.devtoolbox) 1.3.1, [PDF Arranger](https://flathub.org/apps/com.github.jeromerobert.pdfarranger) 1.14.0, [Okteta](https://flathub.org/apps/org.kde.okteta) 0.26.27, [Meld](https://flathub.org/apps/org.gnome.meld) 3.24.0, [LabPlot](https://flathub.org/apps/org.kde.labplot) 2.12.1 and [DB Browser for SQLite](https://flathub.org/apps/org.sqlitebrowser.sqlitebrowser) 3.13.1 |
| ARM64 Homebrew | `jd` 2.5.0, `websocat` 1.14.1 |
| Official upstream | [MQTTX](https://github.com/emqx/MQTTX/releases/tag/v1.13.0) 1.13.0 ARM64 AppImage in `~/.local/opt/mqttx/` (`sha256:71591bfd99fe91dc440234b3b8f1aaedd3995ae5613ac32c84ee20679e8a3a53`); [CyberChef](https://github.com/gchq/CyberChef/releases/tag/v10.24.0) 10.24.0 offline in `~/.local/opt/cyberchef-10.24.0/` (release ZIP `sha256:29947b4d7805b74135c8370f3cba19b609d63e8ece6e33b2cb8ee0dfbbf1393c`) |
| OpenAI | [ChatGPT Desktop Linux preview](https://learn.chatgpt.com/docs/linux/linux-app) 26.928.20755 (updated September 29), official ARM64 Debian package and signed OpenAI repository. |
| Markdown | [Typora](https://typora.io/releases/stable) 1.13.6-1 official ARM64 `.deb` (`sha256:dff792f71002efe579e60ae11cf2d4ffdf8979f917808c8a944877bd192a654a`); [Obsidian](https://obsidian.md/download) 1.13.7 official ARM64 AppImage in `~/.local/opt/obsidian-1.13.7/` (`sha256:e286fd2bb2a5d346a35a577bd764c73fd5537dddec2b99a1a3e5e35974085203`, matching the upstream release digest). |
| Native Linux units | ConvertAll **0.8.0-3**, pure-Python Debian package extracted into `~/.local/opt/convertall-0.8.0/`, using the existing science environment's isolated PyQt5. No system Qt replacement. |
| MQTT Explorer | [Official ARM64 release](https://github.com/thomasnordquist/MQTT-Explorer/releases/tag/v0.4.0-beta.6) **0.4.0-beta.6** (`mqtt-explorer` package `0.4.0~beta.6`); this is a **prerelease**, not a new stable release. The `.deb` matched upstream's SHA-512 metadata. |

MQTTX and CyberChef have user desktop launchers. CyberChef opens its local
HTML in Chromium; it does not need a hosted service. MQTTX's AppImage needs
the unversioned `libz.so` symlink supplied by `zlib1g-dev` on this phone.
Typora and MQTT Explorer were installed from local official `.deb` files,
Obsidian from an AppImage, and ConvertAll from an extracted Debian package.
No update repository was added for them: future versions need a deliberate
update; APT does not manage the extracted ConvertAll copy.

The live phone also has a **Homelab Dashboard** launcher using Chromium's
`--app=<URL>` mode. Its private URL and personal launcher are not exported to Git
or the image recipe.

## Checks and limits

- The APT plan was simulated with `--no-remove --no-upgrade` before install.
  It completed without removals or changes to held packages. `dpkg --audit`
  is empty and the hold count is still 258. `smartmontools.service` and
  `iperf3.service` are disabled/inactive; no background server was requested.
- `qalc`, `jd`, `websocat`, `hurl` and PyModbus passed command/import smoke
  checks. Dev Toolbox, PDF Arranger, Qalculate Qt and MQTTX survived short
  launch checks; **touch usability and workflows have not been validated**.
- Dev Toolbox 1.3.1 prints a nonfatal `AttributeError` in its
  JSON/YAML/TOML view on startup. Treat that conversion feature as unverified.
- CyberChef's page title loaded in headless Chromium. Recipes, clipboard and
  GUI use are still unverified.
- ChatGPT Desktop remained running for a 15-second Wayfire/XWayland launch and
  reported a visible renderer. Account sign-in and full GUI use remain untested.
  Droidian is not among OpenAI's formally supported desktop distributions.
- Typora and Obsidian survived short launches; their launchers are visible in
  Plasma. Typora's local launcher uses `--disable-gpu` after Electron GPU
  initialization errors; Obsidian started without `--no-sandbox`. Editing,
  touch usability, sync and Typora license activation were **not** tested.
- **ConvertAll is now native Linux**, at Eduardo's request. Its command line
  passed `1 m → 100 cm`, `1 bar → 14.503774 psi` and `0 °C → 32 °F`;
  its GUI ran for 15 seconds without startup errors. Only three resource paths
  in the extracted Python package were adapted. The current Flutter/Android
  1.0.3 is **not** the version used by this native integration. Native APT
  dependency resolution would replace the held Qt5 GLES stack; the existing
  science PyQt5 runtime avoids that, without another environment. The old
  Android package `org.bellz.convertall` and its launcher were removed;
  Waydroid was returned to its previous stopped-session state.
- MQTT Explorer survived a 15-second software-rendered XWayland launch and has
  a visible Plasma launcher. Its wrapper does **not** disable the sandbox.
  No broker connection, subscription, publication or industrial interaction
  was tested. It ships example public-broker profiles: choose your own broker
  deliberately; do not publish machine commands just to test the UI.
- [LocalSend](https://github.com/localsend/localsend/releases/tag/v1.18.2)
  was **not retained**: its Flatpak exits with an EGL platform error on this
  Wayfire/HWC setup; the official ARM64 binary stays up but repeatedly reports
  Flutter compositor/GL-context errors. Do not list it as working.
- Sid candidates for `okteta`, `sqlitebrowser`, `labplot` and `meld` were
  rejected by the resolver under the held Qt/GLib cohort. Their isolated
  Flatpaks survived short launch checks, but touch/file workflows remain
  unverified. [Exact blockers and upgrade path](../apt/README.md#application-abi-blockers-2026-09-29).
- `pulseview`, `sigrok-cli`, `srecord`, `dfu-util`, `arp-scan` and `tshark`
  have **not** been tested against attached hardware or production networks.
  Device writes and network scans require a separate, explicit task.

Before using this as a reproducible image feature, select the validated
subset, pin the inputs, and add it to the rootfs recipe. Installing on the
running phone alone does not change the image.

## Scratch and ready-to-run C (September 29)

- **Scratch (web oficial)** opens the [official editor](https://scratch.mit.edu/projects/editor/)
  as a Chromium app; it requires Internet access. Scratch's current
  [official downloads](https://scratchfoundation.org/tools) do not list Linux.
- **TurboWarp (Scratch offline)** is the maintained, compatible editor, **not
  the official Scratch app**. Installed ARM64 **1.16.0** from its
  [signed APT repository](https://desktop.turbowarp.org/#linux). Signing-key
  fingerprint: `168EE1EBE4023F875F35A5797E0FEA84B8AFB1D6`; release package
  SHA-256: `79c638eef985e95cd4cde1ce46932406b15933fe1870f4395d0bc79b3e7f5249`.
  Future updates use APT. The old Flathub Scratch 3.10.1 wrapper was not installed.
- **Geany 2.1-2** uses the existing native **GCC 16.2.0**, Make and GDB.
  Open `~/Documents/C/hola.c` or save a new `.c` file. **F5 compiles and runs**;
  F8 checks/compiles an object; F9 builds an executable. Flags: C17,
  `-Wall -Wextra -Wpedantic -g`, linked with `-lm`. Geany saves a modified file
  before the action. Programs run interactively in the existing Ghostty wrapper,
  and the run terminal stays open until Enter. This default is for **one C file**;
  multi-file projects need their own Make/CMake configuration.

Reinstall the user integration **on the Edge**, after installing `geany` and
`turbowarp-desktop` with a reviewed APT transaction:

```sh
# Back up existing Geany settings before replacing them.
mkdir -p ~/.config/geany/filedefs ~/.local/share/applications ~/Documents/C
install -m644 port/shell/geany.conf ~/.config/geany/geany.conf
install -m644 port/shell/geany-filetypes.c ~/.config/geany/filedefs/filetypes.c
test -e ~/Documents/C/hola.c || install -m644 port/shell/hola.c ~/Documents/C/hola.c
install -m644 port/shell/scratch-web.desktop port/shell/turbowarp-desktop.desktop \
  ~/.local/share/applications/
```

TurboWarp's default launch reported WebGL blocked. Its local desktop override
selects Mesa software rendering and XWayland, with `--ignore-gpu-blocklist`,
**only for TurboWarp**; it does not disable the sandbox or change Plasma's GPU
configuration. The adapted process ran for 20 seconds without those WebGL
errors. Geany started for 12 seconds and exited cleanly when the timed test
ended. Compile/build/run checks passed on host and ARM64, including paths with
spaces, interactive input and rejection of invalid input. A separate Ghostty
run executed the configured C command. The Scratch URL returned HTTP 200.
**Touch interaction, creating/saving Scratch projects and TurboWarp sprite
rendering remain owner checks**; these short launches do not prove those workflows.

## EQS Hacking Toolbox

Open **EQS Hacking Toolbox** from Plasma. The new interface uses
[Textual 8.2.8](https://textual.textualize.io/) instead of nested fzf menus,
with an OpenCode-inspired workspace: categories, search, a tool list and
contextual help. **Colors come from Ghostty's ANSI palette and default
foreground/background**, not a separate RGB theme. Changing the terminal
palette also changes the toolbox; the app does not edit Ghostty's configuration.

| Control | Behavior |
|---|---|
| `Ctrl+F` | Focus search; matches names, commands and help, ignoring accents. |
| Arrows / mouse / scroll | Browse categories and tools without executing them. |
| `Enter` / `F1` / **Leer ayuda** | Read the selected entry's full help. Enter in search focuses the list. |
| `Ctrl+R` / action button | Explicitly run the guided action, open the app or show the tool's options. Existing target validation and confirmations still apply. |
| `Tab` / `Shift+Tab` | Move keyboard focus between controls. |
| `Esc` | Close help, clear search, or return to **Todo**. |
| `Ctrl+Q` / **Salir** | Close the toolbox. |

Wide terminals show three panes. Below 110 columns the category rail becomes a
selector; below 86 columns the full help moves to `Enter`/`F1`, leaving room for
the tool list. **LOCAL**, **OFFLINE**, **RED**, **CAPTURA**, **APP** and **AYUDA**
distinguish what an entry actually does. Missing guide executables are marked
and cannot run; an installed executable is not a claim of working hardware.
Empty searches disable execution. Interactive commands temporarily regain the
native terminal for prompts, output and sudo; Enter returns to the same selection.
No credentials are handled by the UI. Use the external keyboard/mouse; actual
touch usability remains an owner check.

| Category | Actions |
|---|---|
| Red | Interfaces, listeners, ARP/NDP cache, subnet math, ping, DNS, traceroute, Nmap, ARP scan, MTR, iperf3, Ncat/Netcat, DNSenum, SNMP, Masscan, Hping, socket/traffic utilities and Ndiff. |
| Web y TLS | Confirmed HTTPS HEAD; help for SSLScan, testssl.sh, SSH audit, OpenSSL/GnuTLS, SQLMap, ffuf, Gobuster and Wfuzz. |
| Capturas offline | Read/describe a PCAP with tshark/capinfos; Termshark, Editcap, Ngrep, TCPFlow and Netsniff-ng guides. |
| Wi-Fi y Bluetooth | Cached Wi-Fi and paired devices; declared `iw` capabilities, rfkill state, BlueZ tools, Aircrack-ng and Bettercap guides. |
| USB | USB tree and serial inventory without opening devices. |
| Archivos | SHA-256, bounded hex view and CyberChef offline. |
| Forense y binarios | File type, ELF header, Radare2 metadata and ExifTool; Binwalk, YARA, Sleuth Kit, Foremost, Hexedit, Strace, Ltrace and GDB guides. |
| Auditoría local | dpkg/holds and read-only firewall view; Lynis, Debsums and Lsof guides. |
| Contraseñas (laboratorio) | John, Hashcat and Hydra help; no automatic credential reads or login attempts. |
| Industrial y electrónica | MQTT Explorer and native ConvertAll; Tio, Mosquitto, Sigrok, DFU and SRecord guides, without hardware writes. |
| Utilidades | GNU Units, Qalculate, Dos2unix, ShellCheck and Hyperfine guides. `moreutils` is also installed for terminal use. |
| Ayuda | Controls, executable inventory and hardware/authorization limits. |

**91 entries across 12 categories**, combining guided actions and help/manual
entries. An entry labelled **[ayuda]** opens that program's options and explains
its use; it does **not** initiate a scan, fuzzing run, authentication test or
firmware write. Use a separate terminal for deliberately scoped advanced jobs.

Opening the menu performs **no scan or capture**. Nmap accepts a **single IP**,
requires confirmation and checks 100 TCP ports, with a 30-second host timeout;
no NSE scripts, exploits or version probes. Scans can still disrupt sensitive
industrial equipment: use only authorized targets in a suitable test window.
Capture requires confirmation and sudo, stops after **200 packets or 60 seconds**,
uses a 128-byte snap length, enforces directory 0700/file 0600 even when the
capture directory already exists, and writes a private `.pcap` under
`~/Documents/EQS-Capturas`. Captures can contain sensitive data; do not publish them.
HTTPS HEAD and traceroute also require confirmation and have explicit time/
probe limits. Offline PCAP reads disable DNS resolution and show at most 100
packets. File analysis never executes the selected executable; nevertheless,
parsing an untrusted file is not a security sandbox.
This does **not** add Sub-GHz, RFID, NFC emulation, BadUSB or validated
Wi-Fi monitor/injection support. No Kali repository or persistent listening service was added. Installing Lynis
enabled its upstream audit timer; it was explicitly disabled/stopped afterward.
Debsums remains `CRON_CHECK=never`; iperf3 and smartmontools stay inactive.

```sh
# On the Edge: review this app-only simulation before the matching install.
apt-get -s --no-remove --no-install-recommends --no-upgrade install python3-textual=8.2.8-1
sudo apt-get --no-remove --no-install-recommends --no-upgrade install python3-textual=8.2.8-1
mkdir -p ~/.local/bin ~/.local/share/applications
install -m755 port/shell/eqs-hacking ~/.local/bin/eqs-hacking
install -m644 port/shell/eqs_hacking_ui.py ~/.local/bin/eqs_hacking_ui.py
install -m644 port/shell/eqs-hacking.desktop ~/.local/share/applications/
# Host-safe checks; UI check needs Textual 8.2.8 in that Python environment.
python3 port/shell/test-hacking.py
python3 port/shell/test-hacking-ui.py
python3 port/shell/test-geany.py
```

The menu's help, input validation, cancellation and bounded scan arguments passed
on host and ARM64. All **63** native guide/local-query commands produced output
without missing executables, loader failures or fatal signals; some tools
normally return nonzero codes for help. Offline checks parsed a **synthetic**
one-frame PCAP with capinfos/tshark and `/usr/bin/true` with readelf/rabin2.
Real menu/submenu navigation and local commands were exercised on the phone.
The replacement Textual UI has headless checks on host and ARM64 for search,
keyboard/mouse browsing, explicit execution, cancellation/error return,
missing/empty states, terminal-palette mode and layouts at 140×38, 100×28,
80×24 and 56×20 cells. A real phone SSH PTY exercised search, offline subnet
calculation and return to the menu; this is not touchscreen sign-off.
The toolbox, native ConvertAll and MQTT Explorer launchers are visible to
Gio/Plasma. Touch use and actual broker workflows remain owner checks.
**No network scan, packet capture, radio attack or serial interaction was performed.**


### Package selection and repeat installation

[`hacking-packages.txt`](hacking-packages.txt) records the selected repository
packages, **not** a claim to install every security-related package in Debian.
On the live phone the expansion added **153 binary packages including
libraries**, with **zero changes to any previously installed package version**,
zero removals, the same 258 holds and `FLASH_BOOTIMAGE=no`. H29, Wayfire and
plasmashell remained running with their original PIDs. Both rootfs recipes
remain unchanged; this is not an image build or a firmware validation.

The later Textual UI installation added **seven** Python packages, with **zero
upgrades or removals** in the APT/dpkg transaction logs. The same 258 hold
selections remain. It uses the Sid `python3-textual=8.2.8-1` package and no
additional Python environment on the phone. The previous fzf script is kept
privately at `~/.cache/eqs-toolbox-before-textual/eqs-hacking`; copying it back to
`~/.local/bin/eqs-hacking` restores the previous UI without a flash.

- Wfuzz's Sid dependencies required Python 3.14, incompatible with the retained
  `python3-gbinder` requirement `<3.14`. Reviewed Droidian packages
  `python3-pycurl=7.45.6-1` and compatible `python3-legacy-cgi` solved it without
  changing Python. The pure-Python CGI package was then updated to the
  compatible Sid 2.6.4-3 candidate. PycURL warns it is not built with OpenSSL:
  **Wfuzz TLS fuzzing remains unvalidated**; do not disable certificate checks
  to bypass that warning. A later resolver may require a new review of PycURL.
- Radare2 6.1.8 did not load with `--no-install-recommends`: its executables need
  unversioned `libr_util.so`/`libr_main.so`. Installing the matching
  `libradare2-dev` and runtime packages fixed it; no private symlinks were made.
- The menu appends `/usr/sbin:/sbin` only to its tool environment, so installed
  tools also resolve from an unprivileged SSH/terminal PATH. Tool-local
  `PAGER=cat` keeps help from trapping the keyboard in a nested pager;
  GUI/user shell settings are unchanged.
- Native Wireshark GUI requires Qt 6.11 plugins, incompatible with the retained
  Qt 6.10.2. Use the installed **Termshark/tshark** instead; no Qt holds were removed.
- DNSrecon's candidate similarly requires incompatible Python extensions;
  DNSenum and Dig are available. Nikto, Kismet and Metasploit were not present
  in the configured repository indices. No Kali source was added to obtain them.
- Hashcat help works, but its OpenCL backend-information probe did not complete
  within 12 seconds. **No usable CPU/GPU backend or password-audit performance
  is claimed.** Monitor/injection, Bluetooth interception and raw packet tools
  likewise still need compatible hardware and a separate authorized test.

Before repeating an install on the Edge, preserve the port holds and review the
actual plan (repository candidates change):

```sh
packages=$(sed '/^#/d; /^$/d' port/shell/hacking-packages.txt | tr '\n' ' ')
apt-get -s --no-remove --no-install-recommends --no-upgrade install $packages
# Only after reviewing the complete plan for retained/boot changes and removals:
sudo apt-get --no-remove --no-install-recommends --no-upgrade install $packages
```

For the two additional Linux apps, install the official MQTT Explorer ARM64
`.deb` after hash verification and APT simulation, and extract the signed-index
Debian ConvertAll package rather than installing its conflicting Qt dependency:

```sh
repo=$PWD  # Run this block from the repository checkout.
mkdir -p ~/.local/state/eqs-convertall ~/.local/opt/convertall-0.8.0
cd ~/.local/state/eqs-convertall
apt-get download convertall=0.8.0-3
# Expected SHA-256: e7ee8a72eace1c87892515e59b9720109125a04ed72038910844a3f1ce2667cd
printf '%s  %s\n' e7ee8a72eace1c87892515e59b9720109125a04ed72038910844a3f1ce2667cd convertall_0.8.0-3_all.deb | sha256sum -c -
dpkg-deb -x convertall_0.8.0-3_all.deb ~/.local/opt/convertall-0.8.0
# Adapt only the three packaged resource paths, retaining the upstream code:
sed -i -e "s|'/usr/share/convertall/|'$HOME/.local/opt/convertall-0.8.0/usr/share/convertall/|g" \
  -e "s|'/usr/share/doc/convertall'|'$HOME/.local/opt/convertall-0.8.0/usr/share/doc/convertall'|g" \
  ~/.local/opt/convertall-0.8.0/usr/share/convertall/convertall.py
# Existing science PyQt5 environment required; return to the checkout:
cd "$repo"
install -m755 port/shell/convertall port/shell/mqtt-explorer ~/.local/bin/
install -m644 port/shell/convertall.desktop port/shell/mqtt-explorer.desktop \
  ~/.local/share/applications/
```

MQTT Explorer `.deb` SHA-256:
`318da7a4c9351d02e63651d28e1ba9da157c6c59aa513c655c5e1e5c7a12143d`.
Its SHA-512 also matched `latest-linux-arm64.yml` from the same official release.
That metadata check is not a separate publisher signature. Native ConvertAll's
input archive retains the APT index provenance; the resource-path adaptation
and the user launcher are not a newly built Debian package.

Research references: [Wireshark offline capture tools](https://www.wireshark.org/docs/man-pages/),
[SSH audit upstream](https://github.com/jtesta/ssh-audit), and
[Kali's warning against mixing repositories](https://www.kali.org/docs/general-use/kali-apt-sources/).

## Electronics and engineering toolboxes

Two separate Plasma launchers use the **same Textual frontend and terminal ANSI
palette** as Hacking Toolbox, not two copied interfaces. The four app additions
are documented [below](#engineering-apps-september-30). Open **EQS Electrónica**
or **EQS Ingeniería**. The controls above apply; browsing/Enter reads help,
while **Ctrl+R** or the action button explicitly executes. Calculations accept
decimal comma and scientific notation, without thousands separators.

| Toolbox | Offline calculators | Existing apps and help |
|---|---|---|
| **EQS Electrónica** — 24 entries | Ohm/power, unloaded resistor divider, LED resistor, RC time/cutoff, PWM, UINT32/INT32/FLOAT32 and four byte/word orders, RGB/HEX/RGB565, framebuffer memory. | KiCad, Fritzing, Arduino IDE, Qalculate!, native ConvertAll, Okteta, Geany; Ngspice, Sigrok, PulseView, Tio, SRecord, GCC and units help. |
| **EQS Ingeniería** — 26 entries | Linear industrial scaling, calibrated dosing/mass/error, sample repeatability, reduction/screw/counts per mm, shaft power/torque, rectangular area/volume/waste. | SMath Studio, existing Octave, Scilab, wxMaxima, Spyder, LabPlot, SQLite, Meld, MQTT Explorer and converters; Sage, scientific Python, VisiData, Miller, Gnuplot and MQTT help. |

All **14 calculators** show inputs, units, formulas and model limitations.
The scaling calculator accepts reversed endpoints, reports out-of-range values
and **does not clamp them**. `UE` means the engineering unit shared by the
entered endpoints/measurements. Dosing uses the calibration in pulses/L and
density in kg/L **that you enter**, not a hidden default. Motion uses motor
turns per output turn, screw lead in mm/output turn, and effective encoder
counts per **motor** turn (include quadrature in your calibration if applicable).
Repeatability uses sample standard deviation (`n−1`), not accuracy against a
reference; CV is undefined at zero mean. The dosing tolerance is inclusive,
with only a `1e-12` relative allowance for floating-point boundary rounding.

Nonfinite numbers, fractional integer inputs, invalid ranges and zero
denominators are rejected; blank input/Ctrl+C cancels. Numeric magnitudes are
limited to `1e100`; underflow/overflow reports an error instead of a plausible
number. Integers are parsed exactly and limited to `2^53−1`. Framebuffer
dimensions are capped at 65536 per axis and 64 buffers, without allocating
them. Its estimate aligns each row to one byte; real DMA stride/metadata can
require more memory. RGB565 is quantized color data, not a display configuration.

**These are field estimates, not instruments or safety/regulated design tools.**
Check component tolerances, sensor calibration, mechanics and real measurement
conditions. They do not design structures, size regulated installations,
diagnose NAMUR faults, implement protection or prove electrical safety.
Instrumentation entries invoke only `--help` or SRecord's version output;
they never open serial ports, scan attached hardware, acquire signals, flash
firmware or send PLC/MQTT commands. Qt help uses an offscreen display only for
that subprocess; real app launchers retain their existing graphics wrappers.
Opening an app deliberately can expose its normal edit/connect actions; this
menu is not a sandbox. Missing guide executables or app launchers are disabled,
not installed; a present launcher does not prove that its runtime works.

Install the integration **on the Edge**, with the existing Textual/tools:

```sh
mkdir -p ~/.local/bin ~/.local/share/applications
# Back up the existing eqs_hacking_ui.py before updating the shared frontend.
install -m755 port/shell/eqs-field-toolbox ~/.local/bin/
install -m644 port/shell/eqs_hacking_ui.py ~/.local/bin/
install -m644 port/shell/eqs-electronics.desktop port/shell/eqs-engineering.desktop \
  ~/.local/share/applications/
eqs-field-toolbox electronics --list
eqs-field-toolbox engineering --list
python3 port/shell/test-field-toolbox.py  # Needs the existing Textual environment.
python3 port/shell/test-hacking.py
python3 port/shell/test-hacking-ui.py
```

The shared frontend keeps the Hacking Toolbox defaults compatible. The live
installation retains its previous frontend privately in
`~/.cache/eqs-toolbox-before-field-20260930/`; restoring it and removing only
the two field launchers/backend undoes this integration without a flash.
The shared toolbox UI/backend itself needs no extra package, daemon or Python
environment; the apps added below have their own dependencies. **These are live
phone integrations, not additions to the base/current image recipes.**

### Initial verification on September 30 (before the four app additions)

- `test-field-toolbox.py`, `test-hacking.py` and `test-hacking-ui.py` passed on
  host and ARM64. Checks cover all 14 calculators, decimal comma, exact integer
  validation, reversed/out-of-range scaling, inclusive dosing tolerance,
  cancellation, missing inputs, command arguments and both profiles at 140×38,
  100×28, 80×24 and 56×20 cells. Python compilation, desktop entry validation
  and `git diff --check` also passed. Host science/Geany regression checks passed.
- All **41 distinct entries** have their guide executable or app launcher on
  the live Edge. All 14 help/version commands returned output without loader
  failure/fatal signal; `mosquitto_sub --help` normally returns status 1.
- A real phone SSH PTY exercised search → LED calculation (`5 V`, `2 V`,
  `20 mA` → `150 Ω`, `0.06 W`) → return/exit, and industrial scaling
  (`12` over `4…20` to `0…100` → `50 UE`) → return/exit. These are synthetic
  input calculations, not measurements from connected hardware.
- Both native Ghostty launchers and their Python children stayed up for
  15 seconds. Only the two temporary test sessions were closed. Plasma/Gio
  sees both new launchers; **touch usability and complete app workflows remain
  owner checks**, not inferred from headless tests or short startup checks.
- Exact inventories remained identical: **2332 installed package/version
  rows**, **258 holds**, Wayfire/plasmashell PIDs, H29 kernel and
  `FLASH_BOOTIMAGE=no`; `dpkg --audit` is empty. No package transaction,
  service installation, network probe, acquisition, serial open or flash.

Reference models: [TI's resistor-divider tool](https://www.ti.com/download/kbase/volt/volt_div3.htm),
[TI's first-order RC filter explanation](https://e2e.ti.com/blogs_/archives/b/precisionhub/posts/three-guidelines-for-designing-anti-aliasing-filters),
and the [Ngspice manual](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf)
for deliberate offline simulation. These references do not validate a physical
circuit or an industrial installation.


## Engineering apps (September 30)

Added to the live ARM64 phone and the existing field toolboxes, **not either
image recipe**. All four apps have Plasma launchers.
[SMath Studio 1.5.0.9678 and its private Cairo runtime](SCIENCE.md#smath-studio-30-de-septiembre)
are documented separately.

| App | Installed version / source | Compatibility choice |
|---|---|---|
| KiCad | **10.0.6**, Flathub `org.kicad.KiCad/aarch64/stable` | Isolated Python/GTK runtime and app-only software rendering. Native Sid requires Python 3.14, conflicting with the retained Waydroid bridge. Symbols, footprints, templates and 3D libraries are installed. |
| Fritzing | **1.0.1-1+b4**, Droidian/Debian ARM64 | Matches the retained Qt5 5.15.15 cohort; newer Sid package requires incompatible Qt. Native XWayland wrapper, no system Qt replacement. |
| Arduino IDE | **1.8.19** (`2:1.8.19+dfsg1-5`), Debian ARM64 | Classic IDE with AVR core 1.8.7 and GCC AVR 16.2.0. Upstream IDE 2.3.10 publishes Linux x86-64, not ARM64. Other board cores are not installed. |

Reinstall **on the Edge**, after simulating and reviewing each transaction:

```sh
set -e
sudo apt-get --no-remove --no-upgrade --no-install-recommends install arduino
sudo apt-get --no-remove --no-upgrade --no-install-recommends install \
  fritzing=1.0.1-1+b4 fritzing-data=1.0.1-1 \
  libqt5serialport5=5.15.15-2 libqt5sql5t64=5.15.15+dfsg-6 \
  libqt5xml5t64=5.15.15+dfsg-6 libqt5sql5-sqlite=5.15.15+dfsg-6
sudo flatpak install --system flathub org.kicad.KiCad
mkdir -p ~/.local/bin ~/.local/share/applications
install -m755 port/shell/kicad port/shell/fritzing ~/.local/bin/
install -m644 port/shell/org.kicad.KiCad.desktop port/shell/fritzing.desktop \
  ~/.local/share/applications/
python3 port/shell/test-engineering-apps.py
```

KiCad's wrapper deliberately calls `/usr/bin/flatpak.real`: Droidian's
`flatpak-hybris` wrapper splits quoted arguments and injects Android GL paths.
This override is **KiCad-only**; it does not change other Flatpaks or the phone's
GPU configuration. Fritzing's wrapper removes inherited Qt plugin/theme paths
for its native Qt5 runtime. Neither wrapper disables a sandbox.

Verification: KiCad's first-run configuration window stayed up for 15 seconds;
its CLI exported the bundled ECC83 schematic to SVG. Fritzing opened a blank
sketch and exported the bundled RGB LED example to breadboard/schematic/PCB SVG.
Arduino opened and **compiled an empty Uno sketch** (442 bytes flash, 9 bytes
RAM), without a connected board. KiCad's setup wizard remains for the owner.
Full touch/editing/3D workflows and actual board uploads have **not** been tested.
An export or successful compile is not electrical or physical validation.

Sources: [KiCad Linux](https://www.kicad.org/download/linux-distros/),
[KiCad Flathub manifest](https://github.com/flathub/org.kicad.KiCad),
[Debian Fritzing](https://packages.debian.org/trixie/fritzing),
[Debian Arduino](https://packages.debian.org/sid/arduino), and
[Arduino IDE 2 release assets](https://github.com/arduino/arduino-ide/releases/tag/2.3.10).


After all four additions: **45 unique toolbox entries** (24 electronics,
26 engineering; shared entries overlap). Exact before/after inventories show
**49 new APT packages**, no removals or changes to any of the original 2332
package/version rows, identical H29 and all 258 holds, and empty `dpkg --audit`.
Wayfire/plasmashell were not restarted. The two unused Brew experiment formulas
were removed; existing Brew versions stayed identical. No flash, serial port
open, board upload or industrial command was performed.

The focused host/ARM64 checks are `test-engineering-apps.py` (mocked argv,
spaces and app-scoped environments) and `test-field-toolbox.py` (offline
calculators and both Textual profiles); these are distinct from the short
real GUI/export/compiler checks above. Removing an app needs a reviewed
package transaction, not unholding mobile dependencies or a broad autoremove.

## Worksheets, diagrams and notes (October 1)

Six Plasma launcher entries are installed on the live Edge, **not either image
recipe**. Search for their names in the launcher; no phone reboot is needed.

| Launcher | Installed route | First use / limits |
|---|---|---|
| EngineeringPaper (web) | [Official application](https://engineeringpaper.xyz/) in Chromium app mode | Engineering worksheets, equations and units. Internet at startup; export important work to a file. |
| Calcpad (web) | [Official online IDE](https://calcpad.eu/Ide) in Chromium app mode | Engineering calculation documents. The official desktop app requires Windows x64; no Wine or emulation installed. |
| Excalidraw (web) | [Official whiteboard](https://excalidraw.com/) in Chromium app mode | Diagrams and sketches; export `.excalidraw` files. Upstream supports offline PWA use, but offline installation/cache has **not** been validated here. |
| AFFiNE (web) | [Official web app](https://app.affine.pro/) in Chromium app mode | Notes and whiteboards. Current [v0.27.4 Linux release](https://github.com/toeverything/AFFiNE/releases/tag/v0.27.4) is x64 only, not ARM64. |
| AppFlowy (web) | [Official web app](https://appflowy.com/app/) in Chromium app mode | Notes and projects. Current [0.14.6 Linux release](https://github.com/AppFlowy-IO/AppFlowy/releases/tag/0.14.6) and Flathub build are x86-64 only. |
| SiYuan | [Official **3.8.6 ARM64 Debian package**](https://github.com/siyuan-note/siyuan/releases/tag/v3.8.6) | Native local notes. Choose a workspace folder at first launch. Tested Spanish UI and local kernel; no account or cloud sync configured. |

The five web entries are **browser launchers, not native packages or an offline
PWA installation**. They use the existing Chromium profile and website storage;
their online code updates independently of APT. Internet, accounts and cloud
sync depend on each service. No account, payment, sync or self-hosted server was
configured. Browser storage is not a backup; export important work.

### Reinstall on the Edge

Download the pinned upstream SiYuan package and verify its SHA-256 before APT:

```sh
set -e
curl --fail --location --output /tmp/siyuan-3.8.6-linux-arm64.deb \
  https://github.com/siyuan-note/siyuan/releases/download/v3.8.6/siyuan-3.8.6-linux-arm64.deb
echo '44a7e3eda29e16fc7e9bae452d32b6ded9db40d024504bb139ae6317c7680544  /tmp/siyuan-3.8.6-linux-arm64.deb' | sha256sum -c -
sudo apt-get -s --no-remove --no-upgrade --no-install-recommends \
  install /tmp/siyuan-3.8.6-linux-arm64.deb
```

**Review the simulation before proceeding.** On October 1 it proposed exactly
one new package, no upgrades or removals. Stop if another transaction changes
the retained mobile stack; do not unhold dependencies or run autoremove.

```sh
set -e
sudo apt-get --no-remove --no-upgrade --no-install-recommends \
  install /tmp/siyuan-3.8.6-linux-arm64.deb
mkdir -p ~/.local/bin ~/.local/share/applications
install -m755 port/shell/siyuan ~/.local/bin/
install -m644 port/shell/siyuan.desktop port/shell/engineeringpaper.desktop \
  port/shell/calcpad.desktop port/shell/excalidraw.desktop \
  port/shell/affine-web.desktop port/shell/appflowy-web.desktop \
  ~/.local/share/applications/
update-desktop-database ~/.local/share/applications
kbuildsycoca6 --noincremental
python3 port/shell/test-engineering-apps.py
```

SiYuan's wrapper selects XWayland and software rendering **for this app only**,
preserving quoted arguments and adding no `--no-sandbox` flag. Its default
`system.networkServe=false` binds its kernel/proxy to localhost, confirmed
from [upstream](https://github.com/siyuan-note/siyuan/blob/v3.8.6/kernel/server/serve.go)
and the live test. Enabling network serving later is a separate security choice.
The wrapper does not alter upstream Electron security settings.

### Verification and remaining owner checks

- Host and ARM64 launcher checks passed: five exact official URLs, quoted argv
  and app-scoped SiYuan flags. Desktop entry validation and KDE/Gio discovery
  passed for all six entries. The field-toolbox regression passed on ARM64 and
  on the host using isolated Textual 8.2.8. Plain host Python lacks Textual; use
  `uv run --no-project --with textual==8.2.8 python port/shell/test-field-toolbox.py`
  without changing the system Python environment.
- Each web application opened a real **1200×540** test window with its expected
  page title and stayed up for **14 seconds**. Tests used separate browser
  profiles, not personal accounts. The SiYuan wrapper opened a Spanish onboarding
  workspace for **16 seconds** with localhost-only listeners; an earlier kernel
  startup check ran for 20 seconds. Only temporary test processes were closed.
- Exact inventory comparison: all **2381 prior APT package/version rows**
  unchanged; only `siyuan=3.8.6` added. **258 holds**, H29 and Wayfire/plasmashell
  PIDs unchanged; `dpkg --audit` empty. No flash, reboot or platform upgrade.
- These checks prove short startup, **not full editing, touch usability,
  offline operation, saved-file round trips or cloud sync**. Validate those
  workflows with disposable content before using important project data.
