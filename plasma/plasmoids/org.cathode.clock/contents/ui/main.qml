/*
    Cathode Clock - a Windows 98 style taskbar clock.

    Besides the time, it draws the 98 "notification area" box: a thin sunken
    frame around the clock that also stretches left to enclose the system tray
    when the tray sits directly before it on the panel. Only the frame lines are
    drawn over the tray, so its icons stay fully clickable.

    SPDX-License-Identifier: GPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami
import org.kde.ksvg as KSvg
import org.kde.plasma.workspace.calendar as PlasmaCalendar

PlasmoidItem {
    id: root

    property date now: new Date()
    readonly property string timeText: Qt.formatTime(now, Qt.locale().timeFormat(Locale.ShortFormat))

    // Where the sunken box starts, in the clock's own coordinates (<= 0).
    property real boxLeft: 0

    toolTipMainText: Qt.formatDate(now, Qt.locale().dateFormat(Locale.LongFormat))
    toolTipSubText: ""

    preferredRepresentation: compactRepresentation

    // Find the system tray sitting right before us in the panel, if any.
    function trayBeforeUs() {
        let container = root;
        while (container && container.isAppletContainer !== true) {
            container = container.parent;
        }
        if (!container || !container.parent) {
            return null;
        }
        const siblings = container.parent.children;
        for (let i = 0; i < siblings.length; ++i) {
            const s = siblings[i];
            if (s && s.isAppletContainer === true && s.appletIndex === container.appletIndex - 1
                    && s.applet && s.applet.plasmoid && s.applet.plasmoid.pluginName === "org.kde.plasma.systemtray") {
                return s;
            }
        }
        return null;
    }

    function updateBox() {
        const item = root.compactRepresentationItem;
        if (!item || Plasmoid.formFactor !== PlasmaCore.Types.Horizontal) {
            root.boxLeft = 0;
            return;
        }
        const tray = trayBeforeUs();
        if (!tray) {
            root.boxLeft = 0;
            return;
        }
        const p = item.mapFromItem(tray, 0, 0);
        root.boxLeft = Math.min(0, Math.round(p.x) - 2);
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            root.now = new Date();
            root.updateBox();
        }
    }

    compactRepresentation: MouseArea {
        id: compact

        readonly property int pad: Kirigami.Units.smallSpacing + 2

        Layout.minimumWidth: label.implicitWidth + pad * 2
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth
        Layout.fillHeight: true

        hoverEnabled: true
        onClicked: root.expanded = !root.expanded
        onWidthChanged: root.updateBox()
        onXChanged: root.updateBox()

        KSvg.FrameSvgItem {
            id: box
            imagePath: "widgets/frame"
            prefix: "sunken"
            x: root.boxLeft
            y: 0
            width: compact.width - x
            height: compact.height
        }

        PlasmaComponents3.Label {
            id: label
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: compact.pad
            text: root.timeText
            textFormat: Text.PlainText
        }
    }

    fullRepresentation: PlasmaCalendar.MonthView {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 18
        Layout.minimumHeight: Kirigami.Units.gridUnit * 16
        today: root.now
        showWeekNumbers: false
    }
}
