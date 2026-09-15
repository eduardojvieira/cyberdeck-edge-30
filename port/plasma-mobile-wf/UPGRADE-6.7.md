# Plasma 6.7.5 upgrade — work in progress

**September 15, 2026: desktop and physical panel navigation confirmed.**
The phone has Mobile and adapted Workspace **6.7.5**, Qt **6.10.2 GLES** and
Frameworks **6.28**, retaining H29 and Wayfire/HWC.
A controlled shell-only restart activated 6.7.5. The missing QScreen backend
and its selector were repaired; Wayfire and the existing applications were not
restarted during that activation. A subsequent boot and an unlocked screen
capture confirm the landscape desktop, populated dock, 200% scale and Spanish
top-bar date. Eduardo also confirmed that panel hiding, edge reveal and
Home/Recents work on the phone. This is not a complete usability or
GPU-acceleration validation.
The image inputs and known-good builder remain **6.3.3+eqs5**. Do not remove the
custom-package holds or switch the phone to `next` to bypass dependency checks.

## What was verified

Before the upgrade, authenticated SSH access and
`apt-get -o APT::Update::Error-Mode=any update` succeeded. The channel was already
`current`; an upgrade simulation selected zero changes. Those repository
Plasma/Qt packages were older than the upstream 6.7.5 requirements.

| Component | Before upgrade (`current`) | Isolated `next` index | Upstream 6.7.5 requirement |
| --- | --- | --- | --- |
| Plasma Mobile / Wayfire | 6.3.3 +eqs5 | No repository `plasma-mobile-wf` candidate | Rebase the adaptation |
| Qt | 6.8.2, Droidian GLES | 6.10.2, Droidian GLES | At least 6.10.0 |
| KDE Frameworks | 6.13.0 | 6.28.0 | At least 6.26.0 |
| Plasma Workspace | 6.3.4, Droidian fork | 6.7.4, Debian package | Preserve Wayfire startup patches |

The `next` index was fetched into a separate user-owned APT directory. **It was
not added to the phone's sources.** Its InRelease SHA-256 was
`fe58534bdf1cd0618e23f49f57d724692d2de33c6024527d59890e046c11a2be`.
It also changes libhybris to a different development branch. Availability of its
packages does not establish compatibility with the working HWC adaptation.

The targeted upgrade simulation correctly refused to combine the installed
shell's `qt6-declarative-private-abi (= 6.8.2)` and
`qt6-waylandclient-private-abi (= 6.8.2)` with Qt 6.10.2. `libplasma6` also changes
to `libplasma7`. This needs a rebuilt, coherent package set, not an APT force flag.

The phone was missing the image recipe's boot-flash guard. It now has
`/etc/flash-bootimage/01prevent-flashing` containing `FLASH_BOOTIMAGE=no`, and
holds on `linux-image-motorola-eqs` and `linux-bootimage-motorola-eqs` in addition
to `plasma-mobile-wf`. These are userspace configuration changes, not a flash.
No compositor restart or password change was performed.

## Source candidates

Private worktrees and build logs are under `.work/plasma-6.7.5-upgrade/`.
They are development inputs, **not installable releases or image inputs**.
The complete Mobile adaptation is now preserved in
[`upgrade-mobile-6.7.5.patch`](upgrade-mobile-6.7.5.patch), including packaging;
it applies to the clean KDE Git source below, not to eqs5 or the Droidian fork.

- [KDE Plasma Mobile v6.7.5](https://github.com/KDE/plasma-mobile/tree/v6.7.5):
  `10773c81e36b322f307737391f836126d1115277`.
  The [official source archive](https://kde.org/info/plasma-6.7.5/) hash verifies:
  `e25d53707be3bf86aad2b2712bcdcb9133f7c75a54c434724de5663aa78b773f`.
- Droidian's Wayfire delta comes from
  `91ba13c86f6893fed1505acf97c5594a67318ab3`, relative to its upstream v6.5.2.
  Startup, wallpaper and Waydroid UI conflicts were resolved in the candidate;
  the deleted virtual-keyboard KCM was not restored.
- The candidate reuses the exact eqs5 PAM/IPC and rotation implementations,
  with navigation callers updated for the new QML paths. The newer Droidian
  reference still contains the old PAM lifetime bug: “newer” is not a reason
  to drop the safety patches.
- Native KDE 6.7 clocks already use locale-aware dates. The candidate keeps
  those changes and localizes the Droidian lockscreen separately.
- The new KScreen rotation-suggestion helper must not start a second sensor
  policy under Wayfire; the existing quicksetting/autorotate-iio path remains
  responsible for orientation locking. ARM64 compilation and a synthetic
  sensor test pass; physical rotation and lockscreen checks remain pending.

**Workspace is part of the port too.** Its standard `plasma_session` starts
`kwin_wayland_wrapper` without honoring `KDE_NO_KWIN`. The small
[`upgrade-workspace-6.7.5.patch`](upgrade-workspace-6.7.5.patch) preserves
Droidian's classic-startup and splash changes on
`cc1ab7963f94a9b76836412855caed6b94066188` (KDE v6.7.5), using Droidian
`781719c6098b88e32de0d3f509af391795162466` as the reference. It omits cosmetic
logging changes. Both changed targets (`plasma_session` and `ksplashqml`)
compiled for ARM64. Full Debian package construction passed; the 17 runtime packages passed
final-payload inspection before the phone installation.
The existing `startkderc` with `systemdBoot=false` must also be preserved.

Workspace packaging comes from Debian `6.7.4-1` plus
[`upgrade-workspace-packaging-6.7.5.patch`](upgrade-workspace-packaging-6.7.5.patch).
The source archive SHA-256 is
`d5443ffba4932e1801f5703066a299ef3253b58d0d66f8d6ee36e010ca518852`;
it was checked against the HTTPS DSC, not a verified DSC signature. The patch
keeps Debian hardening and locates the installed multiarch QCoro Core config.

The Mobile candidate requires exactly the adapted
`plasma-workspace 4:6.7.5-0+eqs1~pre1`. A stock Workspace with KWin startup is not
an interchangeable dependency. Its refreshed payload includes the new Panels
D-Bus interface, presets, metainfo and logging categories. Packaging does not
start, enable or restart the shell service during the upgrade.

### Panel and gesture integration

The new panel tracker uses KWin's window-management protocol, which the
installed Wayfire does not provide. The candidate instead reuses the existing
bounded Wayfire IPC client for foreground/fullscreen state and clears it on
disconnect. This intentionally supports **one internal screen with maximized
apps**, not arbitrary multi-output or overlapping-window tracking. The gesture
handle now invokes the same guarded Wayfire overview action as the buttons.

The pinned Wayfire source registers `view-fullscreened` but emits
`view-fullscreen`; focus and geometry events therefore provide the fullscreen
state fallback. No compositor replacement was made to work around that bug.
Plasma's panel reveal uses its own touch strip and layer-shell; physical testing
must also check coexistence with the existing Wayfire edge-swipe bindings.
**The package default stays disabled.** On September 15, the native
setting was enabled on Eduardo's phone for the physical check, without a
restart. Wayfire's workarea expanded from 1200×482 to 1200×540 logical pixels;
this confirms that the running panels released their reserved space. Eduardo
then opened an application and confirmed the physical test: bars hide, reveal
on edge swipes, and Home/Recents respond correctly. Keep this user-reported
hardware evidence distinct from the earlier synthetic IPC tests.

The existing **Auto Hide Panels** quicksetting toggles it. The equivalent
command, run as the desktop user, is:

```sh
kwriteconfig6 --file plasmamobilerc --group General \
  --key autoHidePanelsEnabled --type bool --notify true
```

Use `false` to undo it, with no restart. To repeat the confirmed check, open an
application: the bars should hide, reveal from the screen edges, and still
provide working Home and Recents actions. The live-phone confirmation does not
promote the candidate cohort into the image; the remaining usability checks
and reproducible image integration are separate work.

### QScreen backend restored and activated

The new shell exposed a real integration failure: `libkscreen-bin 6.7.4-1`
no longer ships `KSC_QScreen.so`, while the inherited environment still selects
it. Mobile's Panels D-Bus manager retries failed configuration reads without a
delay, producing a CPU/logging loop. The new backend selector also expects
`QScreen`, not the old filename-form value `KSC_QScreen.so`.

The [small QScreen adaptation](qscreen-6.7/README.md) restores the read-only
upstream backend against the exact installed private ABI. It rejects output
writes, reports actual scale and geometry, and tracks Qt screen changes. It
is packaged separately rather than copying the incompatible old plugin.

- **Installed:** `eqs-kscreen-qscreen 6.7.4-0+eqs2`, built from the public
  CMake/CPack recipe after clean source/patch replay.
- Package SHA-256: `573de571646085b2d5b262bf38b1acfe22567fe194681f3e474f85bd04862455`.
- Native read-only `GetConfigOperation`, 200% metadata and rejected writes
  pass. The SDK additionally passes four virtual orientations, primary-output
  selection, workarea exclusion, live config updates and output removal.
- After the user unlocked, the shell-only restart produced a new 6.7.5
  process and registered `/Mobile/Panels/HWCOMPOSER1`. Its log has **zero**
  failed-KScreen-config retries. Wayfire PID and independent app PIDs stayed
  unchanged. The temporary CPU cap was removed (`CPUQuota=` resets it;
  `CPUQuota=infinity` is rejected by the installed systemctl).
- The first restarted shell loaded addon `+eqs1`; `+eqs2` subsequently corrected
  primary-output ordering discovered by the two-screen synthetic test. A
  fresh native process tested the installed `+eqs2`. On the subsequent boot,
  the shell's mapped plugin inode matches the installed `+eqs2` file, and
  `dpkg -V eqs-kscreen-qscreen` reports no differences. Its startup environment
  has the persistent selectors and its journal has zero KScreen retry errors.
  No reboot was issued during this follow-up validation.

The persistent session launcher, user-manager activation environment and
existing transient shell unit now use `KSCREEN_BACKEND=QScreen` and
`KSCREEN_BACKEND_INPROCESS=1`. Neither kernel nor compositor was changed.

**Launcher boundary:** the tested phone uses `eqs-wayfire-session`, whose
corrected selectors are recorded in
[`port/bringup/diagnostics/eqs-wayfire-session`](../bringup/diagnostics/eqs-wayfire-session).
The Mobile package still contains the inherited filename-form selectors in
`/usr/bin/startplasmamobile-wf`; that launcher is bypassed on this phone.
Preserve the tested launch override and QScreen addon when reproducing the
development setup. Installing the Mobile package alone is not sufficient.
Fixing its default launcher requires a new package revision; do not silently
change the source associated with the recorded `~pre2` package hash.

A shell restart relocks the session. Earlier screencopies caught an interim
large graphic or were refused while locked; the later unlocked capture in
`.work/plasma-6.7.5-upgrade/validation/desktop.png` shows the actual desktop
rendering normally. Do not treat the interim graphic as the final UI state.

Startup warnings still mention older Waydroid/PowerDevil/audio/notification
interfaces. Two startup helpers (`plasma-mobile-initial-start` and the fallback
session restore) also report SIGSEGV; the former logged that its already-used
wizard would not run. No core/backtrace was available through `coredumpctl`
(not installed), so their cause is unresolved. The shell remains running;
that does not establish that session restoration or every application works.
**Do not mark the entire UI or hardware matrix passed from this backend fix.**

For a full cohort rollback, first simulate and then remove **only**
`eqs-kscreen-qscreen` with `--no-auto-remove`, as part of the prepared rollback
session. The native removal simulation selects exactly that one package;
then the existing 356-package return path can reclaim the old QScreen plugin
without file ownership conflicts. Do not run the old rollback helper directly
with the addon still installed, and do not use autoremove.

### Lockscreen contrast follow-up (`~pre2`)

The live light theme has Window text `#363636`, but Complementary text
`#eff0f1` over `#333333`. Desktop panels already select Complementary over the
wallpaper; the custom Wayfire lockscreen did not, explaining the dark clock
and labels. The `~pre2` recipe sets a **local** non-inheriting Complementary
palette on the lock root and its transition window. The transition label
explicitly uses the window's theme because QQuickWindow does not propagate
that attached palette to its content item. Global desktop colors, wallpaper,
PAM and navigation code are unchanged. This follows the existing
[Kirigami color-set mechanism](https://develop.kde.org/docs/getting-started/kirigami/style-colors/),
not a new theme or a global foreground override.

[`test-lockscreen-colors.cpp`](test-lockscreen-colors.cpp) evaluates the actual
root palette declarations and transition-label binding with real Kirigami and
desktop Label controls, in isolated light/dark configurations. It never
instantiates the real lock, PAM or hardware services. The source check fails
with the old dark foreground and passes for both surfaces in both palettes.
The installed mode reads the **compiled QRC payload**, not loose QML.

```sh
g++ -fPIC port/plasma-mobile-wf/test-lockscreen-colors.cpp \
  $(pkg-config --cflags --libs Qt6Quick Qt6QuickControls2) -o /tmp/test-lock-colors
QT_FORCE_STDERR_LOGGING=1 /tmp/test-lock-colors --source "$candidate" light
QT_FORCE_STDERR_LOGGING=1 /tmp/test-lock-colors --source "$candidate" dark
# In the matching ARM64 SDK, or natively on the Edge:
QT_FORCE_STDERR_LOGGING=1 /tmp/test-lock-colors --installed "$EXTRACTED_ROOT" light
QT_FORCE_STDERR_LOGGING=1 /tmp/test-lock-colors --installed "$EXTRACTED_ROOT" dark
```

**Incremental-build trap:** Debian's cached `binary` sequence initially copied
the new loose QML but left both plugin resources unchanged. The final-payload
test rejected that package before installation. Explicitly build
`mobileshellplugin` and `sessionlockplugin` with CMake before repeating binary
packaging; package build exit zero alone is insufficient. Private evidence is
under `.work/plasma-6.7.5-upgrade/lock-colors/`. Activation and the physical
contrast check remain pending. Eduardo chose to reboot later himself; the
unlock watcher was canceled without restarting Plasma or Wayfire.

**Installed:** `plasma-mobile-wf 6.7.5-0+eqs1~pre2`, SHA-256
`d191d15d6c755ca173aaddcfca7d42afef78575c18b94af16ae250eaa3d9aad7`.
The final package passes four ARM64 palette checks and all 18 date checks.
Its runtime ELF sections change only in the two intended plugins; 42 other
ELFs differ only in GNU debug links after DWZ packaging. Dependencies and
maintainer scripts are unchanged. Clean source replay matches all 101 paths;
the source delta from `~pre1` is two QML files and the Debian changelog only.

On the Edge, the same four compiled-resource palette checks pass; `apt-get
check`, `dpkg --audit` and package verification are clean. `kdeglobals` is
byte-for-byte unchanged, and the package remains held. Neither plasmashell nor
Wayfire restarted during installation, so the running shell still uses the old
resources until a controlled activation. The root-owned
`/var/cache/eqs-plasma-6.7.5-20260915/lock-colors/` retains both revisions,
SHA-256 sums and install logs for a scoped return to `~pre1`. Native APT
simulation selected exactly one upgrade and no removals. Its `--no-download`
mode rejected local-file staging, even with an absolute path; the ordinary
local-file transaction succeeded without importing another package.

## Repeat the host checks

```sh
candidate=.work/plasma-6.7.5-upgrade/candidate
python3 port/plasma-mobile-wf/test-safety.py "$candidate" --prepared
python3 port/plasma-mobile-wf/test-safety.py "$candidate" --prepared --case nav-panel-state
python3 port/plasma-mobile-wf/test-rotation.py "$candidate" --prepared
g++ -fPIC port/plasma-mobile-wf/test-locale.cpp \
  $(pkg-config --cflags --libs Qt6Gui Qt6Qml) -o /tmp/test-eqs-locale
QT_FORCE_STDERR_LOGGING=1 /tmp/test-eqs-locale --source-6.7 "$candidate"
```

Observed: **27 PAM/IPC/navigation cases**, the virtual-output rotation test and
**18 date checks** passed on host Qt 6.11.2. Reintroducing the old PAM body in a
separate candidate fails with ASan heap-use-after-free. The default eqs5 tests
still pass, including the seven builder rejection checks and gesture-config
checks. The additional panel-state test loads the real tracker QML and drives
the real IPC implementation with synthetic socket events; it failed before
the bridge and now passes. Parsing the gesture QML is not a physical gesture test.

`--prepared` tests the supplied source as-is and reports its hashes. It does
not certify provenance, apply patches, validate package dependencies or replace
the default pinned-source checks. `--source-6.7` selects the new clock paths and
their upstream long-date format. `--installed` keeps the eqs5 resource layout;
`--installed-6.7` checks the new compiled resource paths, including Halcyon.

The rootless ARM64 build environment has Qt 6.10.2/KF 6.28 and a clean
`dpkg --audit`. Full Mobile compilation, its incremental panel/gesture rebuild
and staging completed. `test-upgrade-import.cpp` loaded the actual staged
SessionLock, WayfireIPC and RotationUtil modules with `LD_BIND_NOW=1` in that
environment; it never instantiates the lock singleton or calls real PAM.
The synthetic rotation sensor stays inactive under Wayfire; removing the guard
in a separately built control starts it and correctly fails the test.
The staged ARM64 libraries also passed all **18 compiled-resource date checks**
on Qt 6.10.2 (`test-locale --installed-6.7 /build/mobile-stage`), covering
`es_AR`, `en_US` and `de_DE`. The old resource layout correctly fails against
6.7; it was not silently redefined, so the existing eqs5 builder stays valid.

Clean-source replay with `patch --fuzz=0` reproduced **101 Mobile files and
four Workspace/source-packaging files** byte-for-byte, including executable
modes. Full `.deb` builds now use Debian's `hardening=+all`, separately from
the preliminary CMake build. Their current logs are:

- `.work/plasma-6.7.5-upgrade/mobile-package-build.log`
- `.work/plasma-6.7.5-upgrade/workspace-package-build.log`

**A successful preliminary build is not a completed package or device test.**

### Completed packages and libc compatibility

The final `plasma-mobile-wf_6.7.5-0+eqs1~pre1_arm64.deb` built successfully
(SHA-256 `b31fb962a6190992e203e466ae174f2e102eb2d0bad2785a94eb6fe3fd748064`).
The **extracted final package**, not just staging, passed the three ARM64
module imports, the synthetic rotation guard and all 18 compiled-resource date
checks. Selected entrypoints and lock/IPC/rotation/brightness libraries also
passed ARM64, RELRO, immediate binding and non-executable-stack checks.
The Panels D-Bus interface and Spanish catalogs are present.

Workspace's final `plasma-workspace_6.7.5-0+eqs1~pre1_arm64.deb` has SHA-256
`f40e79738aa37cc142fd2d482ff580eb90ed702b7104acaa4ea8fd2006cec422`.
All 17 runtime packages match the generated `.changes` inventory. The four
entrypoints pass ARM64/hardening/relocation checks, and 129 final library/plugin
ELFs pass `ldd -r` with the corresponding package set. `plasmashell --version`
reports 6.7.5. These are isolated ARM64 checks, not a physical screen test.

The isolated APT preflight found a real transitive conflict:

```text
installed libhybris-common1 → libc6 > 2.41 and < 2.42
new Qt 6.10.2 GLES          → libc6 >= 2.43
```

The old package's `mm.so`/`n.so` linkers import `__libc_fatal@GLIBC_PRIVATE`,
which generates the minor-version restriction. The live Wayfire process uses
`q.so`; that linker and `libhybris-common.so` have no such import. This does
**not** authorize removing the old package's dependency bound.

The narrow candidate is a rebuild of the same
[libhybris source](https://github.com/droidian/libhybris/tree/99bb6098f44c5890cda0ee40d665da15dacd472e)
against libc 2.43, retaining its source patches and Android 30 headers, rather
than adopting the `next.lindroid.drm` fork. All 825 source files were checked
against the pinned Git blobs. The complete ARM64 Debian build now passes.
[`upgrade-libhybris-glibc243.patch`](upgrade-libhybris-glibc243.patch) records
the three packaging changes: a local rebuild version, the upstream
[`9b543a4` Vulkan header fix](https://github.com/droidian/libhybris/commit/9b543a4e6e1efdb82e80bf95e1cdd000990bdf98),
and removal of an obsolete quilt entry already integrated in the base source.
That entry had caused `dpkg-source` to skip the new patch. Clean replay of all
three packaging files passes with zero fuzz.

Only **`libhybris-common1`**, not the other rebuilt libhybris packages, was installed:

- Version: `0.0.5.53-1+droidian0+z5+git20250520205628.99bb609.next.production+eqs1~glibc243`.
- Package SHA-256: `c006268a5e601a0d74460b4bea904be1ba31e0a0ae2bbb26b8e36c619d13eabe`.
- Its generated libc bounds are now `> 2.43` and `< 2.44`; no dependency was
  removed or forced.
- The final common/Q exported symbol sets match the old package exactly
  (128/526). Both load with `RTLD_NOW` in isolated ARM64 libc 2.43 and resolve
  the seven checked linker entrypoints. **This does not initialize Android or
  validate GPU rendering.**
- A libc/common1-only APT simulation passes with eight upgrades, one new package
  and no removals. The complete offline dependency simulation also passes:
  350 upgrades, 69 additions and six reviewed ABI-package replacements.

The rebuilt common1 is installed; fresh GPU-client validation is still pending.
The private preflight protects **111 installed hardware, Android, audio,
network and SSH packages**, with only the exact common1 replacement allowed as an exception.
The live APT sources and image inputs remain unchanged.

### Installation and maintenance checks

The network settings moved from Mobile to `plasma-nm` in this upgrade. The
old eqs5 package still owns the cellular, hotspot and Wi-Fi KCMs; the two new
payloads no longer overlap. Upstream's `Replaces` names `plasma-mobile`, not
`plasma-mobile-wf`, so the **unpack order matters**. The flat local repository
actually selected NM before Mobile, unlike the earlier online simulation. The installer first
uses `dpkg --unpack --no-triggers` on the new Mobile package to release its old
KCM files, then installs the complete, prevalidated set. Native APT needs
`--fix-broken` with that explicit set after the preparatory unpack. No bare
repair command, dependency-forcing or `--force-overwrite` is used.
The reverse path explicitly unpacks the old NM package before restoring old
Mobile. Native APT chose the wrong order there too; the guard rejected it.
Both native return-path simulations (356 old versions, then 355 after a
**synthetic** NM pre-unpack) pass with exactly 69 additions removed. No live
rollback or simulated-status write to the real dpkg database was performed.

The phone's `Origin: Droidian` priority of 1002 also selects older repository
versions over newer local builds. An isolated APT check confirms that a
package-specific priority of 990 prevents that downgrade while permitting
newer compatible repository versions. The scoped policy is now installed in
`/etc/apt/preferences.d/30-eqs-plasma67-userspace`. Native
`apt-get --simulate upgrade` selects **zero upgrades, downgrades or removals** with the current
indexes, including after a successful `apt-get update`. A fresh SSH login
also succeeds after the libc-triggered SSH restart.
`Acquire::Droidian::Version` remains `current`; no moving `next` source
or global priority change was applied. Only the adapted Mobile, Workspace,
common1 and the existing kernel packages are held. A future Qt ABI transition
still needs a compatible rebuild, not removal of those safeguards.

Baseline Qt/KDE/libc packages and 15 named session/startup configuration files
have been backed up privately, together with APT auto/manual state. The
verified local bundle contains all 419 forward packages and all 356 original
packages affected by the transaction. A return-path simulation against an
explicitly synthetic post-install package database restores those 356 versions
and removes exactly the 69 additions. It is not a physical rollback test. The libc upgrade invokes Debian's
service and systemd-manager re-execution hooks even if those packages are held; holds
are not a guarantee that maintenance scripts have no runtime effects.

## Remaining device validation

The complete bundle passed the native phone APT simulation before installation.
The next gate is the running shell, not another kernel or image build:

1. **Passed:** native install, `apt-get check` and empty `dpkg --audit`; all
   419 selected versions and six replacements match the plan. The other
   protected packages, kernel, Wayfire PID and named startup/rotation files
   were unchanged at package installation. Activation subsequently corrected
   only the launcher's KScreen selector. SSH and the Android container remain active. Native checks
   of the four installed entrypoints and all 18 compiled-resource dates also
   pass on the phone. These package checks alone do not certify the graphical session.
2. **Shell startup and KScreen initialization passed.** Check physical
   lock/unlock, navigation, rotation, keyboard, locale and
   graphics on the phone. Keep SSH recovery and the old packages available.
   Physical edge gestures cannot be certified by the host tests.
3. **Passed:** scoped priority 990 tested and installed; ordinary upgrade
   simulation selects zero changes. Keep the next Qt ABI transition staged
   until the local shell/Workspace/common1 builds are compatible.
4. Update image inputs only after target validation. The known-good image
   recipe remains eqs5; these development packages are not a new public image.
