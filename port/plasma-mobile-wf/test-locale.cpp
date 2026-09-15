// Read-only Qt dates: SOURCE, --source-6.7 SOURCE, --installed ROOT or --installed-6.7 ROOT.
// g++ -fPIC test-locale.cpp $(pkg-config --cflags --libs Qt6Gui Qt6Qml) -o test-locale
// Installed mode reads the compiled QRCs, not merely the loose QML copies.
#include <QFile>
#include <QGuiApplication>
#include <QLibrary>
#include <QLocale>
#include <QQmlComponent>
#include <QQmlEngine>
#include <QRegularExpression>
#include <QDebug>
#include <memory>
#include <vector>

int main(int argc, char **argv)
{
    qputenv("QT_QPA_PLATFORM", "offscreen");
    QGuiApplication app(argc, argv);
    const QString option = argc == 3 ? QString::fromLocal8Bit(argv[1]) : QString();
    const bool installed = option == "--installed" || option == "--installed-6.7";
    const bool modern = option == "--source-6.7" || option == "--installed-6.7";
    if (argc != 2 && !installed && !modern) return 64;
    const QString root = QString::fromLocal8Bit(argv[installed || modern ? 2 : 1]);
    const QString module = "/usr/lib/aarch64-linux-gnu/qt6/qml/org/kde/plasma/private/mobileshell";
    std::vector<std::unique_ptr<QLibrary>> libraries;
    if (installed) {
        QStringList paths{module + "/libmobileshellplugin.so", module + "/sessionlockplugin/libsessionlockplugin.so"};
        if (modern)
            paths.append("/usr/lib/aarch64-linux-gnu/qt6/plugins/plasma/applets/org.kde.plasma.mobile.homescreen.halcyon.so");
        for (const auto &path : paths) {
            auto lib = std::make_unique<QLibrary>(root + path);
            if (!lib->load()) { qCritical() << lib->errorString(); return 1; }
            libraries.push_back(std::move(lib));
        }
    }
    struct Case { const char *source; const char *installed; const char *format; const char *installed67 = nullptr; };
    const Case cases[] = {
        {"components/mobileshell/qml/statusbar/ClockText.qml", ":/org/kde/plasma/private/mobileshell/ClockText.qml", "ddd d MMMM"},
        {"components/mobileshell/qml/statusbar/StatusBar.qml", ":/org/kde/plasma/private/mobileshell/StatusBar.qml", "ddd d MMMM"},
        {"components/mobileshell/qml/actiondrawer/LandscapeContentContainer.qml", ":/org/kde/plasma/private/mobileshell/LandscapeContentContainer.qml", "ddd d MMMM",
         ":/org/kde/plasma/private/mobileshell/actiondrawer/private/NotificationDrawer.qml"},
        {"components/sessionlockplugin/qml/Main.qml", ":/org/kde/plasma/private/mobileshell/sessionlockplugin/Main.qml", nullptr},
        {"shell/contents/lockscreen/Clock.qml", "/usr/share/plasma/shells/org.kde.plasma.mobileshell/contents/lockscreen/Clock.qml", nullptr},
        // The eqs5 build disables Halcyon; 6.7 builds it as a compiled applet.
        {"containments/homescreens/halcyon/package/contents/ui/Clock.qml", nullptr, "ddd d MMM",
         ":/qt/qml/plasma/applet/org/kde/plasma/mobile/homescreen/halcyon/Clock.qml"},
    };
    int failures = 0;
    for (const auto &localeName : {"es_AR", "en_US", "de_DE"}) {
        const QLocale locale(localeName);
        QLocale::setDefault(locale);
        QQmlEngine engine;
        for (const auto &test : cases) {
            const char *resource = modern && test.installed67 ? test.installed67 : test.installed;
            if (installed && !resource) continue;
            QString sourcePath = QString::fromLatin1(test.source);
            if (modern) {
                sourcePath.replace("halcyon/package/contents/ui/", "halcyon/qml/");
                sourcePath.replace("actiondrawer/LandscapeContentContainer.qml", "actiondrawer/private/NotificationDrawer.qml");
            }
            QString path = installed ? QString::fromLatin1(resource) : root + '/' + sourcePath;
            if (installed && !path.startsWith(':')) path.prepend(root);
            QFile file(path);
            if (!file.open(QIODevice::ReadOnly)) { qCritical() << "Missing QML:" << path; return 1; }
            const QString text = QString::fromUtf8(file.readAll());
            const auto match = QRegularExpression("text: ([^\\n]*(?:formatDate|toLocaleDateString)[^\\n]*)").match(text);
            if (!match.hasMatch()) { qCritical() << "Missing date expression:" << path; return 1; }
            QQmlComponent component(&engine);
            component.setData((QStringLiteral(
                "import QtQml\nQtObject {\n"
                "property date when: new Date(2026, 8, 11, 12, 0, 0)\n"
                "property var timeSource: ({data: {Local: {DateTime: when}}})\n"
                "property var source: timeSource\n"
                "property var clockSource: ({dateTime: when})\n"
                "property var topPanel: ({currentDT: when})\n"
                "property string result: ") + match.captured(1) + "\n}").toUtf8(), QUrl("file:///eqs-date-test.qml"));
            std::unique_ptr<QObject> object(component.create());
            if (!object || component.isError()) { qCritical() << component.errors(); return 1; }
            const QString actual = object->property("result").toString();
            const QDate date(2026, 9, 11);
            const QString expected = test.format && !modern ? locale.toString(date, QString::fromLatin1(test.format))
                                                : locale.toString(date, QLocale::LongFormat);
            if (actual != expected) {
                qCritical().noquote() << "FAIL:" << localeName << sourcePath << actual << "expected" << expected;
                ++failures;
            } else {
                qInfo().noquote() << "PASS:" << localeName << sourcePath << actual;
            }
        }
    }
    qInfo() << "Qt" << qVersion() << (installed ? "packaged resources" : "source expressions") << "failures:" << failures;
    return failures ? 1 : 0;
}
