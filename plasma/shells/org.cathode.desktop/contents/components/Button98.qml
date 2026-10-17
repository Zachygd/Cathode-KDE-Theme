/* Windows 98 push button. SPDX-License-Identifier: GPL-2.0-or-later */
import QtQuick

Item {
    id: button
    property alias text: label.text
    property bool isDefault: false
    signal clicked()

    implicitWidth: Math.max(75, label.implicitWidth + 24)
    implicitHeight: 23
    opacity: enabled ? 1 : 0.6
    activeFocusOnTab: true

    readonly property bool down: mouse.pressed && mouse.containsMouse

    Pal98 { id: pal }

    // default / focused buttons get the black outline
    Rectangle {
        anchors.fill: parent
        color: pal.darkest
        visible: button.isDefault || button.activeFocus
    }
    Bevel98 {
        anchors.fill: parent
        anchors.margins: (button.isDefault || button.activeFocus) ? 1 : 0
        kind: button.down ? "pressed" : "raised"
    }
    Text {
        id: label
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: button.down ? 1 : 0
        anchors.verticalCenterOffset: button.down ? 1 : 0
        color: pal.text
    }
    // dotted focus rectangle, like 98
    Rectangle {
        anchors.fill: parent
        anchors.margins: 4
        color: "transparent"
        border.color: pal.text
        border.width: 1
        opacity: 0.6
        visible: button.activeFocus
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        onClicked: button.clicked()
    }
    Keys.onSpacePressed: button.clicked()
    Keys.onReturnPressed: button.clicked()
    Keys.onEnterPressed: button.clicked()
}
