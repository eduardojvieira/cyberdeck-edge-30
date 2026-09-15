// SPDX-License-Identifier: GPL-2.0-or-later
// Host regression: real source bodies, fake PAM, real Qt Unix sockets. No phone.
#include <QCoreApplication>
#include <QEventLoop>
#include <QTimer>
#include <QLocalServer>
#include <QtEndian>
#include <QString>
#include <QByteArray>
#include <QQmlComponent>
#include <QQmlEngine>
#include <security/pam_appl.h>
#include <pwd.h>
#include <cassert>
#include <cstdlib>
#include <cstring>
#include <memory>

// PAM is deliberately not linked. These fakes cannot authenticate a host user.
struct pam_handle { pam_conv conv; };
static pam_handle fakeHandle;
static int startResult, authResult, accountResult, endResult, endCalls;
static bool multiplePrompts, invalidPrompts;
static int allocations, failAllocation;
static QByteArray expectedPassword;
static void *fakeCalloc(size_t count, size_t size) {
    return ++allocations == failAllocation ? nullptr : calloc(count, size);
}
static char *fakeStrdup(const char *value) {
    return ++allocations == failAllocation ? nullptr : strdup(value);
}
static passwd *fakeGetpwnam(const char *name) {
    static passwd user{};
    user.pw_name = const_cast<char *>("synthetic-user");
    return strcmp(name, user.pw_name) ? nullptr : &user;
}
static void freeResponses(int count, pam_response *responses) {
    if (!responses) return;
    for (int i = 0; i < count; ++i) free(responses[i].resp);
    free(responses);
}
static int fakePamStart(const char *, const char *, const pam_conv *conv, pam_handle_t **handle) {
    if (startResult) return startResult;
    fakeHandle.conv = *conv;
    *handle = &fakeHandle;
    return PAM_SUCCESS;
}
static int fakePamAuthenticate(pam_handle_t *handle, int) {
    assert(handle == &fakeHandle);
    const pam_message prompts[] = {{PAM_PROMPT_ECHO_OFF, "secret"},
        {PAM_PROMPT_ECHO_ON, "user"}, {PAM_TEXT_INFO, "info"}, {PAM_ERROR_MSG, "error"}};
    const pam_message *messages[]{&prompts[0], &prompts[1], &prompts[2], &prompts[3]};
    pam_response *responses = nullptr;
    const int count = multiplePrompts ? 4 : 1;
    const int result = handle->conv.conv(count, messages, &responses, handle->conv.appdata_ptr);
    if (failAllocation) {
        assert(result == PAM_BUF_ERR && responses == nullptr);
        return result;
    }
    assert(result == PAM_SUCCESS);
    assert(responses && QByteArray(responses[0].resp) == expectedPassword);
    if (multiplePrompts) {
        assert(QByteArray(responses[1].resp) == "synthetic-user");
        assert(responses[2].resp == nullptr && responses[3].resp == nullptr);
        for (int i = 0; i < count; ++i) assert(responses[i].resp_retcode == 0);
    }
    freeResponses(count, responses);
    if (invalidPrompts) {
        const pam_message invalid{999, "unsupported"};
        const pam_message *bad[]{&prompts[0], &invalid};
        responses = nullptr;
        assert(handle->conv.conv(2, bad, &responses, handle->conv.appdata_ptr) != PAM_SUCCESS);
        assert(responses == nullptr); // Includes cleanup after the first allocation.
        assert(handle->conv.conv(0, messages, &responses, handle->conv.appdata_ptr) != PAM_SUCCESS);
        assert(handle->conv.conv(PAM_MAX_NUM_MSG + 1, messages, &responses, handle->conv.appdata_ptr) != PAM_SUCCESS);
        assert(handle->conv.conv(1, nullptr, &responses, handle->conv.appdata_ptr) != PAM_SUCCESS);
        assert(handle->conv.conv(1, messages, nullptr, handle->conv.appdata_ptr) != PAM_SUCCESS);
        const pam_message *missing[]{nullptr};
        assert(handle->conv.conv(1, missing, &responses, handle->conv.appdata_ptr) != PAM_SUCCESS);
        assert(handle->conv.conv(1, messages, &responses, nullptr) != PAM_SUCCESS);
    }
    return authResult;
}
static int fakePamAccount(pam_handle_t *handle, int) {
    assert(handle == &fakeHandle);
    return accountResult;
}
static int fakePamEnd(pam_handle_t *handle, int) {
    assert(handle == &fakeHandle);
    ++endCalls;
    return endResult;
}
class SessionLock {
public:
    pam_handle_t *m_pamh = nullptr;
    int authenticate(QString username, QString password);
    int finish_pam_with(int value);
};
#define getpwnam fakeGetpwnam
#define pam_start fakePamStart
#define pam_authenticate fakePamAuthenticate
#define pam_acct_mgmt fakePamAccount
#define pam_end fakePamEnd
#define calloc fakeCalloc
#define strdup fakeStrdup
#include "auth-under-test.inc"
#undef getpwnam
#undef pam_start
#undef pam_authenticate
#undef pam_acct_mgmt
#undef pam_end
#undef calloc
#undef strdup
#include "wayfireipc.cpp"

static void pump() {
    QEventLoop loop;
    QTimer::singleShot(20, &loop, &QEventLoop::quit);
    loop.exec();
}
static QByteArray frame(const QByteArray &payload) {
    QByteArray result(4, '\0');
    qToLittleEndian<quint32>(payload.size(), result.data());
    return result + payload;
}
struct Connection {
    QLocalServer server;
    std::unique_ptr<WayfireIPC> client;
    QLocalSocket *peer;
    int power = 0, idle = 0, mapped = 0;
    Connection() {
        const auto name = qEnvironmentVariable("EQS_TEST_RUNTIME") + "/s-" + QString::number(QCoreApplication::applicationPid());
        assert(server.listen(name));
        qputenv("WAYFIRE_SOCKET", name.toUtf8());
        client = std::make_unique<WayfireIPC>();
        if (!server.hasPendingConnections()) assert(server.waitForNewConnection(1000));
        peer = server.nextPendingConnection();
        assert(peer);
        QObject::connect(client.get(), &WayfireIPC::pwrKeyStateChanged,
                         [this](int value) { power += value ? 1 : 10; });
        QObject::connect(client.get(), &WayfireIPC::idleTimout, [this] { ++idle; });
        QObject::connect(client.get(), &WayfireIPC::viewMapped,
                         [this](const QString &app) { assert(app == "synthetic-app"); ++mapped; });
        pump();
        peer->readAll(); // Initial watch requests, not events under test.
    }
    void send(const QByteArray &data) {
        assert(peer->write(data) == data.size());
        peer->flush();
        pump();
    }
};

static QList<QJsonObject> requests(QLocalSocket *socket) {
    pump();
    QByteArray bytes = socket->readAll();
    QList<QJsonObject> result;
    while (!bytes.isEmpty()) {
        assert(bytes.size() >= 4);
        auto size = qFromLittleEndian<quint32>(bytes.constData());
        assert(size > 0 && size <= 1024 * 1024 && bytes.size() >= 4 + size);
        const auto doc = QJsonDocument::fromJson(bytes.mid(4, size));
        assert(doc.isObject());
        result.append(doc.object());
        bytes.remove(0, 4 + size);
    }
    return result;
}

static bool navigate(Connection &c, const char *method) {
    bool accepted = false;
    assert(QMetaObject::invokeMethod(c.client.get(), method, Q_RETURN_ARG(bool, accepted)));
    return accepted;
}

static QLocalSocket *navigationPeer(Connection &c) {
    for (int i = 0; i < 25 && !c.server.hasPendingConnections(); ++i) pump();
    auto *peer = c.server.nextPendingConnection();
    assert(peer);
    const auto query = requests(peer);
    assert(query.size() == 1 && query[0]["method"] == "window-rules/list-views");
    return peer;
}

int main(int argc, char **argv) {
    QCoreApplication app(argc, argv);
    assert(argc == 2);
    const QByteArray mode(argv[1]);
    if (mode.startsWith("pam-")) {
        SessionLock lock;
        multiplePrompts = mode == "pam-conversation" || mode == "pam-oom-response";
        invalidPrompts = mode == "pam-invalid-conversation";
        if (mode == "pam-oom-array") failAllocation = 1;
        if (mode == "pam-oom-response") failAllocation = 3;
        expectedPassword = QByteArray(80, 'x'); // Synthetic, forces heap ownership.
        if (mode == "pam-null-input") {
            const QString nul = QStringLiteral("x") + QChar::Null + QStringLiteral("y");
            assert(lock.authenticate("synthetic-user", nul) != PAM_SUCCESS);
            assert(lock.authenticate(nul, "synthetic") != PAM_SUCCESS);
            assert(endCalls == 0 && lock.m_pamh == nullptr);
            return 0;
        }
        if (mode == "pam-start-failure") startResult = PAM_SYSTEM_ERR;
        if (mode == "pam-auth-failure") authResult = PAM_AUTH_ERR;
        if (mode == "pam-account-failure") accountResult = PAM_ACCT_EXPIRED;
        if (mode == "pam-end-failure") endResult = PAM_SYSTEM_ERR;
        const int result = lock.authenticate("synthetic-user", QString::fromUtf8(expectedPassword));
        const bool fail = startResult || authResult || accountResult || endResult || failAllocation;
        assert((result != PAM_SUCCESS) == fail);
        assert(endCalls == (startResult ? 0 : 1));
        assert(lock.m_pamh == nullptr);
        if (fail) return 0;
        // Repeated attempts must not keep or close an already-ended PAM handle.
        assert(lock.authenticate("synthetic-user", QString::fromUtf8(expectedPassword)) == PAM_SUCCESS);
        assert(endCalls == 2 && lock.m_pamh == nullptr);
        return 0;
    }
    Connection connection;
    if (mode == "nav-panel-state") {
        assert(connection.client->property("activeAppFullscreen").isValid());
        qmlRegisterSingletonInstance("org.kde.plasma.private.mobileshell.wayfireipcplugin", 254, 0,
                                     "WayfireIPC", connection.client.get());
        QQmlEngine engine;
        QQmlComponent component(&engine, QUrl::fromLocalFile(qEnvironmentVariable("EQS_TEST_TRACKER")));
        std::unique_ptr<QObject> tracker(component.create());
        if (!tracker || component.isError()) qFatal("Tracker QML: %s", qPrintable(component.errorString()));
        const auto check = [&](bool showing, bool fullscreen) {
            assert(tracker->property("showingWindow").toBool() == showing);
            assert(tracker->property("isCurrentWindowFullscreen").toBool() == fullscreen);
            assert(tracker->property("windowCount").toInt() == (showing ? 1 : 0));
        };
        QJsonObject view{{"id", 1}, {"pid", 123}, {"app-id", "app"}, {"role", "toplevel"},
                         {"layer", "workspace"}, {"mapped", true}, {"fullscreen", false}};
        const auto send = [&](const char *event) {
            connection.send(frame(QJsonDocument(QJsonObject{{"event", event}, {"view", view}}).toJson()));
        };
        check(false, false);
        send("view-focused"); check(true, false);
        view["fullscreen"] = true;
        send("view-geometry-changed"); check(true, true); // no focus change needed
        view["id"] = 2; view["fullscreen"] = false;
        send("view-geometry-changed"); check(true, true); // another app cannot replace focus
        view["id"] = 1; view["minimized"] = true;
        send("view-minimized"); check(false, false);
        view["minimized"] = false; view["fullscreen"] = true;
        send("view-focused"); check(true, true);
        send("view-unmapped"); check(false, false);
        view["role"] = "desktop-environment"; view["layer"] = "overlay";
        send("view-focused"); check(false, false); // panels/lock never count as apps
        view["role"] = "toplevel"; view["layer"] = "workspace";
        send("view-focused"); check(true, true);
        connection.peer->disconnectFromServer(); pump();
        check(false, false); // fail visible rather than retaining a hidden panel state
        return 0;
    }
    if (mode.startsWith("nav-")) {
        if (mode == "nav-guard") {
            assert(!navigate(connection, "showHome"));
            assert(!navigate(connection, "showOverview"));
            assert(!navigate(connection, "closeActive"));
            assert(!connection.server.hasPendingConnections());
        }
        assert(connection.client->setProperty("navigationEnabled", true));
        if (mode == "nav-overview") {
            assert(navigate(connection, "showOverview"));
            const auto sent = requests(connection.peer);
            assert(sent.size() == 1 && sent[0]["method"] == "scale/toggle_all");
            return 0;
        }
        if (mode == "nav-close" || mode == "nav-focus-change") {
            connection.send(frame(R"({"event":"view-focused","view":{"id":1,"role":"toplevel","layer":"workspace","app-id":"app","pid":123,"mapped":true}})"));
            assert(connection.client->property("hasActiveApp").toBool());
        }
        const char *method = (mode == "nav-close" || mode == "nav-focus-change") ? "closeActive" : "showHome";
        assert(navigate(connection, method));
        auto *peer = navigationPeer(connection);
        assert(!navigate(connection, method)); // no overlapping/stale actions
        if (mode == "nav-timeout") {
            for (int i = 0; i < 125 && peer->state() != QLocalSocket::UnconnectedState; ++i) pump();
            assert(peer->state() == QLocalSocket::UnconnectedState);
            assert(requests(peer).isEmpty());
            connection.send(frame("{\"event\":\"power-key-pressed\"}"));
            assert(connection.power == 1); // RPC timeout must not kill power/idle subscription
            return 0;
        }
        QByteArray views = R"([
          {"id":1,"role":"toplevel","layer":"workspace","app-id":"app","pid":123,"mapped":true,"activated":true,"minimized":false},
          {"id":2,"role":"toplevel","layer":"workspace","app-id":"minimized","pid":124,"mapped":true,"activated":true,"minimized":true},
          {"id":3,"role":"desktop-environment","layer":"overlay","app-id":"dock","pid":125,"mapped":true,"activated":true},
          {"id":4,"role":"toplevel","layer":"workspace","app-id":"gone","pid":126,"mapped":false,"activated":true},
          {"id":-1,"role":"toplevel","layer":"workspace","app-id":"bad-id","pid":127,"mapped":true,"activated":true},
          {"id":1.5,"role":"toplevel","layer":"workspace","app-id":"fractional","pid":128,"mapped":true,"activated":true},
          {"id":7,"role":"toplevel","layer":"workspace","app-id":"shell-dialog","pid":SELF_PID,"mapped":true,"activated":true}
        ])";
        views.replace("SELF_PID", QByteArray::number(QCoreApplication::applicationPid()));
        if (mode == "nav-bad-reply") views = "{\"error\":\"unavailable\"}";
        auto reply = frame(views);
        peer->write(reply.left(7)); peer->flush(); pump();
        assert(requests(peer).isEmpty()); // incomplete snapshot cannot trigger actions
        if (mode == "nav-guard") assert(connection.client->setProperty("navigationEnabled", false));
        if (mode == "nav-focus-change") {
            connection.send(frame(R"({"event":"view-focused","view":{"id":9,"role":"toplevel","layer":"workspace","app-id":"another-app","pid":129,"mapped":true}})"));
        }
        peer->write(reply.mid(7)); peer->flush(); pump();
        const auto sent = requests(peer);
        if (mode == "nav-guard" || mode == "nav-bad-reply" || mode == "nav-focus-change") {
            assert(sent.isEmpty());
        } else {
            assert(sent.size() == 1);
            const auto data = sent[0]["data"].toObject();
            if (mode == "nav-close") {
                assert(sent[0]["method"] == "window-rules/close-view" && data["id"].toInt() == 1);
            } else {
                assert(sent[0]["method"] == "wm-actions/set-minimized");
                assert(data["view_id"].toInt() == 1 && data["state"].toBool());
                assert(navigate(connection, "showHome"));
                auto *again = navigationPeer(connection);
                views.replace("\"minimized\":false", "\"minimized\":true");
                again->write(frame(views)); again->flush(); pump();
                assert(requests(again).isEmpty()); // repeated Home never restores apps
            }
        }
        assert(connection.peer->state() == QLocalSocket::ConnectedState);
        return 0;
    }
    const auto down = frame("{\"event\":\"power-key-pressed\"}");
    const auto up = frame("{\"event\":\"power-key-released\"}");
    if (mode == "ipc-ownership") {
        assert(connection.client->findChildren<QLocalSocket *>().size() == 1);
    } else if (mode == "ipc-fragmented") {
        for (int split = 1; split < down.size(); ++split) {
            connection.send(down.left(split));
            assert(connection.power == split - 1);
            connection.send(down.mid(split));
            assert(connection.power == split);
        }
    } else if (mode == "ipc-complete") {
        connection.send(down + up + frame("{\"event\":\"idle-timeout\"}") +
                        frame("{\"event\":\"view-mapped\",\"view\":{\"app-id\":\"synthetic-app\"}}"));
        assert(connection.power == 11 && connection.idle == 1 && connection.mapped == 1);
    } else if (mode == "ipc-invalid-length" || mode == "ipc-zero-length") {
        QByteArray header(4, '\0');
        qToLittleEndian<quint32>(mode == "ipc-zero-length" ? 0 : 1024 * 1024 + 1, header.data());
        connection.send(header);
        assert(connection.peer->state() == QLocalSocket::UnconnectedState);
        assert(connection.power == 0);
    } else if (mode == "ipc-invalid-json" || mode == "ipc-json-array") {
        connection.send(frame(mode == "ipc-json-array" ? "[]" : "not JSON"));
        assert(connection.peer->state() == QLocalSocket::UnconnectedState);
        assert(connection.power == 0);
    } else if (mode == "ipc-eof") {
        connection.send(down.left(7));
        connection.peer->disconnectFromServer();
        pump();
        assert(connection.power == 0);
    } else if (mode == "ipc-batch") {
        QByteArray batch;
        for (int i = 0; i < 100; ++i) batch += down;
        connection.send(batch);
        for (int i = 0; i < 20 && connection.power < 100; ++i) pump();
        assert(connection.power == 100);
    } else if (mode == "ipc-max-length") {
        QByteArray payload = "{\"event\":\"power-key-pressed\"}";
        payload += QByteArray(1024 * 1024 - payload.size(), ' ');
        connection.send(frame(payload));
        for (int i = 0; i < 50 && connection.power == 0; ++i) pump();
        assert(connection.power == 1);
    } else {
        assert(false && "unknown case");
    }
    return 0;
}
