/*
    Cathode login splash: the animated Cathode logo on black, a wordmark, and a
    sweeping bar in the logo's blues along the bottom edge.
    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick

Rectangle {
    id: root
    color: "black"

    property int stage

    onStageChanged: {
        if (stage === 1) {
            fadeIn.start();
        }
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        AnimatedSprite {
            id: logo
            readonly property real aspect: 378 / 232
            height: Math.round(root.height * 0.32)
            width: Math.round(height * aspect)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -Math.round(root.height * 0.05)
            source: "images/cathode-anim.png"
            frameWidth: 378
            frameHeight: 232
            frameCount: 16
            frameDuration: 85
            loops: AnimatedSprite.Infinite
            interpolate: false
            running: true
            smooth: true
        }

        Text {
            id: wordmark
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: logo.bottom
            anchors.topMargin: Math.round(logo.height * 0.02)
            text: "Cathode"
            color: "#eaf9ff"
            font.bold: true
            font.letterSpacing: Math.round(logo.height * 0.02)
            font.pixelSize: Math.round(logo.height * 0.15)
        }
    }

    // Sweeping bar along the bottom edge
    Item {
        id: barTrack
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: Math.max(4, Math.round(root.height * 0.008))
        clip: true

        Rectangle {
            id: bar
            height: parent.height
            width: parent.width
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#000000" }
                GradientStop { position: 0.3; color: "#01118d" }
                GradientStop { position: 0.55; color: "#0c6eec" }
                GradientStop { position: 0.7; color: "#0cecfb" }
                GradientStop { position: 1.0; color: "#000000" }
            }
            NumberAnimation on x {
                from: -barTrack.width
                to: barTrack.width
                duration: 1800
                loops: Animation.Infinite
                running: true
            }
        }
    }

    OpacityAnimator {
        id: fadeIn
        target: content
        from: 0
        to: 1
        duration: 400
        easing.type: Easing.InOutQuad
    }
}
