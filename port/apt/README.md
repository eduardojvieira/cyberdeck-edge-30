# Sid by default, with the phone port retained

**Current phone policy:** prefer Debian Sid for ordinary packages. There is no
application allowlist. Retain the installed H29 kernel, downstream patches and
shared boot/private-ABI dependencies using native `apt-mark hold` selections.
This replaces the earlier four-application experiment at Eduardo's request.
The optional [current image cohort](../image/README.md#cohorte-actual-28-de-septiembre)
replays this policy from frozen local packages; the older preview recipe and
September 10 ZIP do not. A host build is not a physical validation.

## Updating

From this repository on the Edge:

```sh
sudo apt update
apt-mark showhold
python3 port/apt/check-policy.py
# Review the actual transaction before accepting; no removals allowed:
sudo apt-get --no-remove --no-install-recommends --with-new-pkgs upgrade
```

Normal `apt upgrade` also uses Sid for eligible packages. No `-t sid` or
`package/sid` is needed. Held dependencies can keep a newer application back;
that is intentional until its port dependency can be rebuilt or validated.
Do not remove holds, force dependencies, use `autoremove`, or automate a
`full-upgrade` to bypass this boundary.

[Sid is unstable](https://www.debian.org/releases/sid/), and can contain release
candidates, not only upstream stable versions (the checked curl candidate was
`8.23.0~rc1-2`). Pins and holds do not guarantee runtime compatibility, security
updates, or harmless package maintainer scripts. These retained components need
periodic security review and a coordinated update, not permanent neglect.

## What is retained, and why

[`protected-packages.txt`](protected-packages.txt) names **258 installed binary
packages from 93 source cohorts**. The initial policy retained 252; six Mesa
packages were added after the fresh-start regression described below.
Each line identifies its source. It is an explicit device-specific exception
list, **not** a list of applications allowed to update.

| Retained area | Reason |
| --- | --- |
| eqs kernel, boot image, initramfs tools, flash helper, adaptation | Preserve H29 and its boot/modules/recovery contract; keep `FLASH_BOOTIMAGE=no`. |
| Android/Halium, LXC, libhybris and wrappers | Preserve the working Android container, vendor interface and graphics loader. |
| Wayfire/wlroots-HWC, adapted Mobile and Workspace, QScreen | Stock replacements would lose HWC, navigation, startup or screen integration. |
| Qt 6 base/declarative/Wayland, Qt 5 camera dependencies, Maliit | Preserve private ABI, GLES variants, keyboard and the version-checked camera orientation library. |
| Downstream systemd/udev, GLib/GTK/libinput, NetworkManager | These installed builds contain Droidian changes; their upstream equivalents are not automatically equivalent. |
| PulseAudio/HAL, sensors, Bluetooth bridge, Waydroid helpers | Preserve vendor audio, rotation, Bluetooth and Android-app integration. |
| Mesa 25.0.7-2, six runtime packages | Mesa 26.2.3/LLVM 22 generated unsupported SVE instructions on eqs; retain the working cohort until a replacement passes actual rendering tests. |

Ordinary applications, compilers, browsers, scientific packages, libc within
libhybris's declared bounds, and unmodified KDE libraries can follow Sid when
their dependencies are satisfiable. Holding the port does **not** mean every
latest KDE application can install: Qt 6.11 users still need a coordinated
[Plasma/private-ABI update](../plasma-mobile-wf/UPGRADE-6.7.md).
The manifest excludes noninstalled packages and unneeded holds on branding,
archive keys, `firefox-mobile-config` and package-sideload. Existing user holds
must be preserved as well.

### Application ABI blockers (2026-09-29)

On the live phone, `apt-get -s --no-remove --no-upgrade` rejected four requested
Sid applications for concrete dependencies, not because APT itself is broken:

| Application | Sid dependency | Retained phone library |
| --- | --- | --- |
| Okteta, DB Browser for SQLite | Qt 5 `qtbase-abi-5-15-19` | Droidian Qt 5.15.15, including the camera-related cohort |
| LabPlot 2.12.1 | Qt 6.11.2 and `qt6-base-private-abi (= 6.11.2)` | Qt 6.10.2 with downstream GLES/Plasma integration |
| Meld 3.24.0 | GLib ≥ 2.86 through `python3-gi-cairo` | Droidian GLib 2.84.3 with downstream changes |

Even requesting the older Droidian application versions did not yield a clean
transaction under the current mixed repositories. Four ARM64 Flathub packages
were installed instead: their runtimes are separate from the phone's APT Qt
and GLib. This makes the applications available without claiming the system
libraries can now be upgraded. Short launches passed; usability needs checking
on the touchscreen.

To advance the **system** libraries later, work one source cohort at a time:
inventory reverse dependencies and downstream patches, build matching Qt/GLib
and patched consumers in a staging rootfs, simulate the complete APT transaction
with zero removals/boot changes, then validate the result on the device with a
known recovery path. In particular, Qt private-ABI consumers must be rebuilt
against the exact new version; a lone `apt-mark unhold` is not that migration.

## Configuration

- `debian-sid.sources` → `/etc/apt/sources.list.d/debian-sid.sources`:
  ARM64 `main`, HTTPS and the installed Debian archive signing keyring.
- `50-eqs-sid.pref` → `/etc/apt/preferences.d/50-eqs-sid.pref`:
  Sid **991**, Droidian **990**, neither forcing a downgrade. The specific
  `Package: /^.+$/` rule overrides Droidian's general **1002** without editing
  its packaged file. Earlier package-specific constraints still apply.
- `protected-packages.txt`: native `apt-mark hold` input, with source comments.
  **Apply and verify these holds before replacing the old restrictive policy.**
- `check-policy.py`: read-only APT preflight; honours an isolated `APT_CONFIG`.
  Checks ordinary Sid priorities, installed hold selections and an upgrade
  simulation with no removals, no retained-package changes and no new boot/kernel.
  It does not install anything or certify the hardware after a real update.

The existing GLES exclusion, earlier Plasma maintenance preferences, sources and
boot-write guard are preserved. Holds are not an authorization boundary: explicit
force flags, `dpkg`, or changing selections can bypass them. See
[APT preferences](https://manpages.debian.org/unstable/apt/apt_preferences.5.en.html).

## Verification — 2026-09-26

Signed current/Sid indices and a copy of the real ARM64 dpkg database were used
for isolated preflight. Only the copy's selections were changed during simulation.

- **RED:** the new check rejected the old allowlist because Git's Sid priority
  was `-1`, not the requested default `991`.
- **Negative control:** removing Wayfire's hold from a separate status copy was
  rejected before the upgrade solver ran.
- **Normal upgrade simulation:** **1,211 upgrades, 111 additions, zero removals**;
  no retained package changes. 392 packages remain back for holds/dependencies.
- **Full-upgrade simulation, rejected:** proposed **20 removals**, including
  Hollywood/byobu, NumPy, SciPy, Pandas, Matplotlib and KalgebraMobile. Never run
  that transaction as a shortcut around the retained ABI.

The policy was installed on the phone after verifying all 252 holds (247 added
to the previous five). Its activation alone changed no package versions; other
APT configuration and the boot-write guard were preserved. The activation's first
ordering check stopped on Spanish-vs-ASCII collation; `LC_ALL=C` made the manifest
comparison deterministic before activation proceeded. The final check against
the live APT configuration also passed, with the same 1,211/111/0 transaction.

**The authorized broad upgrade completed on the phone:** 1,211 upgrades,
111 additions, zero removals. The persistent installation unit exited successfully;
all 1,322 planned versions were installed, all 252 original retained versions and
hold selections were unchanged, and `FLASH_BOOTIMAGE=no` stayed intact. The six
Mesa packages were subsequently reverted after the launch failure below. Packages were
downloaded first, local conffiles preserved, and shutdown/sleep inhibited only
during installation. No reboot, desktop restart or flash was performed.

Initial post-installation checks on the Edge, before the owner's reboot:

- `dpkg --audit` empty; `apt-get check` and signed `apt update` successful.
- `check-policy.py`: **0 upgrades, 0 additions, 0 removals; 392 kept back**.
- Fresh SSH password authentication and `sshd -t` passed. Android LXC,
  NetworkManager, Bluetooth bridge and sensors remain active. Wayfire, Plasma
  and Ghostty kept their existing PIDs.
- Ghostty configuration validation, KCalc offscreen version check, scientific
  Python imports/calculations and Octave 11.3 passed. Git is 2.55.0; Neovim 0.12.4.
- libhybris common/Q linker load with `RTLD_NOW`; installed lockscreen palette
  tests pass for light and dark themes. This is not a GPU or real lock/unlock test.

The reboot-required marker names D-Bus and polkit. A fresh desktop boot and
physical peripheral checks remain pending; live processes can retain old libraries.
The `lxc-net` failure was already present before the upgrade; `lxc@android`
remains active.
Two superseded backup-preparation jobs failed before their replacement completed;
the actual upgrade and archive verification succeeded. The separately reported
[power-off battery drain](../bringup/diagnostics/README.md#apagado-pendiente-de-diagnosticar--26-de-septiembre-de-2026)
predates this upgrade and is **not fixed or explained by it**.

Private recovery material is retained under
`/var/cache/eqs-sid-upgrade-20260926/` (root-only): package inventories, scoped
configuration backup, installation logs and hashes for 1,211 previous-version
archives. Three unavailable original archives (`kio-extras`, `libkf6baloowidgets6`,
`libx264-165`) were repacked from installed files and verified as such. They are
not pristine distribution archives; this is **not** a full-system image or a
tested automatic downgrade. Never publish this directory or copy its saved dpkg
status over the live database. The consolidated image recipe and ZIP are unchanged.

### Fresh-start regression and targeted recovery

After an owner-initiated reboot, Ghostty 1.3.1 could no longer open. A native
launch reproduced **SIGILL after about 0.5 seconds**, including with GTK's Cairo
renderer. The private core showed `addvl`, an SVE instruction, in generated code
returning into Mesa 26.2.3's Gallium library with LLVM 22. The phone's `AT_HWCAP`
does not advertise SVE. Enabling it in a kernel configuration is not proof that
applications can execute it. The core was deleted after offline analysis.

Only these six packages were restored from hash-verified original archives to
**25.0.7-2**, with no removals or other package version changes:

```text
libegl-mesa0 libgbm1 libgl1-mesa-dri libglx-mesa0
mesa-libgallium mesa-vulkan-drivers
```

All six are now held in the manifest. Sid remains the default for other eligible
packages. Native APT check/audit pass; the final preflight reports **258 retained,
0 upgrades/additions/removals, 398 kept back**. Kernel, compositor, Ghostty wrapper,
font, theme and async backend were not changed by this recovery.

There was also an independent icon-loader failure: Bubblewrap 0.13 rejected an
old `root root 4755 /usr/bin/bwrap` statoverride. A private non-setuid copy of the
same binary passed the user-namespace test. The obsolete override was removed and
the installed binary restored to root-owned **0755**. Its native
`bwrap --unshare-all --ro-bind / / /usr/bin/true` check now succeeds. Glycin icon
loaders work again without disabling their sandbox or changing kernel policy.

**GREEN:** a fresh Ghostty process rendered with OpenGL 4.5, executed a terminal
child and exited **0** after nine seconds, with no icon-loader failures. A normal
Ghostty/Fish session also started. A remaining GSK shader warning was present in
both failed and successful runs; it was not by itself the cause.

Repeat the small rendering/PTY check **on the unlocked Edge**, not on the PC:

```sh
systemd-run --user --wait --pipe --collect -p RuntimeMaxSec=20 -p LimitCORE=0 \
  "$HOME/.local/bin/ghostty" --gtk-single-instance=false \
  -e /bin/sh -c 'printf "GHOSTTY_RENDER_OK\n"; sleep 3'
```

A configuration validator and an old process surviving an upgrade are not
substitutes for this fresh-start test. Keep Mesa retained until the same check
and affected applications pass with the proposed replacement. Do not enable SVE
blindly, turn off sandboxing, or remove the rest of the Sid policy as a workaround.

### Incremental update — September 29

A fresh signed-index preflight passed with **56 upgrades, two additions and zero
removals**. The authorized update completed; a separate reviewed transaction
installed **nine new packages** for Geany, TurboWarp, DNS and packet-capture tools.
All 258 hold selections, their installed versions and `FLASH_BOOTIMAGE=no` were
preserved. Final preflight: **0 upgrades/additions/removals, 399 kept back**;
`dpkg --audit` empty. ChatGPT Desktop is now 26.928.20755. The existing Flatpak
remote reported no pending updates; personal pinned bundles were not replaced.

Wayfire and Plasma kept their PIDs; Android LXC, NetworkManager, BlueZ and
bluebinder are active. Fresh Geany/C/Ghostty tests passed; TurboWarp needed a
process-local rendering override, documented in the [toolbox](../shell/TOOLBOX.md).
No reboot, desktop restart or flash was performed. This is live-install evidence,
not a refresh of the frozen image cohort or a post-reboot hardware validation.
Scoped package inventories and the upgrade log are private under
`/var/cache/eqs-toolbox-20260929/`; this directory is **not** a tested rollback image.


### Security-toolbox additions — September 29

A later, separate app-only expansion added **153 binary packages including
libraries**, with zero changes to previous installed versions or hold selections.
Install plans used `--no-remove --no-install-recommends --no-upgrade`; the newly
added pure-Python `python3-legacy-cgi` was then advanced to its compatible Sid
2.6.4-3 candidate. No pre-session installed version changed. H29 and all 258
holds remain intact; no new APT sources were added for this expansion. Wfuzz
needed the explicitly selected Python 3.13-compatible Droidian PycURL dependency;
its current Sid PycURL stack would conflict with `python3-gbinder`.
Native ConvertAll instead reuses the isolated science PyQt5 runtime. Installed
packages, incompatible candidates and runtime checks are documented in the
[security toolbox](../shell/TOOLBOX.md#eqs-hacking-toolbox).

Post-expansion `check-policy.py` still passes, with **zero upgrades,
additions or removals and 400 kept back**. This is not an assertion
that every latest Sid package can install. Private inventories/logs are under
`~/.local/state/eqs-hacking/` and `/var/cache/eqs-security-toolbox-20260929/`;
no rollback image was created or exported.

The subsequent terminal-UI replacement installed `python3-textual=8.2.8-1`
and six Python dependencies. Its scoped simulation and APT/dpkg transaction
logs show seven additions and zero upgrades/removals; all 258 hold selections
are unchanged. No venv, kernel, graphics cohort or image recipe was modified.

## Rollback of the policy

The previous APT configuration, selections and package inventory are kept
privately at `~/.local/state/eqs-sid-default.3kicuazu/` on the phone.
To return to the earlier allowlist, restore its saved `50-eqs-sid.pref` **first**.
Only then remove holds added by this change, preserving the original holds and
any later user additions. Re-run an upgrade simulation before installing anything.
Do not restore the old dpkg status file over the real database.

To disable Sid entirely, disable only `debian-sid.sources` and refresh the
indices, retaining the Droidian 990 rule to avoid unintended downgrades.
Changing sources or removing holds does not undo installed package upgrades.
The bulk upgrade's separate recovery material is described above; these policy
backups alone are not a full-system rollback.
