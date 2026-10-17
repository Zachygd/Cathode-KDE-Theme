/*
    Windows 98 3D bevel.
      kind: "window" (frames/dialogs), "raised" (buttons), "pressed",
            "sunken" (thin, status boxes), "field" (text fields)
    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick

Item {
    id: bevel
    property string kind: "raised"
    property color face: kind === "field" ? pal.field : pal.face

    Pal98 { id: pal }

    // [outer top-left, outer bottom-right, inner top-left, inner bottom-right]
    readonly property var c: ({
        "window":  [pal.light, pal.darkest, pal.hilite, pal.shadow],
        "raised":  [pal.hilite, pal.darkest, pal.light, pal.shadow],
        "pressed": [pal.darkest, pal.hilite, pal.shadow, pal.light],
        "field":   [pal.shadow, pal.hilite, pal.darkest, pal.light],
        "sunken":  [pal.shadow, pal.hilite, "transparent", "transparent"]
    })[kind]

    // painted back to front: outer bottom-right, outer top-left, inner bottom-right, inner top-left, face
    Rectangle { anchors.fill: parent; color: bevel.c[1] }
    Rectangle { x: 0; y: 0; width: parent.width - 1; height: parent.height - 1; color: bevel.c[0] }
    Rectangle { x: 1; y: 1; width: parent.width - 2; height: parent.height - 2; color: bevel.c[3] === "transparent" ? bevel.face : bevel.c[3] }
    Rectangle { x: 1; y: 1; width: parent.width - 3; height: parent.height - 3; color: bevel.c[2] === "transparent" ? bevel.face : bevel.c[2] }
    Rectangle {
        readonly property int inset: bevel.kind === "sunken" ? 1 : 2
        x: inset; y: inset; width: parent.width - 2 * inset; height: parent.height - 2 * inset
        color: bevel.face
    }
}
