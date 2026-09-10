// ARM64 container smoke test, not authentication, compositor or device evidence.
// g++ test-plugin-import.cpp $(pkg-config --cflags --libs Qt6Gui Qt6Qml) -o test-plugin-import
// LD_BIND_NOW=1 ./test-plugin-import EXTRACTED_PACKAGE/usr/lib/aarch64-linux-gnu/qt6/qml
#include <QFileInfo>
#include <QGuiApplication>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QDebug>
#include <memory>

int main(int argc, char **argv)
{
    if (argc != 2 || !QFileInfo::exists("/.dockerenv"))
        return 64;
    qputenv("QT_QPA_PLATFORM", "offscreen");
    QGuiApplication app(argc, argv);
    if (QString::fromLatin1(qVersion()) != QStringLiteral("6.8.2"))
        return 1;
    const QString root = QFileInfo(QString::fromLocal8Bit(argv[1])).canonicalFilePath();
    QQmlEngine engine;
    engine.addImportPath(root);
    const char *plugins[] = {"sessionlockplugin", "wayfireipcplugin"};
    const char *types[] = {"SessionLock", "WayfireIPC"};
    for (int i = 0; i < 2; ++i) {
        const QString name = QString::fromLatin1(plugins[i]);
        const QString library = root + "/org/kde/plasma/private/mobileshell/" + name + "/lib" + name + ".so";
        if (root.isEmpty() || !QFileInfo::exists(library)) {
            qCritical() << "Required package plugin is absent:" << library;
            return 1;
        }
        const QByteArray uri = "org.kde.plasma.private.mobileshell." + name.toLatin1();
        QQmlComponent component(&engine);
        component.setData("import QtQml\nimport " + uri + " 254.0\nQtObject {}", QUrl("file:///eqs-import-probe.qml"));
        std::unique_ptr<QObject> object(component.create());
        if (!object || component.isError() || qmlTypeId(uri.constData(), 254, 0, types[i]) < 0) {
            qCritical() << component.errors();
            return 1;
        }
        // Register/resolve the type without constructing the singleton or trying a PIN.
        qInfo() << "PASS: QML plugin import and type registration" << library;
    }
}
