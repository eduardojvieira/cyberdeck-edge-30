// ARM64/Qt 6.10.2 import check inside the isolated upgrade build root, not HIL.
// g++ -fPIC test-upgrade-import.cpp $(pkg-config --cflags --libs Qt6Gui Qt6Qml Qt6Sensors) -o test-upgrade-import
// LD_BIND_NOW=1 ./test-upgrade-import STAGED_QML_DIRECTORY
#include <QFileInfo>
#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QDebug>
#include <QOrientationSensor>
#include <QSensorBackend>
#include <QSensorManager>
#include <memory>

static int sensorStarts = 0;
class TestOrientationBackend : public QSensorBackend {
public:
    explicit TestOrientationBackend(QSensor *sensor) : QSensorBackend(sensor) { setReading<QOrientationReading>(nullptr); }
    void start() override { ++sensorStarts; }
    void stop() override {}
};
class TestOrientationFactory : public QSensorBackendFactory {
public:
    QSensorBackend *createBackend(QSensor *sensor) override { return new TestOrientationBackend(sensor); }
};

int main(int argc, char **argv)
{
#ifndef __aarch64__
    return 64;
#endif
    if (argc != 2 || !QFileInfo::exists("/.eqs-plasma-build-root"))
        return 64;
    qputenv("QT_QPA_PLATFORM", "offscreen");
    qputenv("KDE_NO_KWIN", "1");
    QGuiApplication app(argc, argv);
    if (QString::fromLatin1(qVersion()) != QStringLiteral("6.10.2"))
        return 1;
    const QString root = QFileInfo(QString::fromLocal8Bit(argv[1])).canonicalFilePath();
    if (root.isEmpty()) return 1;
    TestOrientationFactory factory;
    QSensorManager::registerBackend(QOrientationSensor::sensorType, "eqs-test", &factory);
    QSensorManager::setDefaultBackend(QOrientationSensor::sensorType, "eqs-test");
    {
        QOrientationSensor probe;
        if (!probe.start() || sensorStarts != 1) { qCritical() << "Synthetic sensor did not start"; return 1; }
        probe.stop();
    }
    sensorStarts = 0;
    QQmlEngine engine;
    engine.addImportPath(root);
    const char *plugins[] = {"sessionlockplugin", "wayfireipcplugin", "rotationplugin"};
    const char *types[] = {"SessionLock", "WayfireIPC", "RotationUtil"};
    for (int i = 0; i < 3; ++i) {
        const QString name = QString::fromLatin1(plugins[i]);
        const QString library = root + "/org/kde/plasma/private/mobileshell/" + name + "/lib" + name + ".so";
        if (!QFileInfo::exists(library)) { qCritical() << "Missing candidate plugin:" << library; return 1; }
        const QByteArray uri = "org.kde.plasma.private.mobileshell." + name.toLatin1();
        QQmlComponent component(&engine);
        component.setData("import QtQml\nimport " + uri + " 254.0\nQtObject {}", QUrl("file:///eqs-upgrade-import.qml"));
        std::unique_ptr<QObject> object(component.create());
        const int type = qmlTypeId(uri.constData(), 254, 0, types[i]);
        if (!object || component.isError() || type < 0) { qCritical() << component.errors(); return 1; }
        if (i == 2) {
            // Construct only RotationUtil, never the lock singleton or real PAM.
            QObject *rotation = engine.singletonInstance<QObject *>(type);
            if (!rotation || rotation->property("showRotationButton").toBool() ||
                rotation->property("deviceRotation").toInt() != 0 ||
                rotation->property("currentRotation").toInt() != 0 || sensorStarts != 0) {
                qCritical() << "KWin rotation policy ran under Wayfire; sensor starts:" << sensorStarts;
                return 1;
            }
            if (!QMetaObject::invokeMethod(rotation, "rotateToSuggestedRotation") || sensorStarts != 0) return 1;
        }
        qInfo() << "PASS: ARM64 Qt" << qVersion() << "import/type registration" << library;
    }
    qInfo() << "PASS: Wayfire keeps the KScreen rotation-suggestion sensor inactive (synthetic backend, not HIL)";
}
