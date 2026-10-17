/* Title bar in the active scheme's gradient. SPDX-License-Identifier: GPL-2.0-or-later */
import QtQuick

Rectangle {
    id: bar
    property alias text: title.text
    property bool showClose: false
    signal closeClicked()

    height: 18
    Pal98 { id: barPal }
    gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: barPal.titleStop(0).position; color: barPal.titleStop(0).color }
        GradientStop { position: barPal.titleStop(1).position; color: barPal.titleStop(1).color }
        GradientStop { position: barPal.titleStop(2).position; color: barPal.titleStop(2).color }
        GradientStop { position: barPal.titleStop(3).position; color: barPal.titleStop(3).color }
        GradientStop { position: barPal.titleStop(4).position; color: barPal.titleStop(4).color }
        GradientStop { position: barPal.titleStop(5).position; color: barPal.titleStop(5).color }
    }
    Text {
        id: title
        anchors.left: parent.left
        anchors.leftMargin: 4
        anchors.verticalCenter: parent.verticalCenter
        color: "#ffffff"
        font.bold: true
    }
    Item {
        visible: bar.showClose
        width: 16; height: 14
        anchors.right: parent.right
        anchors.rightMargin: 2
        anchors.verticalCenter: parent.verticalCenter
        Bevel98 { anchors.fill: parent; kind: closeMouse.pressed ? "pressed" : "raised" }
        Text { anchors.centerIn: parent; text: "✕"; font.pixelSize: 9; font.bold: true; color: closePal.text }
        Pal98 { id: closePal }
        MouseArea { id: closeMouse; anchors.fill: parent; onClicked: bar.closeClicked() }
    }
}
