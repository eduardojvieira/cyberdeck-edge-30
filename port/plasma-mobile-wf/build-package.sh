#!/usr/bin/env bash
# Offline package build inside the prepared, unprivileged ARM64 snapshot container.
set -euo pipefail

fail() { printf 'build-plasma-package: %s\n' "$*" >&2; exit 1; }
[[ $# == 2 ]] || fail 'usage: build-package.sh PINNED_SOURCE_TAR_GZ NEW_OUTPUT_DIRECTORY'
base=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly source_sha='559c81cc6a4f97b234802ced57fbc126defede7d155b4daf510ce735d6c6054f'
readonly patch_sha='6eaf2eca9669e28d3ed90762c0d19168a14d8e18822c54386a2d41f0832133a2'
readonly navigation_patch_sha='673e6c35af56e5d66e6b838e3187e4adbb4836f74025e79de158dbe0c0627f8d'
readonly rotation_patch_sha='7451143ee68a75cf9c6408791b0e4a177b5e62a4c0cee003b6719aee390b4695'
readonly locale_patch_sha='366baf21911628cb2339ddb26cb91ee5ad8f6b97e138aa640d66c7b69bcccacb'
readonly commit='69444e68c5d59fbcdeb79acc1a49313a4f114148'
readonly version='6.3.3-1~git20250414214107.69444e6.next.upgrade.6.3+eqs5'
archive=$(realpath -e -- "$1")
[[ ! -e $2 && ! -L $2 ]] || fail 'output must not already exist'
output=$(realpath -m -- "$2")
[[ -f $archive ]] || fail 'source archive is missing'
[[ $(sha256sum -- "$archive" | cut -d ' ' -f 1) == "$source_sha" ]] || fail 'source archive hash differs'
[[ $(sha256sum -- "$base/fix-session-safety.patch" | cut -d ' ' -f 1) == "$patch_sha" ]] || fail 'reviewed patch hash differs'
[[ $(sha256sum -- "$base/fix-navigation.patch" | cut -d ' ' -f 1) == "$navigation_patch_sha" ]] || fail 'reviewed navigation patch hash differs'
[[ $(sha256sum -- "$base/fix-rotation.patch" | cut -d ' ' -f 1) == "$rotation_patch_sha" ]] || fail 'reviewed rotation patch hash differs'
[[ $(sha256sum -- "$base/fix-locale.patch" | cut -d ' ' -f 1) == "$locale_patch_sha" ]] || fail 'reviewed locale patch hash differs'
[[ ! -e $output && ! -L $output ]] || fail 'output must not already exist'
[[ $(id -u) != 0 ]] || fail 'build as an unprivileged user, not root'
[[ -f /.dockerenv ]] || fail 'run inside the isolated build container, not on the phone or host'
[[ $(dpkg --print-architecture) == arm64 ]] || fail 'requires the ARM64 build environment, not the host compiler'
[[ $(apt-config shell snapshot Acquire::Droidian::Version) == "snapshot='101.20251130'" ]] || fail 'snapshot differs'

# The lock plugin links private Qt Wayland APIs; do not silently use host/next Qt.
while read -r package expected; do
    [[ $(dpkg-query -W -f='${Version}' "$package") == "$expected" ]] || fail "target ABI package differs: $package"
done <<'EOF'
libqt6core6t64 6.8.2+dfsg-9
libqt6gui6-gles 6.8.2+dfsg-9+droidian0+git20250817220106.4f83511.next.production
qt6-base-private-dev 6.8.2+dfsg-9
qt6-declarative-private-dev 6.8.2+dfsg-7
qt6-wayland-private-dev 6.8.2-4
EOF

mkdir -- "$output"
mkdir -- "$output/source"
tar -xzf "$archive" --strip-components=1 --no-same-owner -C "$output/source"
cd "$output/source"
for name in fix-session-safety.patch fix-navigation.patch fix-rotation.patch fix-locale.patch; do
    patch -p1 --batch --forward --fuzz=0 --dry-run -i "$base/$name"
    patch -p1 --batch --forward --fuzz=0 -i "$base/$name"
done
g++ -fPIC "$base/test-locale.cpp" $(pkg-config --cflags --libs Qt6Gui Qt6Qml) -o "$output/test-locale"
"$output/test-locale" "$output/source"
{
    cat <<EOF
plasma-mobile-wf ($version) rolling; urgency=medium

  * eqs: preserve PAM credential lifetime, validate conversations and bound
    complete Wayfire IPC frames without changing lock/unlock policy.
  * Route Home, Recents and Close through bounded Wayfire IPC, protect shell
    surfaces and deny navigation while locked or the focused app changes.
  * Connect the rotation quicksetting to Wayfire autorotate-iio with atomic
    persistence; the same output policy applies to the lock screen.
  * Preserve the actual HWCOMPOSER-1 transform in the same atomic update,
    so locking landscape does not reset to portrait on configuration reload.
  * Respect the date locale in every shell clock and translate Wayfire lock
    password/charging labels, including the compiled QML resources.
  * Build upstream $commit against
    Droidian snapshot 101.20251130. Pending device validation.

 -- eqs port maintainers <eqs-port@localhost>  Fri, 11 Sep 2026 15:00:00 +0000

EOF
    cat debian/changelog
} > debian/changelog.eqs
mv debian/changelog.eqs debian/changelog
dpkg-checkbuilddeps
export SOURCE_DATE_EPOCH=1789138800 TZ=UTC LC_ALL=C.UTF-8
export DEB_BUILD_OPTIONS=parallel=4 DPKG_DEB_THREADS_MAX=4
dpkg-buildpackage -b -us -uc
cd "$output"
for package in plasma-mobile-wf plasma-mobile-wf-tweaks plasma-mobile-wf-config-hwcomposer; do
    arch=all
    [[ $package != plasma-mobile-wf ]] || arch=arm64
    deb="${package}_${version}_${arch}.deb"
    [[ $(dpkg-deb -f "$deb" Package) == "$package" ]] || fail 'package name differs'
    [[ $(dpkg-deb -f "$deb" Version) == "$version" ]] || fail 'package version differs'
    [[ $(dpkg-deb -f "$deb" Architecture) == "$arch" ]] || fail 'package architecture differs'
done
mkdir inspection
dpkg-deb -x "plasma-mobile-wf_${version}_arm64.deb" inspection
"$output/test-locale" --installed "$output/inspection"
python3 - "$output/inspection/usr/share/locale/es/LC_MESSAGES/plasma_org.kde.plasma.private.mobileshell.mo" <<'PY'
import gettext
import sys
with open(sys.argv[1], 'rb') as source:
    catalog = gettext.GNUTranslations(source)
for text, expected in [('Password', 'Contraseña'), ('Charging: %1 mA', 'Cargando: %1 mA'),
                       ('Discharging: %1 mA', 'Descargando: %1 mA')]:
    assert catalog.gettext(text) == expected, text
print('PASS: packaged Spanish lockscreen catalog')
PY
for plugin in sessionlockplugin wayfireipcplugin screenrotationplugin; do
    mapfile -t libraries < <(find inspection/usr/lib/aarch64-linux-gnu/qt6/qml -type f -name "*${plugin}*.so")
    [[ ${#libraries[@]} == 1 ]] || fail "missing or ambiguous plugin: $plugin"
    readelf -h "${libraries[0]}" > "inspection/${plugin}-elf.txt"
    grep -Eq 'Class: +ELF64$' "inspection/${plugin}-elf.txt" || fail 'plugin is not ELF64'
    grep -Eq 'Machine: +AArch64$' "inspection/${plugin}-elf.txt" || fail 'plugin is not ARM64'
done
dpkg-query -W -f='${binary:Package}\t${Version}\t${Architecture}\n' | LC_ALL=C sort > BUILD-PACKAGES.tsv
{
    printf 'HOST ARM64/QEMU BUILD ONLY; NOT DEVICE VALIDATED OR A FLASH IMAGE\n'
    printf 'source_commit=%s\nsource_archive_sha256=%s\npatch_sha256=%s\n' "$commit" "$source_sha" "$patch_sha"
    printf 'navigation_patch_sha256=%s\n' "$navigation_patch_sha"
    printf 'rotation_patch_sha256=%s\n' "$rotation_patch_sha"
    printf 'locale_patch_sha256=%s\n' "$locale_patch_sha"
    printf 'builder_sha256=%s\n' "$(sha256sum -- "$base/build-package.sh" | cut -d ' ' -f 1)"
    printf 'version=%s\nsnapshot=101.20251130\nsource_date_epoch=%s\n' "$version" "$SOURCE_DATE_EPOCH"
} > BUILD-PROVENANCE.txt
sha256sum ./*.deb ./*.buildinfo BUILD-PACKAGES.tsv BUILD-PROVENANCE.txt > SHA256SUMS
printf 'PASS: ARM64 Debian packages built; device installation and validation still required\n'
