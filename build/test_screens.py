#!/usr/bin/env python3
"""Load the Cathode lock screen and Shut Down dialog offscreen with stand-ins
for Plasma's greeter APIs, drive them like a user would, and save screenshots
for light and dark mode.

Usage: test_screens.py SHELL_CONTENTS_DIR OUT_DIR
"""
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, QRect, Qt, QPointF
from PySide6.QtGui import QGuiApplication, QKeyEvent, QPalette, QColor, QMouseEvent, QFont
from PySide6.QtQml import QQmlPropertyMap
from PySide6.QtQuick import QQuickView, QQuickItem

SHELL, OUT = sys.argv[1], sys.argv[2]
STUBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teststubs")
app = QGuiApplication([])
app.setFont(QFont("Tahoma", 9))
results = []


def check(name, ok):
    results.append((name, bool(ok)))


class Recorder(QObject):
    def __init__(self):
        super().__init__()
        self.calls = []

    @Slot(str)
    def record(self, what):
        self.calls.append(what)


class Authenticator(QObject):
    failed = Signal()
    succeeded = Signal()
    busyChanged = Signal()
    infoMessageChanged = Signal()
    errorMessageChanged = Signal()
    promptForSecretChanged = Signal()

    def __init__(self):
        super().__init__()
        self._busy = False
        self.responses = []

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(bool, constant=True)
    def graceLocked(self):
        return False

    @Property(str, notify=infoMessageChanged)
    def infoMessage(self):
        return ""

    @Property(str, notify=errorMessageChanged)
    def errorMessage(self):
        return ""

    @Property(str, notify=promptForSecretChanged)
    def promptForSecret(self):
        return "Password:"

    @Slot()
    def startAuthenticating(self):
        self._busy = True
        self.busyChanged.emit()
        self.promptForSecretChanged.emit()

    @Slot(str)
    def respond(self, text):
        self.responses.append(text)
        self._busy = False
        self.busyChanged.emit()
        (self.succeeded if text == "hunter2" else self.failed).emit()


def pump():
    for _ in range(5):
        app.processEvents()


def type_text(view, text):
    for ch in text:
        for t in (QKeyEvent.KeyPress, QKeyEvent.KeyRelease):
            app.sendEvent(view, QKeyEvent(t, 0, Qt.NoModifier, ch))
    pump()


def key(view, k):
    for t in (QKeyEvent.KeyPress, QKeyEvent.KeyRelease):
        app.sendEvent(view, QKeyEvent(t, k, Qt.NoModifier))
    pump()


def click(view, name):
    item = view.rootObject().findChild(QQuickItem, name)
    assert item is not None, name
    if not item.isVisible():
        return False
    pos = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    for t in (QMouseEvent.MouseButtonPress, QMouseEvent.MouseButtonRelease):
        app.sendEvent(view, QMouseEvent(t, pos, pos, Qt.LeftButton, Qt.LeftButton if t == QMouseEvent.MouseButtonPress else Qt.NoButton, Qt.NoModifier))
    pump()
    return True


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schemes  # noqa: E402

SCHEME = "cathode"


def set_dark(dark):
    pal = QPalette()
    if dark:
        for role, c in [(QPalette.Window, "#3a3a3a"), (QPalette.WindowText, "#e8e8e8"), (QPalette.Base, "#2a2a2a"), (QPalette.Text, "#e8e8e8"), (QPalette.Button, "#3a3a3a")]:
            pal.setColor(role, QColor(c))
    pal.setColor(QPalette.Highlight, QColor(schemes.BY_SLUG[SCHEME]["sel"]))
    app.setPalette(pal)


keep = []


def lock_test(dark):
    tag = SCHEME + "-" + ("dark" if dark else "light")
    set_dark(dark)
    auth, rec, quit_called = Authenticator(), Recorder(), []
    keep.extend([auth, rec])
    v = QQuickView()
    keep.append(v)
    v.engine().addImportPath(STUBS)
    ctx = v.rootContext()
    ctx.setContextProperty("authenticator", auth)
    ctx.setContextProperty("sessionRecorder", rec)
    ctx.setContextProperty("kscreenlocker_userName", "Zach")
    v.engine().quit.connect(lambda: quit_called.append(True))
    v.setResizeMode(QQuickView.SizeRootObjectToView)
    v.resize(1280, 720)
    v.setSource(QUrl.fromLocalFile(os.path.join(SHELL, "lockscreen", "LockScreen.qml")))
    assert v.status() == QQuickView.Ready, [e.toString() for e in v.errors()]
    v.show()
    v.requestActivate()
    root = v.rootObject()
    root.setProperty("locked", True)
    pump()
    sc = schemes.BY_SLUG[SCHEME]
    want = sc["desk_dark"] if dark else sc["desk_light"]
    check(f"[{tag}] desktop colour follows the scheme", v.grabWindow().pixelColor(4, 4).name() == want)
    logo = v.rootObject().findChild(QObject, "lockLogo")
    check(f"[{tag}] logo follows the scheme", logo is not None and logo.property("source").toString().endswith(f"/logos/{SCHEME}.png")
          and logo.property("progress") == 1.0)

    type_text(v, "wrong")
    key(v, Qt.Key_Return)
    check(f"[{tag}] wrong password rejected", auth.responses == ["wrong"] and not quit_called
          and "incorrect" in root.property("notification"))
    v.grabWindow().save(os.path.join(OUT, f"lockscreen-{tag}.png"))

    check(f"[{tag}] Sleep button suspends", click(v, "sleepButton") and rec.calls == ["suspend"])
    rec.calls.clear()

    click(v, "shutdownButton")
    check(f"[{tag}] Shut Down... opens options", root.property("page") == "shutdown")
    v.grabWindow().save(os.path.join(OUT, f"lockscreen-shutdown-{tag}.png"))
    key(v, Qt.Key_Down)               # Shut down -> Restart
    key(v, Qt.Key_Return)
    check(f"[{tag}] Restart sent without hidden prompt", rec.calls == ["reboot:0"] and root.property("page") == "unlock")
    rec.calls.clear()

    click(v, "shutdownButton")
    click(v, "cancelButton")
    check(f"[{tag}] Cancel goes back, does nothing", rec.calls == [] and root.property("page") == "unlock")

    click(v, "logoffButton")
    check(f"[{tag}] Log Off... asks first", root.property("page") == "logoff" and rec.calls == [])
    v.grabWindow().save(os.path.join(OUT, f"lockscreen-logoff-{tag}.png"))
    click(v, "okButton")
    check(f"[{tag}] confirmed Log Off logs out", rec.calls == ["logout:0"])
    rec.calls.clear()

    type_text(v, "hunter2")
    key(v, Qt.Key_Return)
    check(f"[{tag}] right password unlocks", auth.responses[-1] == "hunter2" and bool(quit_called))
    v.close()


def logout_test(dark):
    tag = SCHEME + "-" + ("dark" if dark else "light")
    set_dark(dark)
    for sdtype_name, expect in [("ShutdownTypeDefault", "Shut down"), ("ShutdownTypeReboot", "Restart"),
                                ("ShutdownTypeLogout", "Log out")]:
        v = QQuickView()
        st = QQmlPropertyMap(v)
        for i, n in enumerate(["ShutdownTypeDefault", "ShutdownTypeNone", "ShutdownTypeReboot", "ShutdownTypeHalt", "ShutdownTypeLogout"]):
            st.insert(n, i)
        spd = QQmlPropertyMap(v)
        spd.insert("SuspendState", True)
        spd.insert("HibernateState", False)
        spd.insert("StandbyState", True)
        keep.extend([v, st, spd])
        ctx = v.rootContext()
        ctx.setContextProperty("maysd", True)
        ctx.setContextProperty("sdtype", st.value(sdtype_name))
        ctx.setContextProperty("ShutdownType", st)
        ctx.setContextProperty("spdMethods", spd)
        ctx.setContextProperty("canLogout", True)
        ctx.setContextProperty("softwareUpdatePending", False)
        ctx.setContextProperty("screenGeometry", QRect(0, 0, 1280, 720))
        v.resize(1280, 720)
        v.setSource(QUrl.fromLocalFile(os.path.join(SHELL, "logout", "Logout.qml")))
        assert v.status() == QQuickView.Ready, [e.toString() for e in v.errors()]
        v.show()
        v.requestActivate()
        pump()
        root = v.rootObject()
        fired = []
        for sig in ["haltRequested", "rebootRequested", "logoutRequested", "cancelRequested", "lockScreenRequested"]:
            getattr(root, sig).connect(lambda s=sig: fired.append(s))
        root.suspendRequested.connect(lambda m: fired.append(f"suspend{m}"))
        labels = [o["label"] for o in root.property("options").toVariant()]
        check(f"[{tag}] {sdtype_name} preselects {expect}", labels[root.property("selected")] == expect)
        if sdtype_name == "ShutdownTypeDefault":
            v.grabWindow().save(os.path.join(OUT, f"logout-{tag}.png"))
            root.forceActiveFocus()
            pump()
            key(v, Qt.Key_Down)
            key(v, Qt.Key_Return)
            check(f"[{tag}] logout dialog: Down + Enter = Restart", fired == ["rebootRequested"])
            fired.clear()
            key(v, Qt.Key_Escape)
            check(f"[{tag}] logout dialog: Esc cancels", fired == ["cancelRequested"])
        v.close()


for SCHEME, dark in [("cathode", False), ("cathode", True), ("brick", False), ("sunset", True), ("slate", False)]:
    lock_test(dark)
    logout_test(dark)

ok = True
for name, passed in results:
    print(("PASS " if passed else "FAIL ") + name)
    ok &= passed
sys.exit(0 if ok else 1)
