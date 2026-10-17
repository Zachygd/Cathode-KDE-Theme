#!/usr/bin/env python3
"""Generate the Cathode98 Aurorae window decoration (Windows 98 style)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import Grid, Svg, LT, HI, FACE, SH, DK, TEXT, INACT1, INACT2, TITLE_STOPS, VARIANT, SCHEME  # noqa: E402
from schemes import theme_id, theme_name  # noqa: E402

DARK = VARIANT == "dark"
TID, TNAME = theme_id(SCHEME, DARK), theme_name(SCHEME, DARK)
# Caption buttons are identical for every colour, so other schemes link to the
# standard theme's button files instead of carrying their own copies.
SHARED = None if SCHEME == "cathode" else theme_id("cathode", DARK)

OUT = sys.argv[1] if len(sys.argv) > 1 else "aurorae/themes/Cathode98"
os.makedirs(OUT, exist_ok=True)

# --- geometry (keep in sync with Cathode98rc) -------------------------------
FRAME = 3          # drawn bevel thickness (kwin border may be wider; extra shows face)
TITLE_H = 18
GAP = 1            # face-coloured line between caption and client
TOP = FRAME + TITLE_H + GAP   # 22
W = 40             # sample width (stretched)
H = TOP + 12 + FRAME


def window_grid():
    g = Grid(W, H, FACE)
    # outer bevel: LT / DK, inner bevel: HI / SH  (Win98 window frame)
    g.hline(0, 0, W - 1, LT)
    g.vline(0, 0, H - 1, LT)
    g.hline(0, H - 1, W, DK)
    g.vline(W - 1, 0, H, DK)
    g.hline(1, 1, W - 3, HI)
    g.vline(1, 1, H - 3, HI)
    g.hline(1, H - 2, W - 2, SH)
    g.vline(W - 2, 1, H - 2, SH)
    return g


def decoration(svg, prefix, c1, c2=None):
    gid = f"grad-{prefix}"
    svg.gradient(gid, c1, c2)
    g = window_grid()

    def caption(ox, oy, w, h):
        # gradient band across the stretched top element (caption row only)
        return [f'<rect x="{ox}" y="{oy + FRAME}" width="{w}" height="{TITLE_H}" fill="url(#{gid})"/>']

    def caption_left(ox, oy, w, h):
        return []

    svg.frame(prefix, g, (FRAME, TOP, FRAME, FRAME), side_items={"top": caption})


def maximized(svg, prefix, c1, c2=None):
    # Maximized windows use NoBorder: only <prefix>-center is drawn, stretched
    # over the whole decoration, so it must be uniform vertically.
    gid = f"grad-{prefix}"
    svg.gradient(gid, c1, c2)
    y = svg.cursor_y
    svg.element(f"{prefix}-center", [f'<rect x="0" y="{y}" width="{W}" height="{TITLE_H}" fill="url(#{gid})"/>'])
    svg.cursor_y += TITLE_H + 8


svg = Svg()
svg.hint("hint-stretch-borders")
decoration(svg, "decoration", TITLE_STOPS)
decoration(svg, "decoration-inactive", INACT1, INACT2)
maximized(svg, "decoration-maximized", TITLE_STOPS)
maximized(svg, "decoration-maximized-inactive", INACT1, INACT2)
svg.write(os.path.join(OUT, "decoration.svg"))

# --- caption buttons ---------------------------------------------------------
BW, BH = 16, 14

GLYPHS = {
    "close": (4, 3, [
        "xx....xx",
        ".xx..xx.",
        "..xxxx..",
        "...xx...",
        "..xxxx..",
        ".xx..xx.",
        "xx....xx",
    ]),
    "minimize": (4, 9, [
        "xxxxxx",
        "xxxxxx",
    ]),
    "maximize": (3, 2, [
        "xxxxxxxxx",
        "xxxxxxxxx",
        "x.......x",
        "x.......x",
        "x.......x",
        "x.......x",
        "x.......x",
        "x.......x",
        "xxxxxxxxx",
    ]),
    "restore": (3, 2, [
        "...xxxxxx",
        "...xxxxxx",
        "...x....x",
        "xxxxxx..x",
        "xxxxxx..x",
        "x....xxxx",
        "x....x...",
        "x....x...",
        "xxxxxx...",
    ]),
    "help": (5, 2, [
        ".xxxx.",
        "xx..xx",
        "....xx",
        "...xx.",
        "..xx..",
        "..xx..",
        "......",
        "..xx..",
        "..xx..",
    ]),
}


def button_grid(name, state):
    g = Grid(BW, BH, FACE)
    ox, oy, rows = GLYPHS[name]
    if state == "pressed":
        g.sunken(0, 0, BW, BH)
        g.bitmap(rows, ox + 1, oy + 1, TEXT)
    else:
        g.raised(0, 0, BW, BH)
        if state == "deactivated":
            g.bitmap(rows, ox + 1, oy + 1, HI)
            g.bitmap(rows, ox, oy, SH)
        else:
            g.bitmap(rows, ox, oy, TEXT)
    return g


for name in GLYPHS:
    if SHARED:
        link = os.path.join(OUT, f"{name}.svg")
        if os.path.lexists(link):
            os.remove(link)
        os.symlink(f"../{SHARED}/{name}.svg", link)
        continue
    svg = Svg()
    svg.hint("hint-stretch-borders")
    for prefix, state in [
        ("active", "normal"),
        ("pressed", "pressed"),
        ("inactive", "normal"),
        ("pressed-inactive", "pressed"),
        ("deactivated", "deactivated"),
        ("deactivated-inactive", "deactivated"),
    ]:
        svg.frame(prefix, button_grid(name, state), (2, 2, 2, 2))
    svg.write(os.path.join(OUT, f"{name}.svg"))

# --- metadata + config -------------------------------------------------------
with open(os.path.join(OUT, "metadata.desktop"), "w") as f:
    f.write(f"""[Desktop Entry]
Name={TNAME}
Comment=Windows 98 style window frames for Cathode
X-KDE-PluginInfo-Author=Zach
X-KDE-PluginInfo-Name={TID}
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=GPL-2.0-or-later
X-KDE-PluginInfo-EnabledByDefault=true
""")

with open(os.path.join(OUT, TID + "rc"), "w") as f:
    f.write(f"""[General]
ActiveTextColor=255,255,255
InactiveTextColor={"150,150,150" if DARK else "192,192,192"}
UseTextShadow=false
HaloActive=false
HaloInactive=false
TitleAlignment=Left
TitleVerticalAlignment=Center
Animation=0
Shadow=false
DecorationPosition=0

[Layout]
BorderLeft=4
BorderRight=4
BorderBottom=4
BorderTop=0
TitleEdgeTop={FRAME}
TitleEdgeBottom={GAP}
TitleEdgeLeft={FRAME}
TitleEdgeRight={FRAME}
TitleEdgeTopMaximized=0
TitleEdgeBottomMaximized=0
TitleEdgeLeftMaximized=2
TitleEdgeRightMaximized=2
TitleBorderLeft=3
TitleBorderRight=3
TitleHeight={TITLE_H}
ButtonWidth={BW}
ButtonHeight={BH}
ButtonWidthMenu=16
ButtonSpacing=0
ButtonMarginTop=2
ButtonMarginTopMaximized=2
ExplicitButtonSpacer=2
PaddingLeft=0
PaddingRight=0
PaddingTop=0
PaddingBottom=0
""")
print("aurorae ->", OUT)
