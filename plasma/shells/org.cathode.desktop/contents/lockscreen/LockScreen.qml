/*
    Cathode lock screen: a Windows 98 style "Unlock Computer" dialog on the
    classic teal desktop, with Sleep / Log Off... / Shut Down... buttons.

    Unlocking talks to kscreenlocker's `authenticator` exactly like Plasma's
    built-in fallback greeter. Power actions use Plasma's SessionManagement
    (the same object KDE's own lock screen uses for Sleep and Switch User).
    Shut down / restart / log off are sent with confirmation skipped (value 0),
    because a normal confirmation prompt would open hidden behind the lock
    screen; these pages are the confirmation instead.

    If this file ever fails to load, kscreenlocker falls back to its built-in
    lock screen, so it can't lock you out.

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import org.kde.plasma.private.sessions
import "../components"

Item {
    id: lockScreen

    property bool locked: false
    property bool viewVisible: false
    property string notification: ""
    property bool authSucceeded: false

    // "unlock", "shutdown" or "logoff"
    property string page: "unlock"
    property int shutdownChoice: 0

    signal unlockRequested()

    Pal98 { id: pal }

    SessionManagement { id: session }

    // Options on the Shut Down page, in 98 order; only what this machine can do.
    readonly property var shutdownOptions: [
        { label: "Shut down", show: session.canShutdown, run: () => session.requestShutdown(0) },
        { label: "Restart", show: session.canReboot, run: () => session.requestReboot(0) },
        { label: "Hibernate", show: session.canHibernate, run: () => session.hibernate() },
        { label: "Switch user", show: session.canSwitchUser, run: () => session.switchUser() }
    ].filter(o => o.show)

    function tryUnlock() {
        if (authenticator.graceLocked || authenticator.busy) {
            return;
        }
        lockScreen.notification = "";
        authenticator.startAuthenticating();
    }

    function resetFocus() {
        if (page === "unlock") {
            password.forceActiveFocus();
        } else {
            dialog.forceActiveFocus();
        }
    }

    function showPage(p) {
        page = p;
        shutdownChoice = 0;
        resetFocus();
    }

    function acceptPage() {
        if (page === "unlock") {
            tryUnlock();
        } else if (page === "shutdown" && shutdownOptions.length > 0) {
            shutdownOptions[shutdownChoice].run();
            showPage("unlock");
        } else if (page === "logoff") {
            session.requestLogout(0);
            showPage("unlock");
        }
    }

    Component.onCompleted: resetFocus()
    onLockedChanged: resetFocus()
    onViewVisibleChanged: resetFocus()

    Connections {
        target: authenticator
        function onFailed() {
            lockScreen.notification = "The password is incorrect. Please try again.";
            password.text = "";
            lockScreen.resetFocus();
        }
        function onBusyChanged() {
            if (!authenticator.busy && !lockScreen.authSucceeded) {
                lockScreen.resetFocus();
            }
        }
        function onInfoMessageChanged() {
            lockScreen.notification = authenticator.infoMessage;
        }
        function onErrorMessageChanged() {
            lockScreen.notification = authenticator.errorMessage;
        }
        function onPromptForSecretChanged() {
            authenticator.respond(password.text);
        }
        function onSucceeded() {
            lockScreen.authSucceeded = true;
            Qt.quit();
        }
    }

    // Classic teal desktop (covers the wallpaper plugin layer underneath)
    Rectangle {
        anchors.fill: parent
        color: pal.desktop
    }

    // Date and time, bottom right
    Text {
        id: clock
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 16
        color: "#ffffff"
        font.pixelSize: 15
        function stamp() {
            return Qt.formatDateTime(new Date(), Qt.locale().dateFormat(Locale.LongFormat) + "   " + Qt.locale().timeFormat(Locale.ShortFormat));
        }
        text: stamp()
        Timer {
            interval: 1000; running: true; repeat: true
            onTriggered: clock.text = clock.stamp()
        }
    }

    // ---- the dialog ------------------------------------------------------
    Item {
        id: dialog
        visible: lockScreen.locked
        anchors.centerIn: parent
        width: 520
        height: titleBar.height + body.implicitHeight + 3 + 3 + 2 + 14
        focus: lockScreen.page !== "unlock"

        Keys.onEscapePressed: lockScreen.showPage("unlock")
        Keys.onReturnPressed: lockScreen.acceptPage()
        Keys.onEnterPressed: lockScreen.acceptPage()
        Keys.onUpPressed: lockScreen.shutdownChoice = Math.max(0, lockScreen.shutdownChoice - 1)
        Keys.onDownPressed: lockScreen.shutdownChoice = Math.min(lockScreen.shutdownOptions.length - 1, lockScreen.shutdownChoice + 1)

        Bevel98 { anchors.fill: parent; kind: "window" }

        TitleBar98 {
            id: titleBar
            x: 3; y: 3
            width: parent.width - 6
            text: lockScreen.page === "shutdown" ? "Shut Down Cathode"
                : lockScreen.page === "logoff" ? "Log Off Cathode" : "Unlock Computer"
            showClose: lockScreen.page !== "unlock"
            onCloseClicked: lockScreen.showPage("unlock")
        }

        Column {
            id: body
            x: 14
            y: titleBar.y + titleBar.height + 12
            width: parent.width - 28
            spacing: 10

            Row {
                spacing: 14
                Image {
                    objectName: "lockLogo"
                    source: "images/logos/" + pal.scheme.slug + ".png"
                    width: 72; height: 36
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
                Text {
                    width: body.width - 72 - 14
                    wrapMode: Text.WordWrap
                    color: pal.text
                    text: lockScreen.page === "shutdown" ? "What do you want the computer to do?"
                        : lockScreen.page === "logoff" ? "Are you sure you want to log off " + kscreenlocker_userName + "?\nPrograms that are still open will be closed, and unsaved work will be lost."
                        : "This computer is locked.\nType your password to unlock it."
                }
            }

            // ---- unlock page ----
            Grid {
                visible: lockScreen.page === "unlock"
                columns: 2
                columnSpacing: 10
                rowSpacing: 8
                leftPadding: 86
                verticalItemAlignment: Grid.AlignVCenter

                Text { text: "User name:"; color: pal.text }
                Item {
                    width: 240; height: 21
                    Bevel98 { anchors.fill: parent; kind: "field"; face: pal.face }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        x: 5
                        color: pal.text
                        text: kscreenlocker_userName
                    }
                }

                Text { text: "Password:"; color: pal.text }
                Item {
                    width: 240; height: 21
                    Bevel98 { anchors.fill: parent; kind: "field" }
                    TextInput {
                        id: password
                        anchors.fill: parent
                        anchors.leftMargin: 5
                        anchors.rightMargin: 5
                        verticalAlignment: TextInput.AlignVCenter
                        echoMode: TextInput.Password
                        passwordCharacter: "*"
                        enabled: !authenticator.busy
                        color: pal.text
                        selectionColor: pal.selection
                        selectedTextColor: "#ffffff"
                        focus: lockScreen.page === "unlock"
                        Keys.onReturnPressed: lockScreen.tryUnlock()
                        Keys.onEnterPressed: lockScreen.tryUnlock()
                        Keys.onEscapePressed: text = ""
                    }
                }
            }

            // ---- shut down page ----
            Column {
                visible: lockScreen.page === "shutdown"
                leftPadding: 86
                spacing: 8
                Repeater {
                    model: lockScreen.shutdownOptions.length
                    Radio98 {
                        required property int index
                        text: lockScreen.shutdownOptions[index].label
                        checked: lockScreen.shutdownChoice === index
                        onActivated: lockScreen.shutdownChoice = index
                    }
                }
            }

            Text {
                width: body.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                color: pal.error
                text: lockScreen.notification
                visible: lockScreen.page === "unlock" && text.length > 0
            }

            // ---- buttons ----
            Item {
                width: body.width
                height: 23

                Row {
                    visible: lockScreen.page === "unlock"
                    anchors.left: parent.left
                    spacing: 6
                    Button98 {
                        objectName: "sleepButton"
                        text: "Sleep"
                        visible: session.canSuspend
                        onClicked: session.suspend()
                    }
                    Button98 {
                        objectName: "logoffButton"
                        text: "Log Off..."
                        visible: session.canLogout
                        onClicked: lockScreen.showPage("logoff")
                    }
                    Button98 {
                        objectName: "shutdownButton"
                        text: "Shut Down..."
                        visible: lockScreen.shutdownOptions.length > 0
                        onClicked: lockScreen.showPage("shutdown")
                    }
                }

                Row {
                    anchors.right: parent.right
                    spacing: 6
                    Button98 {
                        objectName: "okButton"
                        text: lockScreen.page === "logoff" ? "Log Off"
                            : (lockScreen.page === "unlock" && authenticator.busy) ? "Checking..." : "OK"
                        isDefault: true
                        enabled: lockScreen.page !== "unlock" || (!authenticator.graceLocked && !authenticator.busy)
                        onClicked: lockScreen.acceptPage()
                    }
                    Button98 {
                        objectName: "cancelButton"
                        text: "Cancel"
                        visible: lockScreen.page !== "unlock"
                        onClicked: lockScreen.showPage("unlock")
                    }
                }
            }
        }
    }
}
