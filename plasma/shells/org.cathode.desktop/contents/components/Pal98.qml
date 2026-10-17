/*
    Cathode 98 palette for the lock and shut-down screens. Follows the active
    colour scheme: a dark window colour switches everything to the dark set.
    SPDX-License-Identifier: GPL-2.0-or-later
*/
import QtQuick
import "CathodeSchemes.js" as CathodeSchemes

QtObject {
    id: pal
    property SystemPalette system: SystemPalette { colorGroup: SystemPalette.Active }
    readonly property bool dark: system.window.hslLightness < 0.5

    readonly property color face:    dark ? "#3a3a3a" : "#c0c0c0"
    readonly property color light:   dark ? "#4a4a4a" : "#dfdfdf"
    readonly property color hilite:  dark ? "#686868" : "#ffffff"
    readonly property color shadow:  dark ? "#242424" : "#808080"
    readonly property color darkest: "#000000"
    readonly property color text:    dark ? "#e8e8e8" : "#000000"
    readonly property color field:   dark ? "#2a2a2a" : "#f4f3ef"
    // the active Cathode scheme, recognised from its selection colour
    readonly property var scheme: CathodeSchemes.scheme(system.highlight)
    readonly property color desktop: dark ? scheme.deskDark : scheme.deskLight
    readonly property color error:   dark ? "#ff8080" : "#800000"
    readonly property color selection: system.highlight
    function titleStop(i) { return CathodeSchemes.stop(system.highlight, i, false) }
}
