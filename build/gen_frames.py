#!/usr/bin/env python3
"""Slice the Cathode logo storyboard (4x4) into aligned animation frames.

The storyboard rows are not evenly spaced, and the artwork drifts a little
between panels, so each frame is cropped from its real row and then aligned to
frame 1 with phase correlation. Panel number labels are erased.

Usage: gen_frames.py STORYBOARD.png OUT_DIR
"""
import os
import sys
import numpy as np
from PIL import Image

SB, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
img = np.array(Image.open(SB).convert("RGBA")).astype(np.float64)

COL_W = 384
ROW_STARTS = [0, 241, 491, 739]      # measured grid lines at ~239, ~488, ~736
H, W = 232, COL_W - 6

crops = []
for r, y0 in enumerate(ROW_STARTS):
    for c in range(4):
        a = img[y0 + 3:y0 + 3 + H, c * COL_W + 3:c * COL_W + 3 + W].copy()
        crops.append(a)

# Soft-edged eraser for the panel numbers ("01".."16") in each top-left corner
from PIL import ImageFilter
_m = Image.new("L", (W, H), 255)
_m.paste(0, (0, 0, 56, 34))
LABEL_MASK = np.array(_m.filter(ImageFilter.GaussianBlur(5))).astype(np.float64) / 255.0
for a in crops:
    a[..., 3] *= LABEL_MASK


def lum(a):
    return a[..., :3].mean(axis=2) * a[..., 3] / 255.0


ref = np.fft.fft2(lum(crops[0]))
aligned = []
for a in crops:
    R = ref * np.conj(np.fft.fft2(lum(a)))
    R /= np.abs(R) + 1e-9
    corr = np.fft.ifft2(R).real
    dy, dx = np.unravel_index(corr.argmax(), corr.shape)
    if dy > H // 2:
        dy -= H
    if dx > W // 2:
        dx -= W
    out = np.zeros_like(a)
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = a[ys, xs]
    aligned.append((out, (int(dx), int(dy))))

# Feather the edges: the panels carry a faint dark-blue tint that would show as
# a rectangle on a pure black screen.
FEATHER = 28
yy = np.minimum(np.arange(H), np.arange(H)[::-1])[:, None]
xx = np.minimum(np.arange(W), np.arange(W)[::-1])[None, :]
edge = np.clip(np.minimum(yy, xx) / FEATHER, 0, 1) ** 1.5
for a, _ in aligned:
    a[..., 3] *= edge

for i, (a, sh) in enumerate(aligned, 1):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, f"frame-{i:02d}.png"))
print("frames ->", OUT, [s for _, s in aligned])
