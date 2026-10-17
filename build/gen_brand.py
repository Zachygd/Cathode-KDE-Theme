#!/usr/bin/env python3
"""Cathode loading-screen assets from the animation frames + static logo.

  * Plasma splash: one horizontal sprite strip for QML AnimatedSprite
  * Plymouth boot theme: numbered frames, progress-bar image, script, .plymouth

Usage: gen_brand.py FRAMES_DIR STATIC_LOGO.png SPLASH_IMAGES_DIR PLYMOUTH_DIR
"""
import glob
import os
import shutil
import sys
from PIL import Image

FRAMES, LOGO, SPLASH, PLY = sys.argv[1:5]
os.makedirs(SPLASH, exist_ok=True)
os.makedirs(PLY, exist_ok=True)

frames = [Image.open(p).convert("RGBA") for p in sorted(glob.glob(os.path.join(FRAMES, "frame-*.png")))]
w, h = frames[0].size

# Plasma splash strip
strip = Image.new("RGBA", (w * len(frames), h))
for i, f in enumerate(frames):
    strip.paste(f, (i * w, 0))
strip.save(os.path.join(SPLASH, "cathode-anim.png"))
for old in ("logo.png",):
    p = os.path.join(SPLASH, old)
    if os.path.exists(p):
        os.remove(p)

# Plymouth frames + bar
for i, f in enumerate(frames, 1):
    f.save(os.path.join(PLY, f"frame-{i}.png"))
bar = Image.new("RGBA", (256, 4))
stops = [(0.0, (0x01, 0x11, 0x8d)), (0.5, (0x0c, 0x6e, 0xec)), (1.0, (0x0c, 0xec, 0xfb))]
for x in range(256):
    t = x / 255
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t0 <= t <= t1:
            k = (t - t0) / (t1 - t0)
            col = tuple(round(a + (b - a) * k) for a, b in zip(c0, c1))
    for y in range(4):
        bar.putpixel((x, y), col + (255,))
bar.save(os.path.join(PLY, "bar.png"))

here = os.path.dirname(os.path.abspath(__file__))
shutil.copy(os.path.join(here, "plymouth", "cathode.script"), PLY)
shutil.copy(os.path.join(here, "plymouth", "cathode.plymouth"), PLY)
print("splash strip", strip.size, "| plymouth frames", len(frames), "->", PLY)
