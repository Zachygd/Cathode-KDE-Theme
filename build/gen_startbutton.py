#!/usr/bin/env python3
"""Win98-style Start button images (Cathode logo + bold "Start") for the Start menu.

The bevel and the pixel-font "Start" are drawn on a 1x grid and enlarged 4x with
nearest-neighbour; the logo is painted at 4x from the full-resolution artwork.
4x keeps it sharp on fractional/HiDPI scaling and it downsamples cleanly at 100%.

Usage: gen_startbutton.py LOGO.png OUT_DIR
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from svgkit import Grid, FACE, DK, LT, HI, SH, TEXT, VARIANT, SCHEME  # noqa: E402

LOGO = sys.argv[1]
OUT = sys.argv[2]
SCALE = 4

FONT = {
    "S": [".xxxx.", "xx..xx", "xx....", ".xxxx.", "....xx", "....xx", "xx..xx", ".xxxx."],
    "t": ["....", ".xx.", "xxxx", ".xx.", ".xx.", ".xx.", ".xx.", "..xx"],
    "a": ["......", "......", ".xxxx.", "....xx", ".xxxxx", "xx..xx", "xx..xx", ".xxxxx"],
    "r": [".....", ".....", "xx.xx", "xxx..", "xx...", "xx...", "xx...", "xx..."],
}

H = 28      # 34px taskbar minus 3px margins
text = "Start"
text_w = sum(len(FONT[c][0]) for c in text) + (len(text) - 1)
LOGO_X, LOGO_W, LOGO_H = 5, 28, 17      # the Cathode "C" is wide, give it room
TEXT_X = LOGO_X + LOGO_W + 2
W = TEXT_X + text_w + 5


def tight(im):
    a = im.getchannel("A").point(lambda v: 255 if v > 24 else 0)
    return im.crop(a.getbbox())


logo_src = tight(Image.open(LOGO).convert("RGBA"))
lw, lh = logo_src.size
k = min(LOGO_W * SCALE / lw, LOGO_H * SCALE / lh)
logo = logo_src.resize((max(1, round(lw * k)), max(1, round(lh * k))), Image.LANCZOS)

for state in ["normal", "pressed"]:
    g = Grid(W, H, FACE)
    dx = 0
    if state == "pressed":
        # pushed in, exactly like 98: black/gray shadow top-left, white bottom-right
        g.sunken(0, 0, W, H)
        dx = 1
    else:
        g.raised(0, 0, W, H)
    x = TEXT_X + dx
    for c in text:
        g.bitmap(FONT[c], x, (H - 8) // 2 + dx, TEXT)
        x += len(FONT[c][0]) + 1
    img = Image.new("RGBA", (W, H))
    px = img.load()
    for j in range(H):
        for i in range(W):
            c = g.px[j][i]
            if c:
                px[i, j] = tuple(int(c[q:q + 2], 16) for q in (1, 3, 5)) + (255,)
    big = img.resize((W * SCALE, H * SCALE), Image.NEAREST)
    lx = (LOGO_X + dx) * SCALE + (LOGO_W * SCALE - logo.width) // 2
    ly = (H * SCALE - logo.height) // 2 + dx * SCALE
    big.alpha_composite(logo, (lx, ly))
    # OUT/<scheme>[-dark][-pressed].png  (the Start menu picks the right one)
    name = SCHEME + ("-dark" if VARIANT == "dark" else "") + ("-pressed" if state == "pressed" else "") + ".png"
    os.makedirs(OUT, exist_ok=True)
    big.save(os.path.join(OUT, name))
    print(name, big.size)
