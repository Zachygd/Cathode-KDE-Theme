#!/usr/bin/env python3
"""Write a KDE .colors file for every Cathode scheme, light and dark.

Usage: gen_colors.py OUT_DIR
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from schemes import ALL, comma, theme_id, theme_name  # noqa: E402

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

HEADER = """[ColorEffects:Disabled]
Color={dis}
ColorAmount=0
ColorEffect=0
ContrastAmount=0.55
ContrastEffect=1
IntensityAmount=0
IntensityEffect=0

[ColorEffects:Inactive]
ChangeSelectionColor=false
Color={dis}
ColorAmount=0
ColorEffect=0
ContrastAmount=0
ContrastEffect=0
Enable=false
IntensityAmount=0
IntensityEffect=0

"""


def group(name, bg, alt, fg, inactive, active, link, visited, neg, neu, pos, focus, hover):
    return f"""[{name}]
BackgroundAlternate={alt}
BackgroundNormal={bg}
DecorationFocus={focus}
DecorationHover={hover}
ForegroundActive={active}
ForegroundInactive={inactive}
ForegroundLink={link}
ForegroundNegative={neg}
ForegroundNeutral={neu}
ForegroundNormal={fg}
ForegroundPositive={pos}
ForegroundVisited={visited}

"""


def scheme_text(s, dark):
    sel, deep, tip = comma(s["sel"]), comma(s["deep"]), comma(s["tip"])
    if dark:
        face, alt, view, tipbg = "58,58,58", "70,70,70", "42,42,42", "48,48,42"
        link = comma(s["link_dark"])
        std = dict(fg="232,232,232", inactive="150,150,150", active=link, link=link, visited="180,150,255",
                   neg="255,110,110", neu="235,200,70", pos="120,210,120", focus=sel, hover=tip)
        inact_bg, inact_blend, inact_fg = "44,44,44", "78,78,78", "150,150,150"
        desk = comma(s["desk_dark"])
    else:
        face, alt, view, tipbg = "192,192,192", "223,223,223", "244,243,239", "255,255,225"
        link = comma(s["link_light"])
        std = dict(fg="0,0,0", inactive="128,128,128", active=link, link=link, visited="128,0,128",
                   neg="128,0,0", neu="128,128,0", pos="0,128,0", focus="0,0,0", hover=sel)
        inact_bg, inact_blend, inact_fg = "128,128,128", "192,192,192", "192,192,192"
        desk = comma(s["desk_light"])

    out = HEADER.format(dis=face)
    out += group("Colors:Button", face, alt, **std)
    # Complementary = the desktop colour (the lock screen paints its background with it)
    out += group("Colors:Complementary", desk, deep, fg="255,255,255", inactive="192,192,192", active="255,255,255",
                 link="255,255,0", visited="255,192,255", neg="255,110,110", neu="255,235,120", pos="120,255,120",
                 focus="255,255,255", hover=tip)
    out += group("Colors:Header", face, face, **std)
    out += group("Colors:Header][Inactive", face, face, **std)
    out += group("Colors:Selection", sel, deep, fg="255,255,255", inactive="230,230,230", active="255,255,255",
                 link="230,240,255", visited="240,220,255", neg="255,170,170", neu="255,235,120", pos="170,255,170",
                 focus=sel, hover=tip)
    out += group("Colors:Tooltip", tipbg, tipbg, **std)
    out += group("Colors:View", view, view, **std)
    out += group("Colors:Window", face, alt, **std)
    out += f"""[General]
ColorScheme={theme_id(s["slug"], dark)}
Name={theme_name(s["slug"], dark)}
shadeSortColumn=false

[KDE]
contrast=10

[WM]
activeBackground={deep}
activeBlend={tip}
activeForeground=255,255,255
inactiveBackground={inact_bg}
inactiveBlend={inact_blend}
inactiveForeground={inact_fg}
"""
    return out


n = 0
for s in ALL:
    for dark in (False, True):
        with open(os.path.join(OUT, theme_id(s["slug"], dark) + ".colors"), "w") as f:
            f.write(scheme_text(s, dark))
        n += 1
print("colour schemes ->", OUT, n)
