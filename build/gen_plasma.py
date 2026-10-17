#!/usr/bin/env python3
"""Generate the Cathode98 Plasma style (taskbar, popups, tooltips, buttons)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import Grid, Svg, LT, HI, FACE, SH, DK, INFO, FIELD, HOVER, ACCENT, PAL  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "plasma/desktoptheme/Cathode98"
W = os.path.join(OUT, "widgets")
D = os.path.join(OUT, "dialogs")
os.makedirs(W, exist_ok=True)
os.makedirs(D, exist_ok=True)

SEL = ACCENT      # the active scheme's selection colour (white text)
T = None          # transparent pixel


def window_frame(w=12, h=12, face=None):
    face = FACE if face is None else face
    """Win98 window/menu frame: outer LT/DK, inner HI/SH."""
    g = Grid(w, h, face)
    g.bevel(0, 0, w, h, LT, DK, HI, SH)
    return g


# --- panel-background.svg (the taskbar) --------------------------------------
# The standard taskbar is 34px: 3px margin + 28px of applets + 3px margin.
PANEL_H, PANEL_PAD = 34, 3
APPLET_H = PANEL_H - 2 * PANEL_PAD
svg = Svg()
for prefix in ["", "south", "north", "east", "west"]:
    svg.frame(prefix, window_frame(), (2, 2, 2, 2))
    svg.margins(prefix, 2, PANEL_PAD, 2, PANEL_PAD)
svg.write(os.path.join(W, "panel-background.svg"))


# --- tasks.svg (taskbar buttons) ---------------------------------------------
# The task manager fills the whole panel height, so the gap between buttons and
# the panel bevel is baked in as transparent padding: 3px above/below, 2px right.
PAD_T, PAD_B, PAD_R = PANEL_PAD, PANEL_PAD, 2
TW, TH = 24, PAD_T + APPLET_H + PAD_B


def task_grid(kind):
    g = Grid(TW, TH, T)
    bw, bh = TW - PAD_R, APPLET_H
    if kind == "focus":
        # 98 used a white/gray checkerboard; a flat light gray reads the same and
        # doesn't turn into stripes at fractional display scaling
        g.rect(0, PAD_T, bw, bh, LT)
        g.bevel(0, PAD_T, bw, bh, DK, HI, SH, LT)
    elif kind == "attention":
        g.raised(0, PAD_T, bw, bh)
        g.rect(2, PAD_T + 2, bw - 4, 1, SEL)
        g.rect(2, PAD_T + bh - 3, bw - 4, 1, SEL)
        g.rect(2, PAD_T + 2, 1, bh - 4, SEL)
        g.rect(bw - 3, PAD_T + 2, 1, bh - 4, SEL)
    elif kind == "progress":
        g.rect(2, PAD_T + 2, bw - 4, bh - 4, (SEL, 0.3))
    else:  # normal / minimized / launcher
        g.raised(0, PAD_T, bw, bh)
    return g


svg = Svg()
svg.hint("hint-tile-center")   # keeps the checkerboard on the active button crisp
svg.hint("hint-stretch-borders")
BORDERS = (2, PAD_T + 2, PAD_R + 2, PAD_B + 2)
for prefix, kind in [("", "normal"), ("normal", "normal"), ("minimized", "normal"),
                     ("focus", "focus"), ("attention", "attention"), ("progress", "progress")]:
    svg.frame(prefix, task_grid(kind), BORDERS)
    # content padding: icon/text inset from the bevel, 16px icon vertically centred
    vpad = (APPLET_H - 16) // 2
    svg.margins(prefix, 5, PAD_T + vpad, PAD_R + 4, PAD_B + vpad)
svg.write(os.path.join(W, "tasks.svg"))


# --- dialogs/background.svg + widgets/background.svg (Start menu, popups) -----
for path in [os.path.join(D, "background.svg"), os.path.join(W, "background.svg")]:
    svg = Svg()
    svg.frame("", window_frame(), (2, 2, 2, 2))
    svg.margins("", 3, 3, 3, 3)
    svg.write(path)


# --- tooltip.svg ---------------------------------------------------------------
svg = Svg()
g = Grid(8, 8, INFO)
g.rect(0, 0, 8, 1, DK); g.rect(0, 7, 8, 1, DK); g.rect(0, 0, 1, 8, DK); g.rect(7, 0, 1, 8, DK)
svg.frame("", g, (1, 1, 1, 1))
svg.margins("", 4, 3, 4, 3)
svg.write(os.path.join(W, "tooltip.svg"))


# --- viewitem.svg (menu / list highlight) ------------------------------------
svg = Svg()
for prefix, fill in [("hover", HOVER), ("selected", SEL), ("selected+hover", SEL)]:
    svg.frame(prefix, Grid(6, 6, fill), (1, 1, 1, 1))
    svg.margins(prefix, 3, 2, 3, 2)
svg.frame("normal", Grid(6, 6, T), (1, 1, 1, 1))
svg.margins("normal", 3, 2, 3, 2)
svg.write(os.path.join(W, "viewitem.svg"))


# --- listitem.svg (Plasma list rows) -------------------------------------------
# Without this Plasma falls back to Breeze's, which draws a faint separator line
# under every row (the "random lines" in the Start menu).
svg = Svg()
svg.frame("normal", Grid(6, 6, T), (1, 1, 1, 1))
svg.frame("hover", Grid(6, 6, HOVER), (1, 1, 1, 1))
svg.frame("pressed", Grid(6, 6, SEL), (1, 1, 1, 1))
for prefix in ["normal", "hover", "pressed"]:
    svg.margins(prefix, 3, 2, 3, 2)
y = svg.cursor_y
svg.element("separator", [], transparent_box=(0, y, 8, 1))
svg.cursor_y += 6
svg.write(os.path.join(W, "listitem.svg"))


# --- plasmoidheading.svg (header/footer strips in tray & clock popups) ---------
svg = Svg()
g = Grid(8, 8, FACE); g.hline(0, 6, 8, SH); g.hline(0, 7, 8, HI)      # etched line below
svg.frame("header", g, (1, 1, 1, 2)); svg.margins("header", 4, 3, 4, 4)
g = Grid(8, 8, FACE); g.hline(0, 0, 8, SH); g.hline(0, 1, 8, HI)      # etched line above
svg.frame("footer", g, (1, 2, 1, 1)); svg.margins("footer", 4, 4, 4, 3)
svg.write(os.path.join(W, "plasmoidheading.svg"))


# --- button.svg (Plasma push / tool buttons) ----------------------------------
svg = Svg()
g = Grid(10, 10, FACE); g.raised(0, 0, 10, 10)
svg.frame("normal", g, (2, 2, 2, 2)); svg.margins("normal", 6, 4, 6, 4)
g = Grid(10, 10, FACE); g.raised(0, 0, 10, 10)
svg.frame("focus-background", g, (2, 2, 2, 2)); svg.margins("focus-background", 6, 4, 6, 4)
g = Grid(10, 10, FACE); g.sunken(0, 0, 10, 10)
svg.frame("pressed", g, (2, 2, 2, 2)); svg.margins("pressed", 6, 4, 6, 4)
# focus ring: Win98 marks the focused button with a black outline
g = Grid(10, 10, T); g.rect(0, 0, 10, 1, DK); g.rect(0, 9, 10, 1, DK); g.rect(0, 0, 1, 10, DK); g.rect(9, 0, 1, 10, DK)
svg.frame("focus", g, (1, 1, 1, 1))
for prefix in ["hover", "shadow", "toolbutton-focus"]:
    svg.frame(prefix, Grid(6, 6, T), (1, 1, 1, 1))
g = Grid(10, 10, T); g.thin_raised(0, 0, 10, 10)
svg.frame("toolbutton-hover", g, (1, 1, 1, 1)); svg.margins("toolbutton-hover", 4, 3, 4, 3)
g = Grid(10, 10, T); g.thin_sunken(0, 0, 10, 10)
svg.frame("toolbutton-pressed", g, (1, 1, 1, 1)); svg.margins("toolbutton-pressed", 4, 3, 4, 3)
svg.write(os.path.join(W, "button.svg"))


# --- lineedit.svg (search fields) ---------------------------------------------
svg = Svg()
g = Grid(10, 10, FIELD); g.field(0, 0, 10, 10)
svg.frame("base", g, (2, 2, 2, 2)); svg.margins("base", 4, 3, 4, 3)
for prefix in ["focus", "hover"]:
    svg.frame(prefix, Grid(6, 6, T), (1, 1, 1, 1))
svg.write(os.path.join(W, "lineedit.svg"))


# --- frame.svg ----------------------------------------------------------------
svg = Svg()
g = Grid(8, 8, T); g.thin_sunken(0, 0, 8, 8)
svg.frame("sunken", g, (1, 1, 1, 1))
g = Grid(8, 8, T); g.thin_raised(0, 0, 8, 8)
svg.frame("raised", g, (1, 1, 1, 1))
svg.frame("plain", Grid(6, 6, T), (1, 1, 1, 1))
svg.write(os.path.join(W, "frame.svg"))


# --- line.svg (etched menu separators) ----------------------------------------
svg = Svg()
y = svg.cursor_y
svg.element("horizontal-line", [f'<rect x="0" y="{y}" width="16" height="1" fill="{SH}"/>',
                                 f'<rect x="0" y="{y + 1}" width="16" height="1" fill="{HI}"/>'])
svg.cursor_y += 6
y = svg.cursor_y
svg.element("vertical-line", [f'<rect x="0" y="{y}" width="1" height="16" fill="{SH}"/>',
                               f'<rect x="1" y="{y}" width="1" height="16" fill="{HI}"/>'])
svg.cursor_y += 20
svg.write(os.path.join(W, "line.svg"))


# --- tabbar.svg -----------------------------------------------------------------
# "<edge>-active-tab" is also what Plasma draws under a panel widget while its
# popup is open (the black line under Start / the clock). Windows 98 had no such
# marker, so the panel-edge ones are empty. "north-active-tab" is the selected
# tab inside popups (e.g. the calendar's Days/Months/Years): a slim Cathode blue
# underline keeps that readable.
svg = Svg()
for prefix in ["south-active-tab", "west-active-tab", "east-active-tab", "active-tab"]:
    svg.frame(prefix, Grid(6, 6, T), (1, 1, 1, 1))
g = Grid(6, 6, T); g.rect(0, 4, 6, 2, ACCENT)
svg.frame("north-active-tab", g, (1, 1, 1, 2))
svg.write(os.path.join(W, "tabbar.svg"))


# --- solid / opaque / translucent variants ------------------------------------------
# Plasma asks for "solid/..." images for opaque surfaces (right-click menus, combo
# popups, solid dialogs) and "opaque/..." when compositing is off. Without these it
# silently falls back to Breeze's versions.
import shutil
for variant in ["solid", "opaque", "translucent"]:
    for rel in ["dialogs/background.svg", "widgets/background.svg", "widgets/panel-background.svg",
                "widgets/tooltip.svg"]:
        dst = os.path.join(OUT, variant, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(os.path.join(OUT, rel), dst)
# solid/widgets/tooltip is what Plasma's right-click menus and drop-downs use:
# give it the gray raised 98 menu frame instead of the yellow tooltip.
svg = Svg()
svg.frame("", window_frame(), (2, 2, 2, 2))
svg.margins("", 3, 3, 3, 3)
svg.write(os.path.join(OUT, "solid", "widgets", "tooltip.svg"))


# --- metadata -----------------------------------------------------------------
meta = {
    "KPlugin": {
        "Authors": [{"Name": "Zach"}],
        "Description": "Windows 98 style taskbar, menus and tooltips for Cathode",
        "Id": PAL["THEME_ID"],
        "License": "GPL-2.0-or-later",
        "Name": PAL["THEME_NAME"],
        "Version": "1.0",
    },
    "X-Plasma-API-Minimum-Version": "6.0",
}
with open(os.path.join(OUT, "metadata.json"), "w") as f:
    json.dump(meta, f, indent=4)
with open(os.path.join(OUT, "plasmarc"), "w") as f:
    f.write("[AdaptiveTransparency]\nenabled=false\n\n[ContrastEffect]\nenabled=false\n\n[BlurBehindEffect]\nenabled=false\n")
# No "colors" file: the Plasma style takes its colours (including the accent
# used above) from the active Cathode colour scheme, so one style serves them all.
print("plasma style ->", OUT)
