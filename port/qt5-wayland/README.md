# Camera preview orientation on eqs

**Installed on the current phone, 10 September 2026; visual confirmation pending.** Qt5 loses the
90° preview compensation in landscape. The correction is a private
`libQt5WaylandClient.so.5`, selected **only by the Camera launcher**. No changes
to Wayfire, Plasma, touch calibration, sensor mounting angles or system Qt packages.

## Cause and scope

A native read-only probe on 10 September 2026 reported:

```text
HWCOMPOSER-1: logical 1200x540, physical 69x154 mm
nativeOrientation: PrimaryOrientation (unknown)
primaryOrientation: LandscapeOrientation
orientation: LandscapeOrientation
QtMultimedia autoOrientation angle: 0
portrait-native compensation: 90
```

[Qt5's orientation handler](https://github.com/qt/qtmultimedia/blob/5.15/src/multimedia/video/qvideooutputorientationhandler.cpp)
measures screen rotation from `nativeOrientation()`. QtWayland inherits the
unknown `PrimaryOrientation` default, which `QScreen::angleBetween()` resolves
using the **rotated logical geometry**. That is not the phone's native portrait
orientation. `fix-native-orientation.patch` supplies the native orientation
from the **untransformed wl_output mode**, the same reference already used by
QtWayland for its current orientation.

This keeps QtMultimedia's existing sensor-angle and front-camera mirror handling.
Both QML backends of Droidian Camera use `VideoOutput.autoOrientation`; no separate
QML rotation workaround is added. Saved JPEG orientation follows a different
AAL sensor path and is **not proved by this preview fix**. No photos or videos
were captured during diagnosis.

The launcher accepts the override only with the tested system package
`libqt5waylandclient5=5.15.15-3`. If APT changes it, the launcher warns and uses
system Qt instead of retaining an obsolete private override. No APT hold.

## Sources and reproduction

- Debian `qtwayland-opensource-src 5.15.15-3`, including **all Debian patches**.
  [Source descriptor](https://deb.debian.org/debian/pool/main/q/qtwayland-opensource-src/qtwayland-opensource-src_5.15.15-3.dsc).
- Original tarball SHA-256:
  `bd1b577ec2311c0f615ca4a21aeb108a0b1b5e112c94191ff709cec814599b51`.
- Debian tarball SHA-256:
  `80ed76b87807b7b6a20858f297d19fc8ae60c52addc7d97e1fec02b372324c48`.
- Droidian Camera `a0b51cd89ca73d7688d97ec42fc285c9997de8a7`;
  AAL `8f9043571fcc3cea6ddfa32314a2dbc53742e594` (unchanged).

Use an isolated ARM64 build environment with matching Qt 5.15.15 development
packages, QtWayland private headers/tools, the `qtwayland5` platform plugin and
Wayland development libraries. The existing `eqs-rotation-arm64` container was
reused; **do not install build dependencies on the phone**.

In a fresh unpacked Debian source tree, with its Debian patches already applied:

```sh
patch -p1 --fuzz=0 < /path/to/port/qt5-wayland/test-native-orientation.patch
(cd tests/auto/client/xdgoutput && QT_SELECT=qt5 qmake && make -j4)
# RED against the original installed QtWayland; expected nativeOrientation failure.
QT_QPA_PLATFORMTHEME= tests/auto/client/xdgoutput/tst_xdgoutput nativeOrientation

patch -p1 --fuzz=0 < /path/to/port/qt5-wayland/fix-native-orientation.patch
QT_SELECT=qt5 qmake QT_BUILD_PARTS-=examples QT_BUILD_PARTS-=tests
make -j4 sub-src-qmake_all
make -C src/qtwaylandscanner -j4
make -C src/client -j4
# GREEN must use the new library, not the stock one.
LD_LIBRARY_PATH="$PWD/lib" QT_QPA_PLATFORMTHEME= \
  tests/auto/client/xdgoutput/tst_xdgoutput
```

`test-native-orientation.patch` extends the existing mock compositor: a portrait
panel and a landscape-native monitor each undergo nine orientation transitions,
including both landscape directions and returns to portrait, at scale 2. The
Wayland server and outputs are synthetic; these are **not physical camera tests**.

Launcher checks: `python3 port/qt5-wayland/test-launcher.py` and
`sh -n port/qt5-wayland/droidian-camera`. Evidence and source archives are private
under `.work/eqs-camera-orientation/`.

**Results, 10 September:** the original library fails the native-orientation
assertion. The corrected library passes all **7 xdgoutput tests** in the ARM64
container and on the phone against a private mock Wayland server. Native mock
tests use `QT_WAYLAND_CLIENT_BUFFER_INTEGRATION=shm` to avoid EGL: the expected
missing-integration warning leaves software SHM windows, not a camera preview.
Without that test-only setting, libhybris requires an `android_wlegl` global
which the mock server does not provide. This is not a production launcher setting.

The separate **real Wayfire, no-window probe** uses normal integration: the
original QtMultimedia handler returns 0°, the candidate 90°, with the same
1200x540 display geometry. Native linkage is clean. The stripped ARM64 library
is 1,526,352 bytes, SHA-256
`bd71d40c74cf9dda7482b3227503cbacce7bd052457f0e94cffdd1cccc0c7bfb`.

## Installation boundary and user check

Installed with Eduardo's explicit approval: the library is under
`~/.local/opt/eqs-camera-qt5-5.15.15/lib/`, the launcher in `~/.local/bin/`, and
`droidian-camera.desktop` in `~/.local/share/applications/`. All destinations
were previously absent. The system camera binary, system Qt library, Wayfire
configuration and full package inventory remained unchanged; no reboot or flash.

The menu resolves the user launcher and KDE's application cache was refreshed.
A temporary copy of the **installed** launcher, replacing only its final exec
with the no-window probe, loaded the private library and produced the correct
90° compensation. The installed library also passed all 7 native mock-server
tests again. Camera was not opened, and no photos or videos were captured. Installation
evidence is in `~/.local/state/eqs-camera-orientation-20260910/install.5A6HVK/`
and `.work/eqs-camera-install/` on the PC.

Remove only those two user launch entries to revert, then refresh the application
cache; `/usr/bin/droidian-camera` always bypasses the override. The private library
does not affect other applications. This was installed on the current phone first. The cumulative image recipe
now also installs this exact library and launcher; see [image status](../../docs/RELEASE-20260910.md).
A new clean image still needs its own physical validation.

Close and reopen Camera. Check rear and front preview in
portrait, both landscape directions, and after switching cameras. Check one
saved photo separately. Visual orientation and saved-photo results remain
pending until tested; successful compilation alone is not acceptance.
