// Import the packaged ARM64 singleton and exercise it only on a temporary INI.
#include <QGuiApplication>
#include <QScreen>
#include <qpa/qplatformscreen.h>
#include <qpa/qwindowsysteminterface.h>
#include <QFile>
#include <QFileInfo>
#include <QTemporaryDir>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QDebug>
#include <memory>
class PhoneScreen : public QPlatformScreen {
public:
    QString name() const override { return QStringLiteral("HWCOMPOSER-1"); }
    QRect geometry() const override { return QRect(0, 0, 1080, 2400); }
    int depth() const override { return 32; }
    QImage::Format format() const override { return QImage::Format_ARGB32; }
    Qt::ScreenOrientation orientation() const override { return Qt::InvertedLandscapeOrientation; }
};
int main(int argc, char **argv) {
    if (argc != 2) return 64;
    qputenv("QT_QPA_PLATFORM", "minimal");
    qputenv("QT_QPA_PLATFORMTHEME", "");
    QGuiApplication app(argc, argv);
    auto *panel = new PhoneScreen;
    QWindowSystemInterface::handleScreenAdded(panel);
    if (QString::fromLatin1(qVersion()) != QStringLiteral("6.8.2")) return 1;
    const QString root = QFileInfo(QString::fromLocal8Bit(argv[1])).canonicalFilePath();
    if (root.isEmpty() || !QFileInfo::exists(root + "/org/kde/plasma/quicksetting/screenrotation/libscreenrotationplugin.so")) return 1;
    QTemporaryDir temp;
    if (!temp.isValid()) return 1;
    const QString config = temp.path() + "/wayfire.ini";
    QFile file(config);
    if (!file.open(QIODevice::WriteOnly)) return 1;
    file.write("[autorotate-iio]\nlock_rotation = true\n[output:HWCOMPOSER-1]\ntransform = auto\n"); file.close();
    qputenv("WAYFIRE_CONFIG_FILE", config.toUtf8());
    QQmlEngine engine;
    engine.addImportPath(root);
    QQmlComponent component(&engine);
    component.setData(R"(import QtQml
import org.kde.plasma.quicksetting.screenrotation 1.0
QtObject {
 property bool present: ScreenRotationUtil.available
 property bool rotating: ScreenRotationUtil.autoScreenRotationEnabled
 function enable() { ScreenRotationUtil.autoScreenRotationEnabled = true }
 function disable() { ScreenRotationUtil.autoScreenRotationEnabled = false }
})", QUrl("file:///eqs-rotation-import.qml"));
    std::unique_ptr<QObject> object(component.create());
    if (!object || component.isError()) { qCritical() << component.errors(); return 1; }
    if (!object->property("present").toBool() || object->property("rotating").toBool()) return 1;
    if (!QMetaObject::invokeMethod(object.get(), "enable")) return 1;
    app.processEvents(); app.processEvents();
    if (!file.open(QIODevice::ReadOnly) || file.readAll() != "[autorotate-iio]\nlock_rotation = false\n[output:HWCOMPOSER-1]\ntransform = 90\n") return 1;
    file.close();
    QWindowSystemInterface::handleScreenOrientationChange(panel->screen(), Qt::LandscapeOrientation);
    app.processEvents();
    if (!QMetaObject::invokeMethod(object.get(), "disable")) return 1;
    app.processEvents(); app.processEvents();
    if (!file.open(QIODevice::ReadOnly) || file.readAll() != "[autorotate-iio]\nlock_rotation = true\n[output:HWCOMPOSER-1]\ntransform = 270\n") return 1;
    QWindowSystemInterface::handleScreenRemoved(panel);
    qInfo() << "PASS: packaged ARM64 singleton preserves both landscape transforms; virtual output, not HIL";
}
