/*
    Cathode sign-out screen: the Windows 98 "Shut Down" dialog.
    The screen dims, a dialog asks "What do you want the computer to do?",
    pick an option and press OK (or Enter). Esc / Cancel goes back.

    Uses the same interface Plasma's logout greeter gives every theme:
    context properties (maysd, sdtype, ShutdownType, spdMethods, canLogout,
    softwareUpdatePending, screenGeometry) and the *Requested() signals.

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import "../components"

Item {
    id: root
    width: screenGeometry.width
    height: screenGeometry.height

    signal logoutRequested()
    signal haltRequested()
    signal haltUpdateRequested()
    signal suspendRequested(int spdMethod)
    signal rebootRequested()
    signal rebootRequested2(int opt)
    signal rebootUpdateRequested()
    signal cancelRequested()
    signal lockScreenRequested()
    signal cancelSoftwareUpdateRequested()

    Pal98 { id: pal }

    readonly property bool updates: typeof softwareUpdatePending !== "undefined" && softwareUpdatePending
    readonly property bool mayLogout: typeof canLogout === "undefined" || canLogout

    // Options in 98 order. Each: label, whether it's available, what to do.
    readonly property var options: [
        { label: "Stand by", show: spdMethods.SuspendState, run: () => root.suspendRequested(2) },
        { label: "Hibernate", show: spdMethods.HibernateState, run: () => root.suspendRequested(4) },
        { label: root.updates ? "Install updates and shut down" : "Shut down", show: maysd,
          run: () => root.updates ? root.haltUpdateRequested() : root.haltRequested() },
        { label: root.updates ? "Install updates and restart" : "Restart", show: maysd,
          run: () => root.updates ? root.rebootUpdateRequested() : root.rebootRequested() },
        { label: "Log out", show: root.mayLogout, run: () => root.logoutRequested() },
        { label: "Lock the computer", show: true, run: () => root.lockScreenRequested() }
    ].filter(o => o.show)

    function find(part, fallback) {
        for (let i = 0; i < options.length; ++i) {
            if (options[i].label.indexOf(part) !== -1) {
                return i;
            }
        }
        return fallback;
    }

    // Pre-select whatever was asked for (e.g. "Restart" from the Start menu)
    property int selected: sdtype === ShutdownType.ShutdownTypeReboot ? find("estart", 0)
        : (sdtype === ShutdownType.ShutdownTypeLogout || sdtype === ShutdownType.ShutdownTypeNone) ? find("Log out", 0)
        : find("hut down", 0)

    function accept() {
        options[selected].run();
    }

    focus: true
    Keys.onEscapePressed: root.cancelRequested()
    Keys.onReturnPressed: root.accept()
    Keys.onEnterPressed: root.accept()
    Keys.onUpPressed: selected = Math.max(0, selected - 1)
    Keys.onDownPressed: selected = Math.min(options.length - 1, selected + 1)

    // 98 dimmed the whole screen behind this dialog
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.55
    }
    MouseArea {
        anchors.fill: parent
        onClicked: root.cancelRequested()
    }

    Item {
        id: dialog
        anchors.centerIn: parent
        width: 400
        height: titleBar.height + body.implicitHeight + 3 + 3 + 2 + 14

        // swallow clicks so they don't cancel
        MouseArea { anchors.fill: parent }

        Bevel98 { anchors.fill: parent; kind: "window" }

        TitleBar98 {
            id: titleBar
            x: 3; y: 3
            width: parent.width - 6
            text: "Shut Down Cathode"
            showClose: true
            onCloseClicked: root.cancelRequested()
        }

        Column {
            id: body
            x: 14
            y: titleBar.y + titleBar.height + 12
            width: parent.width - 28
            spacing: 12

            Row {
                spacing: 16
                Image {
                    source: "images/logos/" + pal.scheme.slug + ".png"
                    width: 72; height: 36
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
                Column {
                    spacing: 8
                    Text {
                        text: "What do you want the computer to do?"
                        color: pal.text
                    }
                    Repeater {
                        model: root.options.length
                        Radio98 {
                            required property int index
                            text: root.options[index].label
                            checked: root.selected === index
                            activeFocusOnTab: false
                            onActivated: root.selected = index
                        }
                    }
                }
            }

            Row {
                anchors.right: parent.right
                spacing: 6
                Button98 {
                    text: "OK"
                    isDefault: true
                    onClicked: root.accept()
                }
                Button98 {
                    text: "Cancel"
                    onClicked: root.cancelRequested()
                }
            }
        }
    }
}
