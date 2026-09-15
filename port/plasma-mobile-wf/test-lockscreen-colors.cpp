// Palette regression, not a real lock/PAM invocation. Source or final QRC payload.
// g++ -fPIC test-lockscreen-colors.cpp $(pkg-config --cflags --libs Qt6Quick Qt6QuickControls2) -o test-lockscreen-colors
// ./test-lockscreen-colors --source SOURCE light|dark
// ./test-lockscreen-colors --installed ROOT light|dark
#include <QFile>
#include <QColor>
#include <QGuiApplication>
#include <QLibrary>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QRegularExpression>
#include <QTemporaryDir>
#include <QDebug>
#include <memory>
#include <vector>

int main(int argc, char **argv)
{
    if (argc != 4 || (QByteArray(argv[1]) != "--source" && QByteArray(argv[1]) != "--installed")
        || (QByteArray(argv[3]) != "light" && QByteArray(argv[3]) != "dark")) return 64;
    const bool installed = QByteArray(argv[1]) == "--installed";
    const bool dark = QByteArray(argv[3]) == "dark";
    const QString root = QString::fromLocal8Bit(argv[2]);
    QTemporaryDir config;
    if (!config.isValid()) return 1;
    QFile globals(config.path() + "/kdeglobals");
    if (!globals.open(QIODevice::WriteOnly)) return 1;
    globals.write(QByteArray("[Colors:Window]\nForegroundNormal=") + (dark ? "239,240,241" : "54,54,54")
        + "\nBackgroundNormal=" + (dark ? "51,51,51" : "239,240,241")
        + "\n[Colors:Complementary]\nForegroundNormal=239,240,241\nBackgroundNormal=51,51,51\n");
    globals.close();
    qputenv("XDG_CONFIG_HOME", config.path().toUtf8());
    qputenv("QT_QPA_PLATFORM", "offscreen");
    qputenv("QT_QPA_PLATFORMTHEME", "kde");
    QQuickStyle::setStyle("org.kde.desktop");
    QGuiApplication app(argc, argv);
    std::vector<std::unique_ptr<QLibrary>> libraries;
    if (installed) {
        const QString module = "/usr/lib/aarch64-linux-gnu/qt6/qml/org/kde/plasma/private/mobileshell/";
        for (const auto &name : {"libmobileshellplugin.so", "sessionlockplugin/libsessionlockplugin.so"}) {
            auto lib = std::make_unique<QLibrary>(root + module + name);
            if (!lib->load()) { qCritical() << lib->errorString(); return 1; }
            libraries.push_back(std::move(lib));
        }
    }
    struct Case { const char *source; const char *resource; const char *type; const char *boundary; };
    const Case cases[] = {
        {"components/sessionlockplugin/qml/Main.qml", ":/org/kde/plasma/private/mobileshell/sessionlockplugin/Main.qml", "Item", "property var lastBrightness"},
        {"components/mobileshell/qml/wayfiretweaks/LockScreenSplash.qml", ":/org/kde/plasma/private/mobileshell/LockScreenSplash.qml", "Window", "property var lockText"},
    };
    for (const auto &test : cases) {
        QFile file(installed ? QString::fromLatin1(test.resource) : root + '/' + test.source);
        if (!file.open(QIODevice::ReadOnly)) { qCritical() << file.fileName(); return 1; }
        const QString source = QString::fromUtf8(file.readAll());
        const auto end = source.indexOf(QString::fromLatin1(test.boundary));
        if (end < 0) return 1;
        QString declarations;
        auto matches = QRegularExpression("^\\s*Kirigami\\.Theme\\.(?:inherit|colorSet):[^\\n]+", QRegularExpression::MultilineOption)
                           .globalMatch(source.left(end));
        while (matches.hasNext()) declarations += matches.next().captured() + '\n';
        const auto colorBinding = QRegularExpression("\\n\\s*color: ([^\\n]+)").match(source.mid(source.indexOf("    Label {")));
        const QString labelColor = QByteArray(test.type) == "Window" && colorBinding.hasMatch()
            ? "color: " + colorBinding.captured(1).replace("lsWindow.", "scope.") + '\n' : QString();
        // Evaluate the real root palette declarations with real Kirigami/desktop
        // controls. Do not instantiate the lock singleton, sensors or PAM.
        const QString fields = declarations +
            "property color foreground: label.color\n"
            "property color themedText: Kirigami.Theme.textColor\n"
            "property color backdrop: Kirigami.Theme.backgroundColor\n"
            "property bool isolated: !Kirigami.Theme.inherit && Kirigami.Theme.colorSet === Kirigami.Theme.Complementary\n"
            "Controls.Label { id: label; text: 'Bloqueado'\n" + labelColor + "}\n";
        const QString qml = QStringLiteral(
            "import QtQuick\nimport QtQuick.Window\nimport QtQuick.Controls as Controls\n"
            "import org.kde.kirigami as Kirigami\nWindow { width: 200; height: 100;\n")
            + (QByteArray(test.type) == "Item" ? "property alias tested: scope\nItem { id: scope\n" + fields + "}\n"
                                               : "id: scope\nproperty alias tested: scope\n" + fields) + "}";
        QQmlEngine engine;
        QQmlComponent component(&engine);
        component.setData(qml.toUtf8(), QUrl("file:///eqs-lock-colors.qml"));
        std::unique_ptr<QObject> object(component.create());
        if (!object || component.isError()) { qCritical() << component.errors(); return 1; }
        auto *window = qobject_cast<QQuickWindow *>(object.get());
        if (!window) return 1;
        window->show();
        app.processEvents();
        auto *tested = object->property("tested").value<QObject *>();
        if (!tested) return 1;
        const QColor foreground = tested->property("foreground").value<QColor>();
        const QColor themed = tested->property("themedText").value<QColor>();
        const QColor backdrop = tested->property("backdrop").value<QColor>();
        if (!tested->property("isolated").toBool() || foreground != QColor(239, 240, 241)
            || themed != foreground || backdrop != QColor(51, 51, 51)) {
            qCritical() << "FAIL" << test.source << "isolated" << tested->property("isolated")
                        << "label" << foreground << "theme" << themed << "background" << backdrop;
            return 1;
        }
        qInfo() << "PASS" << test.source << argv[3] << "local complementary palette" << foreground << backdrop;
    }
    return 0;
}
