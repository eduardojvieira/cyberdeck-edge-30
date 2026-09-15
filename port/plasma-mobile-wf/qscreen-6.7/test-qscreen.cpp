// SPDX-License-Identifier: MIT
#include "abstractbackend.h"
#include <kscreen/config.h>
#include <kscreen/configmonitor.h>
#include <kscreen/getconfigoperation.h>
#include <kscreen/output.h>
#include <kscreen/mode.h>
#include <QGuiApplication>
#include <QPluginLoader>
#include <QScreen>
#include <QTimer>
#include <QDebug>
#include <QElapsedTimer>
#include <QThread>
#include <qpa/qplatformscreen.h>
#include <qpa/qwindowsysteminterface.h>

class PhoneScreen : public QPlatformScreen {
public:
    QString name() const override { return QStringLiteral("HWCOMPOSER-1"); }
    QRect geometry() const override { return QRect(0, 0, 1080, 2400); }
    int depth() const override { return 32; }
    QImage::Format format() const override { return QImage::Format_ARGB32; }
    Qt::ScreenOrientation orientation() const override { return Qt::PortraitOrientation; }
};

int main(int argc, char **argv)
{
    QGuiApplication app(argc, argv);
    if (argc != 2 && argc != 3) return 2;
    PhoneScreen *panel = nullptr;
    if (argc == 3) {
        if (QString::fromLocal8Bit(argv[2]) != "--virtual" || app.platformName() != "offscreen") return 2;
        panel = new PhoneScreen;
        QWindowSystemInterface::handleScreenAdded(panel, true);
    }
    QTimer::singleShot(8000, &app, [] { qFatal("QScreen probe timed out"); });
    for (auto *s : app.screens()) {
        qInfo() << "Qt screen" << s->name() << s->geometry() << "scale" << s->devicePixelRatio()
                << "orientations current/native/primary" << s->orientation() << s->nativeOrientation() << s->primaryOrientation();
    }
    QPluginLoader loader(QString::fromLocal8Bit(argv[1]));
    auto *backend = qobject_cast<KScreen::AbstractBackend *>(loader.instance());
    if (!backend || backend->name() != "QScreen" || !backend->isValid()) { qCritical() << loader.errorString(); return 1; }
    auto config = backend->config();
    if (!config || config->outputs().size() != app.screens().size()
        || config->supportedFeatures().testFlag(KScreen::Config::Feature::Writable)) return 1;
    for (auto *s : app.screens()) {
        bool found = false;
        for (const auto &o : config->outputs()) {
            if (o->name() != s->name()) continue;
            found = true;
            if (!o->currentMode()) return 1;
            qInfo() << "KScreen" << o->name() << o->geometry() << o->scale() << o->rotation() << o->currentMode()->size();
            if (o->scale() != s->devicePixelRatio() || config->logicalSizeForOutputInt(*o) != s->size() || !o->isEnabled()) return 1;
        }
        if (!found) return 1;
    }
    for (const auto &input : {KScreen::ConfigPtr{}, config}) {
        const auto result = backend->setConfig(input);
        if (!result.isFinished() || result.result().has_value() || result.result().error().isEmpty()) return 1;
    }
    auto *op = new KScreen::GetConfigOperation(KScreen::ConfigOperation::NoEDID);
    QObject::connect(op, &KScreen::ConfigOperation::finished, &app, [&](auto *operation) {
        if (operation->hasError() || !operation->config() || operation->config()->outputs().size() != app.screens().size()) {
            qCritical() << operation->errorString(); app.exit(1); return;
        }
        if (panel) {
            const auto live = operation->config();
            KScreen::ConfigMonitor::instance()->addConfig(live);
            auto wait = [&] { QElapsedTimer timer; timer.start(); while (timer.elapsed() < 150) { app.processEvents(); QThread::msleep(2); } };
            for (const auto &test : {std::pair{Qt::PortraitOrientation, KScreen::Output::None},
                                    std::pair{Qt::InvertedLandscapeOrientation, KScreen::Output::Left},
                                    std::pair{Qt::InvertedPortraitOrientation, KScreen::Output::Inverted},
                                    std::pair{Qt::LandscapeOrientation, KScreen::Output::Right}}) {
                const bool portrait = test.first == Qt::PortraitOrientation || test.first == Qt::InvertedPortraitOrientation;
                const QRect rect(0, 0, portrait ? 1080 : 2400, portrait ? 2400 : 1080);
                QWindowSystemInterface::handleScreenGeometryChange(panel->screen(), rect, rect.adjusted(0, 20, 0, -30));
                QWindowSystemInterface::handleScreenOrientationChange(panel->screen(), test.first);
                wait();
                auto output = live->primaryOutput();
                qInfo() << "VIRTUAL expected" << test.first << test.second << panel->screen()->geometry() << panel->screen()->devicePixelRatio()
                        << "got" << (output ? output->name() : QString()) << (output ? output->rotation() : KScreen::Output::None)
                        << (output ? live->logicalSizeForOutputInt(*output) : QSize()) << (output ? output->scale() : 0);
                if (!output || output->name() != "HWCOMPOSER-1" || output->rotation() != test.second
                    || live->logicalSizeForOutputInt(*output) != panel->screen()->size()
                    || output->scale() != panel->screen()->devicePixelRatio()) qFatal("live QScreen rotation/scale mismatch");
            }
            QWindowSystemInterface::handleScreenRemoved(panel);
            wait();
            for (const auto &output : live->outputs()) if (output->name() == "HWCOMPOSER-1") qFatal("stale removed output");
            qInfo() << "PASS: four synthetic rotations, workarea excluded, ConfigMonitor updates and screen removal";
        }
        qInfo() << "PASS: QScreen loaded, metadata matches Qt, writes rejected, GetConfigOperation succeeds";
        app.exit(0);
    });
    return app.exec();
}
