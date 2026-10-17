// Test stand-in for Plasma's SessionManagement: records what the UI asks for.
import QtQuick
QtObject {
    property bool canShutdown: true
    property bool canReboot: true
    property bool canLogout: true
    property bool canSuspend: true
    property bool canHibernate: false
    property bool canSwitchUser: true
    function requestShutdown(mode) { sessionRecorder.record("shutdown:" + mode) }
    function requestReboot(mode) { sessionRecorder.record("reboot:" + mode) }
    function requestLogout(mode) { sessionRecorder.record("logout:" + mode) }
    function suspend() { sessionRecorder.record("suspend") }
    function hibernate() { sessionRecorder.record("hibernate") }
    function switchUser() { sessionRecorder.record("switchuser") }
}
