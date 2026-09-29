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
| OpenAI | [ChatGPT Desktop Linux preview](https://learn.chatgpt.com/docs/linux/linux-app) 26.924.51851, official ARM64 Debian package and signed OpenAI repository. |
| Markdown | [Typora](https://typora.io/releases/stable) 1.13.6-1 official ARM64 `.deb` (`sha256:dff792f71002efe579e60ae11cf2d4ffdf8979f917808c8a944877bd192a654a`); [Obsidian](https://obsidian.md/download) 1.13.7 official ARM64 AppImage in `~/.local/opt/obsidian-1.13.7/` (`sha256:e286fd2bb2a5d346a35a577bd764c73fd5537dddec2b99a1a3e5e35974085203`, matching the upstream release digest). |
| Waydroid / Android | [ConvertAll](https://convertall.bellz.org/download.html) 1.0.3 official APK (`sha256:edcad0375eeb31631f51f8ec8af75c2f5e674044097b04b954c617cfaade9f11`, matching upstream), package `org.bellz.convertall`. |

MQTTX and CyberChef have user desktop launchers. CyberChef opens its local
HTML in Chromium; it does not need a hosted service. MQTTX's AppImage needs
the unversioned `libz.so` symlink supplied by `zlib1g-dev` on this phone.
Typora was installed from a local official `.deb`, Obsidian from an AppImage,
and ConvertAll from an APK; no repository was added for those three, so their
versions need a deliberate update rather than an APT upgrade.

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
- ConvertAll's Waydroid package installed, its Plasma launcher is visible and
  a cold launch started Android and its app process. The actual conversion UI
  was not visually checked. Native APT ConvertAll 0.8.0 was rejected because
  its PyQt5 dependency conflicts with the held Qt5 GLES stack; no Qt packages changed.
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
