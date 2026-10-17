#!/usr/bin/env python3
"""Recolour the blue Cathode logo for every scheme.

  * single-colour schemes: hue shift from the logo's blue to the scheme hue
  * Slate: desaturated silver
  * Spectrum / Sunset: hue sweeps left-to-right across the logo

Usage: gen_logos.py LOGO.png OUT_DIR   ->  OUT_DIR/<slug>.png
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from schemes import ALL, LOGO_BASE_HUE  # noqa: E402

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert("RGBA")
a = im.getchannel("A").point(lambda v: 255 if v > 16 else 0)
im = im.crop(a.getbbox())
im.thumbnail((1024, 1024), Image.LANCZOS)
alpha = np.array(im.getchannel("A"))
hsv = np.array(im.convert("RGB").convert("HSV")).astype(np.float64)   # H,S,V in 0..255
H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
w = H.shape[1]
xfrac = np.tile(np.linspace(0, 1, w), (H.shape[0], 1))


def deg(d):
    return d / 360 * 255


for s in ALL:
    o = s["opts"]
    h2, s2, v2 = H.copy(), S.copy(), V.copy()
    if s["slug"] == "cathode":
        pass
    elif o.get("logo") == "spectrum":
        # red on the left (the pixel trail) through to violet at the star
        h2 = deg(0) + xfrac * deg(275) + (H - deg(LOGO_BASE_HUE)) * 0.25
    elif o.get("logo") == "sunset":
        # magenta -> pink -> orange (hue 300 -> 400 i.e. 40)
        h2 = (deg(300) + xfrac * deg(100) + (H - deg(LOGO_BASE_HUE)) * 0.25) % 255
    elif o.get("gray"):
        s2 = S * 0.08
        v2 = np.clip(V * 1.05, 0, 255)
    else:
        # shift to the scheme hue and narrow the logo's cyan-to-violet spread so the
        # colour reads evenly (a plain shift turns red into pink at the edges)
        h2 = (deg(o.get("logo_hue", o["hue"])) + (H - deg(LOGO_BASE_HUE)) * 0.45) % 255
        # yellows and greens read darker than blue at the same value; lift them a little
        if 30 <= o["hue"] <= 100:
            v2 = np.clip(V * 1.08, 0, 255)
    out = np.stack([h2 % 255, s2, v2], axis=-1).astype(np.uint8)
    rgb = Image.fromarray(out, "HSV").convert("RGB")
    rgb.putalpha(Image.fromarray(alpha))
    rgb.save(os.path.join(OUT, s["slug"] + ".png"))
print("logos ->", OUT, len(ALL))
