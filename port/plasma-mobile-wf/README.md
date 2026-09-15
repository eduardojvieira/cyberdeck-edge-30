# Plasma/Wayfire navigation and session safety patches

**September 15:** [6.7.5 is running on the phone](UPGRADE-6.7.md); desktop,
panel hiding, edge reveal and Home/Recents are confirmed. The scoped lockscreen
contrast fix `~pre2` is installed, pending activation; broader usability checks
remain pending.
The image recipe and the validated reference below remain eqs5.

**September 11: `+eqs5` installed and active**, with localized dates and Spanish
lockscreen labels; native packaged-resource tests pass. Only the plasmashell
user unit was restarted after Eduardo unlocked and a desktop capture confirmed
the state. Never restart the system Wayfire session to activate this change.

**September 9: `+eqs4` installed and active on the existing phone, without
flashing.** Native checks preserve both landscape transforms across lock/unlock
toggles and full Wayfire config reloads. H29's previous `+eqs3` sets the real
`autorotate-iio/lock_rotation` option, but its full INI reload also reapplies
`transform=auto`. Wayfire rejects that transform and resets to portrait.
`+eqs4` stores the actual output transform and lock together. Host and native
regressions now check the orientation, not merely the saved lock boolean.
Physical sensor movement and a fresh screen-lock cycle still need user testing.
H28's Home/Recents/Close and PAM/IPC fixes remain intact. No new compositor or
unlock policy. The package remains held: Droidian's origin priority 1002 had
previously downgraded the patched package through PackageKit.

## Source and changes

### Date and lockscreen language (September 11)

[`fix-locale.patch`](fix-locale.patch), packaged as **`+eqs5`**, replaces the
locale-insensitive `Qt.formatDate[Time](date, pattern)` calls in all six shell
clocks with `Date.toLocaleDateString(Qt.locale(), format)`. Compact clocks show
day/month names in the selected locale; lock clocks use its native long date.
Password and charging labels now use the existing mobileshell translation
domain, with Spanish entries. No locale is hardcoded in the QML and no PAM,
keyboard layout, rotation or navigation behavior changes.

This was not an old session: the rebooted phone's plasmashell already had
`LANG`/`LC_TIME=es_AR.UTF-8`. Qt 6.8.2 still rendered `Fri. September 11`.
The modules prefer embedded QRCs, so editing the loose installed QML would not
reliably fix the running code. Rebuild the package with the existing builder.

[`test-locale.cpp`](test-locale.cpp) evaluates the actual date expressions in
es_AR/en_US/de_DE. Source mode covers six clocks (18 cases); installed mode
reads the two compiled plugin resources plus the legacy shell clock (15 cases).
Halcyon is source-only: upstream disables its CMake subdirectory. The test does
not construct the lock singleton, authenticate, or interact with the compositor.

```sh
g++ -fPIC port/plasma-mobile-wf/test-locale.cpp \
  $(pkg-config --cflags --libs Qt6Gui Qt6Qml) -o /tmp/test-eqs-locale
QT_FORCE_STDERR_LOGGING=1 /tmp/test-eqs-locale "$SOURCE" # upstream: expected RED
# Repeat on a separate source copy with fix-locale.patch applied: GREEN.
# Native ARM64/Qt 6.8.2, extracted package root or / on the Edge:
QT_FORCE_STDERR_LOGGING=1 /tmp/test-eqs-locale --installed "$EXTRACTED_ROOT"
```

The builder checks both source expressions and embedded package resources, and
the three translated strings in the compiled Spanish catalog. Evidence and
artifacts: `.work/eqs-locale-clock-20260911/` (private, not a Fastboot image).

Build exit 0; all seven manifest hashes pass. The main package SHA-256 is
`f6150057b52d2df3818f7356b87d61dcbd30b2f88f5b67ffea4a3200c5dafbce`.
Native installed Qt 6.8.2: 15 date checks and three catalog checks pass.
Host: 27 PAM/IPC/navigation regressions, rotation, gesture config and seven
builder rejection checks pass. Dpkg scripts/dependencies and the PAM/IPC/rotation
C++ sources are unchanged from `+eqs4`; dpkg audit/verify are clean and the hold
is preserved. Rollback package: `/var/lib/eqs-locale-clock-20260911/` on the Edge.
The ZIP from September 10 was not rebuilt; only its next-build input was updated.

Activation evidence: `activate.log`, `pre-reload.png` and `post-reload.png` in
the same private directory. Plasma PID 5948 → 13778; Wayfire 4475 and the boot ID
were preserved. The new process has `LANG`/`LC_TIME=es_AR.UTF-8`, loads the current
plugins, and has no automatic restarts. The lockscreen visibly shows
«viernes, 11 de septiembre de 2026» and «Descargando». It relocked normally on
startup; a later unlocked status-bar capture is still pending (native clock
tests pass). Existing QML warnings also occur in the previous PID's journal;
this locale change does not fix those unrelated warnings.
`actual_brightness=0` was also observed with the desktop visible: that node
alone is not an awake/locked-state check. The root backup's `STATUS` records the
earlier installation checkpoint; current activation is recorded in the user's
`~/.cache/eqs-locale-clock-20260911/ACTIVE`.

### Desktop and lock wallpaper (September 8)

The current phone has a **per-user image wallpaper override** at
`~/.local/share/plasma/wallpapers/org.kde.image/`, applying
[`follow-desktop-wallpaper.patch`](follow-desktop-wallpaper.patch).
Long-press an empty home-screen area → **Wallpapers** → choose an image.
The lock background now follows that selection without a separate picker.

The patch observes Plasma's resolved `MediaProxy.modelImage` and uses the existing
`SessionLockSettings.wallpaperFile` setter, including its KConfig notification.
It does not change locking, PAM, keyboard handling, compositor or system files.
No daemon or polling; no screenshot is used as a wallpaper. Scope: this phone's
image wallpaper, not arbitrary third-party/video or solid-color plugins.

Baseline: `plasma-workspace-data`
`4:6.3.4-1~git20250502212128.c41cc1c.next.upgrade.6.3`;
`contents/ui/main.qml` SHA-256:
`7ab8ecbee7a7eb3d5102b93c1d813bed63519359752607681ad2c5ff168a5ba9`.
The stock lock setting pointed to a missing Debian SVG. Native RED/GREEN checks
confirmed the replacement, a file with spaces/`#`/Unicode, and a KDE wallpaper
package resolving to an actual image. The original desktop image was restored;
Plasma's PID and the phone's boot ID did not change. Lock-screen pixels and a
fresh graphical login were not tested.

Read-only native check (run as `droidian`, not root):

```sh
python3 test-wallpaper-sync.py
```

Backup: `~/.local/state/eqs-wallpaper.CnCbLR/`. To revert, move only the user
wallpaper override out of Plasma's search path, restore the prior lock wallpaper
if desired, and reload the wallpaper or start a new graphical session.
The user override survives package updates but can mask upstream wallpaper fixes:
rebase/verify this small patch when upgrading `plasma-workspace-data`.
It is not yet integrated into the rootfs builder.

### H28/H29 package patches

- Repository: [droidian/plasma-mobile-wf](https://github.com/droidian/plasma-mobile-wf).
- Commit: `69444e68c5d59fbcdeb79acc1a49313a4f114148`.
- Full source archive SHA-256: `559c81cc6a4f97b234802ced57fbc126defede7d155b4daf510ce735d6c6054f`.
- Installed package baseline: `6.3.3-1~git20250414214107.69444e6.next.upgrade.6.3`.
- Patch: [`fix-session-safety.patch`](fix-session-safety.patch), touching only
  `sessionlock.cpp`, `wayfireipc.cpp` and `wayfireipc.h`.
- Navigation: [`fix-navigation.patch`](fix-navigation.patch), the existing IPC
  class plus four QML callers. Home minimizes app views idempotently, Recents
  invokes native Scale, Close requires a fresh snapshot and unchanged focus.
  Lock state, protected surfaces, a 512-view cap and 1.5-second timeout guard it.
- Rotation: [`fix-rotation.patch`](fix-rotation.patch), only the existing
  `ScreenRotationUtil`. Read `HWCOMPOSER-1`'s actual `QScreen` orientation,
  preserve raw INI bytes, atomically save transform plus lock and
  reload external changes with `QFileSystemWatcher`; no second sensor owner.
  Reject malformed, duplicate, oversized, symlinked or unwritable settings;
  refuse to change rotation without the actual display or for mirrored outputs.
  Mapping for eqs's portrait-native panel: portrait → `normal`, inverted
  landscape → `90`, inverted portrait → `180`, landscape → `270`.

PAM credential buffers stay alive through `pam_end`. Conversations distinguish
username/password prompts from informational messages, allocate the response
array correctly and free partial responses on failure. Failed `pam_start` does
not end an invalid handle; ended handles are cleared. Authentication/account/end
errors still deny unlock; NUL-containing input is rejected and authentication
requests `PAM_DISALLOW_NULL_AUTHTOK`. No real host PAM authentication runs in tests.

IPC uses Qt's socket buffer and owned `QByteArray` data, not raw `char[]`.
Incomplete frames remain buffered; zero/over-1-MiB lengths and invalid JSON
objects disconnect without logging payloads. The 1-MiB bound matches the existing
eqs diagnostic client. Processing yields after 32 frames, and the socket is a
QObject child. This does **not** add reconnect or change the existing one-second
startup connection wait. A protocol-error disconnect requires a session/client
restart; it never authorizes an unlock.

## Offline regression

Host requirements: Python 3, `patch`, Clang with ASan/UBSan, Qt 6.7+ Core/Qml/Network
development files and `moc`, and PAM headers. No PAM library, Docker, phone,
network download or elevated privileges are needed for this test.

```sh
export TMPDIR="$PWD/.work/test-tmp"
mkdir -p "$TMPDIR"
# SOURCE is the full unmodified pinned source, including the four QML callers.
SOURCE="$PWD/.work/plasma-safety/upstream-full"
python3 port/plasma-mobile-wf/test-safety.py "$SOURCE"
# Negative control: must fail on the source defects, not compilation/setup.
python3 port/plasma-mobile-wf/test-safety.py "$SOURCE" --upstream
```

The runner checks four source SHA-256 pins **before** copying/applying the patch
in a temporary directory. It leaves SOURCE unchanged. PAM tests compile the
actual callback and authentication/cleanup method bodies, substituting only the
PAM/account lookup/allocation boundaries. Other SessionLock GUI methods are not
compiled by this test. IPC tests compile the complete class and generated `moc`,
using real local sockets and signals, including every split in a small frame.

H28 verification: **27 cases passed**, host Qt 6.11.2, ASan/UBSan and
leak checking. The target uses Qt 6.8.2. Coverage includes authentication errors,
multiple/invalid PAM messages, allocation failures, NUL input, fragmented and
coalesced frames, invalid sizes/JSON, EOF, socket lifetime and the 1-MiB boundary.
Navigation adds idempotence, focus-race, lock, malformed snapshot, timeout and
protected-surface cases. Logs: `.work/eqs-preview-h28/host-regression.txt`. Source-body/host tests are not full QML plugin,
real PIN, ARM64 ABI, display or HIL validation.

## Rotation regression

```sh
python3 port/plasma-mobile-wf/test-rotation.py "$SOURCE"
# Inside the prepared offline ARM64 container (Qt 6.8.2):
qt_include=$(pkg-config --variable=includedir Qt6Gui)
qt_version=$(pkg-config --modversion Qt6Gui)
g++ test-rotation-import.cpp $(pkg-config --cflags --libs Qt6Core Qt6Gui Qt6Qml) \
  -I"$qt_include/QtGui/$qt_version" -I"$qt_include/QtGui/$qt_version/QtGui" \
  -I"$qt_include/QtCore/$qt_version" -I"$qt_include/QtCore/$qt_version/QtCore" \
  -o test-rotation-import
LD_BIND_NOW=1 ./test-rotation-import EXTRACTED_PACKAGE/usr/lib/aarch64-linux-gnu/qt6/qml
```

Both tests use Qt's minimal platform and a virtual `HWCOMPOSER-1`; they require
QtGui private development headers **only for the test**, not the production
patch. The first compiles the exact class with ASan/UBSan/LSan and covers all
four orientations, enable/disable, external reloads, byte preservation, missing
keys/sections and refusal paths. The second imports the packaged singleton and
checks both landscape directions in a temporary INI. Neither rotates a real
screen or unlocks a session. A native trial must separately verify the actual
Wayfire transform after its full config reload, not just `lock_rotation=true`.
September 9 host RED/GREEN evidence: `.work/eqs-rotation-lock/`.

### September 9 installation and rollback (+eqs4)

Main package SHA-256:
`a208c4c752ed4eee2bc58c52a896ef388ee01b0f247f65214e393befd14fd2fe`.
Build output: `.work/plasma-safety/docker-build/package-output/rotation-eqs4/package/`.
All seven manifest entries pass; all three patched QML modules import with
ARM64/Qt 6.8.2. The exact packaged rotation singleton also passes on the phone
using a virtual output; the old `+eqs3` fails that new regression after loading.

Only the main `.deb` was installed, following a dry run. Maintainer scripts are
byte-identical to `+eqs3`; dependencies are unchanged. `dpkg --audit` and
`dpkg --verify plasma-mobile-wf` are clean, and the package remains held.
No kernel, partitions, Qt, compositor, HWC config or tweaks package was changed.

To activate it, only the existing transient **user plasmashell unit** was
restarted after checking the display was awake/unlocked and its cgroup contained
only Plasma. Plasma changed from PID 6234 to 39036; Wayfire 5801, both terminals,
Firefox and the boot ID stayed unchanged. **Do not restart the system
`plasma-mobile-wf.service` for this: it owns the entire graphical session.**

`native-trial-installed.log` verifies the installed singleton against live
Wayfire: both `90` and `270` survive disable/enable, the effective IPC lock
boolean matches, and unrelated INI bytes stay identical. Original `270` and
enabled autorotation were restored. A privately extracted `wlr-randr` sets the
test orientations; no sensor motion, PIN entry or visual touch test is implied.
No diagnostic daemon or scheduled task was installed.

Phone backup: `~/.local/state/eqs-rotation.3Qzk0n/`, including original INI,
library and exact `+eqs3` `.deb`. Rollback, if needed and explicitly authorized:
install that previous main package, retain its hold, restore the backed-up INI
and reload only Plasma while unlocked. This restores the old rotation bug too;
it does not require flashing. A reboot/relogin with the new package has not
been tested.

## Native Wayfire gestures

`prepare-navigation-config.py EXISTING_INI NEW_INI` preserves raw Wayfire values
and creates a new file only. `test-navigation-config.py` checks routing, color
escaping, preservation and overwrite refusal. Do not use `kwriteconfig6` here:
KConfig doubles existing escaped color prefixes and changes Wayfire's input.

- Bottom edge upward, one finger: Plasma Home D-Bus → patched IPC.
- Right edge inward, one finger: Wayfire `scale/toggle_all`.
- Whole edges, no conflicting Cube gestures; keep navigation buttons visible.

These fire after finger release, not Android-style interactive animations or a
universal Back gesture. Physical recognition, lock/unlock, Home from overview
and keyboard hiding remain explicit tests. The old KWin virtual-keyboard branch
is retained; adapting Maliit visibility is not claimed by this patch.

## Maximized window sizing

The native user configuration now uses `core/transaction_timeout = 1000` (ms),
also emitted by `prepare-navigation-config.py`. It is a shared, bounded resize
wait, not an app whitelist or a window-resizing daemon. `place/mode=maximize`,
panel reservations, fullscreen and transient-window rules remain unchanged.

On September 9, Wayfire `15065ca1` with the original 100 ms limit requested
1200 × 479 from Ghostty, then negotiated the old 800 × 479 size after the late
buffer commit, retaining all maximized edges. Disabling grid crossfade did not
fix it. Changing only the timeout to 1000 ms did: three independent Ghostty
launches and one isolated KDE Kalk launch filled the workarea at scale 200% in
landscape. Ghostty's test commands also exited successfully; correct outer
geometry alone was not accepted as proof of a working terminal.

Applied by hot reload without restarting Wayfire/Plasma or closing the user's
applications. The already-open Ghostty was resized once through native IPC.
Backup and sanitized native evidence: `~/.local/state/eqs-gpu.0KlZPw/`.
This is not a guarantee for clients stalled beyond one second. Portrait,
transient-dialog and fullscreen regression tests have not been performed for
this change. Existing package/image artifacts were not rebuilt: apply the
configuration helper when preparing a new user session.

## ARM64 package build

[`build-package.sh`](build-package.sh) builds the normal upstream Debian packages
at revision `6.3.3-1~git20250414214107.69444e6.next.upgrade.6.3+eqs5`.
It refuses changed source/patch hashes, existing output (including symlinks),
root execution, a non-container/non-ARM64 environment, a different snapshot or
different private Qt dependencies. It does not download, install or flash.
After the build it checks package metadata and all three patched plugins' ELF64/AArch64
headers, and records package inventory, provenance, `.buildinfo` and SHA-256.

The prepared **local** build image is
`sha256:2e7eb7d02ddfc2499a236b56fa2ece6570671bdbc1634c488756a25470e86f26`
(`cyberdeck-edge30/plasma-arm64-build:101.20251130`). It contains the verified
source archive and the complete snapshot build dependencies. With authorized
Docker access, from the repository root:

```sh
mkdir -p "$PWD/.work/plasma-rebuild"
sudo docker run --rm --pull never --network none --platform linux/arm64 \
  --user 1000:1000 --cap-drop ALL --security-opt no-new-privileges \
  --cpus 4 --memory 8g --memory-swap 8g --pids-limit 1024 \
  --env HOME=/home/eqs-builder \
  --mount "type=bind,src=$PWD/port/plasma-mobile-wf,dst=/eqs-plasma-safety,readonly" \
  --mount "type=bind,src=$PWD/.work/plasma-rebuild,dst=/work" \
  sha256:2e7eb7d02ddfc2499a236b56fa2ece6570671bdbc1634c488756a25470e86f26 \
  /eqs-plasma-safety/build-package.sh /plasma-source.tar.gz /work/run-one
```

`run-one` must not exist. Failed builds remain available for inspection; the
script never deletes a previous run or silently resumes a mixed source tree.
The H29 build finished with exit 0 on 2026-09-06. Artifacts and provenance:
`.work/plasma-safety/docker-build/package-output/run-h29-one/`. The four `.deb`
packages, `.buildinfo` and two manifests pass all seven `SHA256SUMS` entries.
All three patched plugins are ELF64/AArch64. Upstream CTest reports **no tests**;
the regression and QML checks below are separate evidence. A second identical
build has not been run; this is not a bit-for-bit reproducibility claim.

The historical H29 `+eqs3` main package SHA-256 is
`acc879833e6ff3dd2845f346d483ed17337b26883dd4a4b4061567c0c25243ab`.
It is a Debian package candidate, **not a Fastboot ZIP**.

Seven host rejection checks, including changed navigation, rotation and locale patches:

```sh
export TMPDIR="$PWD/.work/test-tmp"
python3 port/plasma-mobile-wf/test-build-package.py \
  .work/plasma-safety/docker-build/downloads/plasma-mobile-wf-69444e68c5d59fbcdeb79acc1a49313a4f114148.tar.gz
```

[`test-plugin-import.cpp`](test-plugin-import.cpp) imports the two extracted QML
plugins with Qt 6.8.2/offscreen and resolves their registered types **without
constructing their singletons or authenticating**. Compile/run commands are in
its header. Both original and **new ARM64 packages pass** with `LD_BIND_NOW=1`;
H28's Qt loader trace identifies each new `.so` under `run-h28-one/inspection`
in `.work/eqs-preview-h28/plugin-import.txt`. A
separately corrupted plugin is rejected by Qt's ELF loader. Evidence:
`package-output/import-{baseline,candidate,negative}.log` under the build directory.
This checks loading/registration, not PIN behavior, Wayland locking or display.

Package review: the new dependencies explicitly select `libqt6gui6-gles` and
`libopengl0`, both already present at matching versions in the captured rootfs
inventory. QML/Wayland private ABI remains 6.8.2. Maintainer-script logic is
unchanged (only debhelper comments differ); HWC config payload is unchanged
apart from its changelog. Do not upgrade the HWC-config/tweaks packages or the
graphics stack merely because they were produced by this build. The captured
inventory is not a substitute for checking the current phone's package state.

### Recreating the build environment

The local image above is a convenience cache, not a public image or a phone
rootfs. Its inputs and preparation are:

1. Pinned upstream rootfs-builder:
   `quay.io/droidian/rootfs-builder@sha256:749133320ea6d913989005ac8519630059dac465dd91d7be95066255b0ba434e`.
   Use the existing QEMU AArch64 binfmt registration; do not re-register it or
   grant privileged access to host devices just to build packages.
2. In that disposable container, run
   `debootstrap --arch=arm64 --foreign --variant=buildd --include=ca-certificates --force-check-gpg --keyring=/bootstrap-keyring.gpg rolling /arm64 http://releases.droidian.org/snapshots/101.20251130 /usr/share/debootstrap/scripts/sid`.
   `/bootstrap-keyring.gpg` is a read-only bind of
   `reference/repos/droidian-images/droidian/rootfs-templates/apt/etc/apt/trusted.gpg.d/droidian-bootstrap.gpg`
   from rootfs-templates commit `d2212f43e8de78e3b759d94ee427e24268655aee`.
3. Export `/arm64/.` using `docker cp CONTAINER:/arm64/. -`, and import that tar
   with `docker import --platform linux/arm64`. Start this ARM64 container with
   a writable build directory, **no host devices**, and the limits above.
   Inside it, create `/usr/sbin/policy-rc.d` returning 101 and
   `/etc/flash-bootimage/01prevent-flashing` containing `FLASH_BOOTIMAGE=no`;
   then run `/debootstrap/debootstrap --second-stage`.
4. Create `/etc/apt/trusted.gpg.d` before copying the bootstrap key. Use only
   `deb [signed-by=/etc/apt/trusted.gpg.d/droidian-bootstrap.gpg] http://releases.droidian.org/snapshots/101.20251130 rolling main`
   and set `Acquire::Droidian::Version "101.20251130";` in
   `/etc/apt/apt.conf.d/90-droidian-snapshot`. Update APT; simulate then install
   `libqt6gui6-gles` with `--no-install-recommends`. From the verified full source
   directory, simulate then run `apt-get --no-install-recommends build-dep .`.
5. Require empty `dpkg --audit` output and successful `dpkg-checkbuilddeps`.
   Create the locked, unprivileged build user UID/GID 1000, preserve the source
   archive at `/plasma-source.tar.gz`, and disconnect the container's network
   before compiling. Capture the image ID and installed package inventory.

This follows [debootstrap's foreign/second-stage workflow](https://manpages.debian.org/trixie/debootstrap/debootstrap.8.en.html).
The server refused HTTPS during this run; HTTP is the upstream snapshot URL,
with **mandatory signatures and package hashes**, not `trusted=yes` or disabled
verification. Independently verified InRelease SHA-256:
`d2ed5bd6f6634028a637abe57d4ed0e13d7422c3fb003a5b6745adcfa750b423`, signing key
`F5E431F127AFEA50AB6C37037AC7CFDDA43098E0`.

## Device integration and H27 result

Host preparation now also includes `grim` 1.4.0+ds-2+b2, `tmux` 3.5a-3,
`libinput-tools` 1.28.1-1 and four missing dependencies, cached with signed-index
hashes in `.work/plasma-safety/docker-build/package-output/devtools/` (about 1 MB).
Offline ARM64 smoke checks created a real container PTY with tmux, recovered its
output and confirmed grim refuses an absent compositor without producing a PNG.
Those smoke checks are not phone/SSH/touch tests. The seven packages were later
installed in the authorized H27 trial; native QMLKonsole reported tmux 3.5a.
No SSH server or credentials were provisioned.

The [existing native capture](../bringup/diagnostics/README.md) now has an optional,
bounded screenshot and read-only backlight evidence, with host regressions for
missing tools, refusal, timeout, empty/invalid output and stale files. H27 produced
a decoded 1080x2400 PNG showing Plasma/QMLKonsole. Eduardo reported visible boot;
touch, real PIN and sustained presentation remain unverified.

1. For future package trials, install only with explicitly authorized access,
   exact package rollback and H26 boot/rescue preserved. Change **only the main
   `plasma-mobile-wf` package**; preserve `/etc` and user session overrides.
   Check free space and simulate APT first: no removals or unrelated upgrades.
   Suppress maintainer-script service starts during installation: upstream's
   `--no-restart-on-upgrade` still permits starting a stopped Plasma service.
   Test failed/successful PIN entry, events, screen/touch and graphical recovery.
2. Add that **validated package**, not these loose source files, to the existing
   image builder's internal APT repository. Do not copy an x86-64 test binary to
   the phone or claim the current ZIP includes this patch.

The local handoff directory `.work/plasma-safety/native-trial-eqs1/`
contains the main candidate, its exact original rollback, the seven devtool
packages, current capture script, source/build pins and SHA-256 checks. It has
**no installer, boot images, rootfs or credentials**. Its included checklist
requires the existing H26 environment, usable authenticated access, free space
and preserved recovery before any installation. It is not flashable via Fastboot.
Archive creation was blocked by the local security guard before execution;
no `.tar.gz` was delivered and no alternate route was attempted.

Host preflight (2026-09-05): scoped, authorized `sudo docker` now works without
changing groups or socket permissions. Offline containers start after increasing
the live `/tmp` inode limit from 1,048,576 to 1,114,112; no files were deleted and
no services restarted. This is a temporary host setting, not an image change.

The old amd64 builder's snapshot `101` metadata conflicted with its installed
multiarch `libudev1`. The fresh ARM64 environment above avoids that mismatch;
network authorization was granted and dependency installation completed.

H27 upgraded only the main Plasma package, preserving HWC-config, Qt and session
overrides; APT simulation selected no unrelated upgrades/removals and dpkg audit
and verification passed. Service starts were suppressed during recovery installation.
Original main and HWC-config
packages are preserved under `.work/plasma-safety/docker-build/package-output/rollback/`
with hashes verified against the signed snapshot index. Keep the known boot/rescue
and `/etc` integration overrides intact. H27 evidence and the boot/rescue bundle
are in `.work/eqs-preview-h27/`; it is not a complete rootfs installer.
