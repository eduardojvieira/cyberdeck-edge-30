# QScreen compatibility for Plasma 6.7 on eqs

This is a **read-only backend**, not another compositor. It restores the
QScreen backend removed from libkscreen, using the **6.7.4 private backend ABI**.
Wayfire remains responsible for output modes, scale and rotation.

The backend sources come from KDE/libkscreen
[`6b53bd7`](https://github.com/KDE/libkscreen/tree/6b53bd7bdd3982a42bf518f6cc524b2b4a8ee855/backends/qscreen)
(v6.3.4). The private `AbstractBackend` header comes from
[`33432e4`](https://github.com/KDE/libkscreen/blob/33432e490d0adc6c1ded65d2d24cf0ec7f24da0f/src/abstractbackend.h)
(v6.7.4). `sources.json` pins all nine files by commit and SHA-256.
Do not copy the old `.so`: `setConfig()` changed from `QString` to
`QFuture<std::expected<void, QString>>` despite the unchanged public SONAME.

`compat.patch` adapts that API and output priorities, rejects writes, preserves
200% scaling, and forwards actual Qt geometry/orientation changes to
`ConfigMonitor`. Its portrait-panel rotation mapping is **eqs-specific**;
this is not support for arbitrary displays or mirrored outputs.

## Prepare the sources

Run from the repository root, outside the network-isolated build SDK:

```sh
python3 - <<'PY'
import hashlib, json, urllib.request
from pathlib import Path
recipe = Path('port/plasma-mobile-wf/qscreen-6.7')
source = Path('.work/qscreen-6.7-source')
source.mkdir()  # refuses to overwrite existing work
(source / 'src').mkdir()
for item in json.loads((recipe / 'sources.json').read_text()):
    data = urllib.request.urlopen(item['url'], timeout=30).read()
    assert hashlib.sha256(data).hexdigest() == item['sha256'], item['path']
    (source / 'src' / Path(item['path']).name).write_bytes(data)
PY
patch --batch --fuzz=0 -p1 -d .work/qscreen-6.7-source \
  < port/plasma-mobile-wf/qscreen-6.7/compat.patch
```

## Build and test in the ARM64 SDK

Requires the prepared ARM64 Qt **6.10.2**, Qt GUI private development headers,
KF6Screen **6.7.4**, `libkf6screen8 4:6.7.4-1`, CMake, C++, CPack and dpkg tools.
The private Qt headers are used **only by the synthetic screen test**.
No phone, host desktop, Docker daemon or privileged installation is needed.
Adapt `/recipe`, `/source` and `/build/qscreen` to the SDK's mount paths:

```sh
export SOURCE_DATE_EPOCH=1789430400 LC_ALL=C.UTF-8
cmake -S /recipe -B /build/qscreen -G 'Unix Makefiles' \
  -DEQS_QSCREEN_SOURCE_DIR=/source \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=/usr
cmake --build /build/qscreen -j4
cd /build/qscreen
QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=2 QT_PLUGIN_PATH="$PWD/plugins" \
  KSCREEN_BACKEND=QScreen KSCREEN_BACKEND_INPROCESS=1 LD_BIND_NOW=1 \
  ./test-qscreen "$PWD/plugins/kf6/kscreen/KSC_QScreen.so" --virtual
cpack -G DEB
sha256sum eqs-kscreen-qscreen_6.7.4-0+eqs2_arm64.deb
```

CPack derives shared-library dependencies; exact additional dependencies on
`libkscreen-bin` and `libkf6screen8` prevent unnoticed private-ABI changes.
The package installs only the plugin and its license. It has no maintainer
script, service restart, output-changing command or flash operation.

**Observed RED/GREEN:** old source fails against the new virtual-method API;
API-only restoration fails the 200% geometry check; the old filename-form
selector fails `GetConfigOperation`. The adapted backend passes those checks.
The synthetic test also covers all four orientations, different workarea vs
screen geometry, live `ConfigMonitor` updates and removal of a screen. A
native read-only probe on eqs confirms 1200×540 logical / 2400×1080 displayed
pixels at scale 2. Synthetic rotations are not a physical lock/unlock test.

## Activation and rollback

The selector is **`KSCREEN_BACKEND=QScreen`**, not `KSC_QScreen.so`.
Use `KSCREEN_BACKEND_INPROCESS=1`. The filename is only for the loader/probe.
Both the future session launcher and the existing user-manager/transient
shell environment must agree; changing `/etc` does not change a running
process's environment. Activate through a controlled **shell-only** restart
after unlocking, preserving Wayfire and SSH. Do not interrupt a locked session.

The current Mobile `~pre2` package still ships the inherited filename-form
selectors in `startplasmamobile-wf`. The tested phone bypasses it through the
corrected `eqs-wayfire-session` override. Preserve that override; this addon
alone does not repair the packaged default launcher. See the
[launcher boundary](../UPGRADE-6.7.md#qscreen-backend-restored-and-activated).

For a native read-only test, run `test-qscreen` with the installed plugin path
inside the existing graphical user environment, **without `--virtual`**.
It creates no windows and refuses configuration writes. `--virtual` explicitly
requires the offscreen platform; it is not a target test.

The cohort rollback needs one preparatory step: simulate removal of
`eqs-kscreen-qscreen` with `apt-get --simulate --no-auto-remove remove` and
require **only that package** to be removed. Remove it only as part of the
prepared old-cohort restoration, before the old `libkscreen-bin` reclaims the
same plugin path. Then follow the separately validated Mobile/NM unpack order
in [UPGRADE-6.7.md](../UPGRADE-6.7.md). Do not leave Plasma 6.7 running with a
missing backend. No autoremove or unbounded distribution upgrade.
