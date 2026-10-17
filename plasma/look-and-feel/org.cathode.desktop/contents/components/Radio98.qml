/* Windows 98 radio button with label. SPDX-License-Identifier: GPL-2.0-or-later */
import QtQuick

Item {
    id: radio
    property alias text: label.text
    property bool checked: false
    signal activated()

    Pal98 { id: pal }

    implicitWidth: 18 + label.implicitWidth
    implicitHeight: Math.max(16, label.implicitHeight)

    Item {
        id: circle
        width: 12; height: 12
        anchors.verticalCenter: parent.verticalCenter
        // sunken round well: dark top-left arc, light bottom-right arc
        Rectangle { anchors.fill: parent; radius: 6; color: pal.field }
        Rectangle { anchors.fill: parent; radius: 6; color: "transparent"; border.color: pal.shadow; border.width: 1 }
        Rectangle { anchors.fill: parent; anchors.margins: 1; radius: 5; color: "transparent"; border.color: "#000000"; border.width: 1; opacity: 0.55 }
        Rectangle {
            anchors.centerIn: parent
            width: 4; height: 4; radius: 2
            color: pal.text
            visible: radio.checked
        }
    }
    Text {
        id: label
        anchors.left: circle.right
        anchors.leftMargin: 6
        anchors.verticalCenter: parent.verticalCenter
        color: pal.text
        // dotted focus box around the label of the selected option
        Rectangle {
            anchors.fill: parent
            anchors.margins: -1
            color: "transparent"
            border.color: pal.text
            opacity: 0.6
            visible: radio.checked && radio.activeFocus
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: radio.activated()
    }
}
