#!/usr/bin/env python3
"""Host Qt virtual-screen check. --prepared tests an already patched source as-is."""
from pathlib import Path
import argparse
import hashlib
import os
import shlex
import shutil
import subprocess
import tempfile

base = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--prepared', action='store_true')
args = parser.parse_args()
source = args.source / 'quicksettings/screenrotation'
with tempfile.TemporaryDirectory(prefix='eqs-rotation-') as temp:
    work = Path(temp)
    target = work / 'quicksettings/screenrotation'
    target.mkdir(parents=True)
    for name in ('screenrotationutil.cpp', 'screenrotationutil.h'):
        shutil.copyfile(source / name, target / name)
        if args.prepared:
            print(f'SOURCE SHA256 {hashlib.sha256((target / name).read_bytes()).hexdigest()} quicksettings/screenrotation/{name}', flush=True)
    if not args.prepared:
        subprocess.run(['patch', '-p1', '--batch', '--fuzz=0', '-i', str(base / 'fix-rotation.patch')], cwd=work, check=True)
    flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Core', 'Qt6Gui'], text=True))
    includes = Path(subprocess.check_output(['pkg-config', '--variable=includedir', 'Qt6Gui'], text=True).strip())
    version = subprocess.check_output(['pkg-config', '--modversion', 'Qt6Gui'], text=True).strip()
    flags += ['-I'+str(includes / 'QtGui' / version), '-I'+str(includes / 'QtGui' / version / 'QtGui'),
              '-I'+str(includes / 'QtCore' / version), '-I'+str(includes / 'QtCore' / version / 'QtCore')]
    qt = subprocess.check_output(['pkg-config', '--variable=libexecdir', 'Qt6Core'], text=True).strip()
    subprocess.run([str(Path(qt) / 'moc'), str(target / 'screenrotationutil.h'), '-o', str(work / 'moc.cpp')], check=True)
    (work / 'check.cpp').write_text(r'''
#include "screenrotationutil.h"
#include <QGuiApplication>
#include <QScreen>
#include <qpa/qplatformscreen.h>
#include <qpa/qwindowsysteminterface.h>
#include <QFile>
#include <QSaveFile>
#include <QTemporaryDir>
#include <QElapsedTimer>
#include <QThread>
#include <cassert>
class PhoneScreen : public QPlatformScreen {
public:
    QString name() const override { return QStringLiteral("HWCOMPOSER-1"); }
    QRect geometry() const override { return QRect(0, 0, 1080, 2400); }
    int depth() const override { return 32; }
    QImage::Format format() const override { return QImage::Format_ARGB32; }
    Qt::ScreenOrientation orientation() const override { return Qt::PortraitOrientation; }
};
int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    auto *panel = new PhoneScreen;
    QWindowSystemInterface::handleScreenAdded(panel);
    QTemporaryDir dir;
    const QString path = dir.path() + "/wayfire.ini";
    qputenv("WAYFIRE_CONFIG_FILE", path.toUtf8());
    auto write = [&](QByteArray data) { QSaveFile f(path); assert(f.open(QIODevice::WriteOnly)); assert(f.write(data)==data.size()); assert(f.commit()); };
    auto read = [&]() { QFile f(path); assert(f.open(QIODevice::ReadOnly)); return f.readAll(); };
    auto wait = [&]() { QElapsedTimer t; t.start(); while(t.elapsed()<100) { app.processEvents(); QThread::msleep(1); } };
    const QByteArray output = "[output:HWCOMPOSER-1]\ntransform = normal\n";
    const QByteArray raw = "[decoration]\ncolor = \\#112233ff\n[autorotate-iio]\nlock_rotation = true\n[core]\nplugins = a b c\n" + output;
    write(raw);
    ScreenRotationUtil rotation;
    // Qt's real screen events, no accelerometer or desktop session mutation.
    for (const auto &test : {std::pair{Qt::InvertedLandscapeOrientation, QByteArray("90")},
                            std::pair{Qt::LandscapeOrientation, QByteArray("270")},
                            std::pair{Qt::InvertedPortraitOrientation, QByteArray("180")},
                            std::pair{Qt::PortraitOrientation, QByteArray("normal")}}) {
        write("[output:HWCOMPOSER-1]\ntransform = auto\n[autorotate-iio]\nlock_rotation = false\n"); wait();
        QWindowSystemInterface::handleScreenOrientationChange(panel->screen(), test.first); wait();
        assert(panel->screen()->orientation() == test.first);
        rotation.setAutoScreenRotationEnabled(false); wait();
        const QByteArray expected = "[output:HWCOMPOSER-1]\ntransform = " + test.second + "\n[autorotate-iio]\nlock_rotation = true\n";
        assert(read() == expected);
        rotation.setAutoScreenRotationEnabled(false); wait(); assert(read() == expected);
        rotation.setAutoScreenRotationEnabled(true); wait();
        assert(read() == QByteArray(expected).replace("lock_rotation = true", "lock_rotation = false"));
        ScreenRotationUtil restarted;
        assert(restarted.isAvailable() && restarted.autoScreenRotationEnabled());
    }
    // Enabling must also preserve the actual orientation, not an old INI value.
    write(raw); wait();
    QWindowSystemInterface::handleScreenOrientationChange(panel->screen(), Qt::LandscapeOrientation); wait();
    rotation.setAutoScreenRotationEnabled(true); wait();
    assert(read() == QByteArray(raw).replace("transform = normal", "transform = 270").replace("lock_rotation = true", "lock_rotation = false"));
    QWindowSystemInterface::handleScreenOrientationChange(panel->screen(), Qt::PortraitOrientation); wait();
    write(raw); wait();
    assert(rotation.isAvailable());
    assert(!rotation.autoScreenRotationEnabled());
    rotation.setAutoScreenRotationEnabled(true); wait();
    assert(rotation.autoScreenRotationEnabled());
    assert(read() == QByteArray(raw).replace("lock_rotation = true", "lock_rotation = false"));
    rotation.setAutoScreenRotationEnabled(false); wait();
    assert(read() == raw); assert(!rotation.autoScreenRotationEnabled());
    write(QByteArray(raw).replace("true", "false")); wait();
    assert(rotation.autoScreenRotationEnabled()); // watch survives atomic replacement
    write(raw); wait(); assert(!rotation.autoScreenRotationEnabled());
    write("[core]\nplugins = test\n"); wait();
    assert(rotation.autoScreenRotationEnabled());
    rotation.setAutoScreenRotationEnabled(false); wait();
    assert(read() == "[core]\nplugins = test\n\n[autorotate-iio]\nlock_rotation = true\n\n" + output);
    write("[autorotate-iio]\nother = yes\n[core]\nplugins = test\n"); wait();
    rotation.setAutoScreenRotationEnabled(false); wait();
    assert(read() == "[autorotate-iio]\nother = yes\nlock_rotation = true\n[core]\nplugins = test\n\n" + output);
    // Missing options at the same EOF must stay in their own INI sections.
    write("[autorotate-iio]\n"); wait();
    rotation.setAutoScreenRotationEnabled(false); wait();
    assert(read() == "[autorotate-iio]\nlock_rotation = true\n\n" + output);
    write("[output:HWCOMPOSER-1]\n"); wait();
    rotation.setAutoScreenRotationEnabled(false); wait();
    assert(read() == "[output:HWCOMPOSER-1]\n\ntransform = normal\n[autorotate-iio]\nlock_rotation = true\n");
    for (const auto &bad : {QByteArray("[autorotate-iio]\nlock_rotation = maybe\n"),
         QByteArray("[autorotate-iio]\nlock_rotation = true\nlock_rotation = false\n"),
         QByteArray("[autorotate-iio]\n[autorotate-iio]\n"), QByteArray(131073, 'x'),
         QByteArray("[output:HWCOMPOSER-1]\ntransform = flipped\n"),
         QByteArray("[output:HWCOMPOSER-1]\ntransform = 90\ntransform = 270\n"),
         QByteArray("[output:HWCOMPOSER-1]\n[output:HWCOMPOSER-1]\n"),
         QByteArray("[core]\0bad", 11)}) {
        write(bad); wait(); assert(!rotation.isAvailable());
        rotation.setAutoScreenRotationEnabled(true); wait(); assert(read() == bad);
    }
    write(raw); wait(); assert(rotation.isAvailable());
    assert(QFile::setPermissions(dir.path(), QFileDevice::ReadOwner | QFileDevice::ExeOwner));
    rotation.setAutoScreenRotationEnabled(true); wait();
    assert(read() == raw); assert(!rotation.autoScreenRotationEnabled());
    assert(QFile::setPermissions(dir.path(), QFileDevice::ReadOwner | QFileDevice::WriteOwner | QFileDevice::ExeOwner));
    assert(QFile::remove(path)); wait(); assert(!rotation.isAvailable());
    rotation.setAutoScreenRotationEnabled(true); wait(); assert(!QFile::exists(path));
    const QString real = dir.path() + "/real";
    { QFile f(real); assert(f.open(QIODevice::WriteOnly)); f.write(raw); }
    assert(QFile::link(real, path)); wait(); assert(!rotation.isAvailable());
    rotation.setAutoScreenRotationEnabled(true); wait(); assert(read() == raw);
    QWindowSystemInterface::handleScreenRemoved(panel);
    assert(QFile::remove(path)); write(raw); wait();
    rotation.setAutoScreenRotationEnabled(true); wait(); assert(read() == raw); // no actual panel: refuse
}
''')
    subprocess.run(['clang++', '-std=c++17', '-O0', '-g', '-fsanitize=address,undefined', '-I'+str(target),
                    str(target/'screenrotationutil.cpp'), str(work/'moc.cpp'), str(work/'check.cpp'),
                    *flags, '-o', str(work/'check')], check=True)
    # No font database/desktop theme needed: keep LSan enabled for our objects.
    subprocess.run([str(work/'check')], check=True, timeout=15,
                   env={**os.environ, 'QT_QPA_PLATFORM': 'minimal', 'QT_QPA_PLATFORMTHEME': ''})
    print('PASS: four live Qt orientations, lock/unlock preservation, reload, missing-key insertion and refusal paths; host virtual output only')
