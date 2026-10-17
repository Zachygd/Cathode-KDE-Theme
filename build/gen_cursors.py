#!/usr/bin/env python3
"""Build the ModernXP X cursor theme (na0miluv/modernXP-cursor-theme, GPL-3.0)
without Inkscape/xcursorgen: resvg renders the SVGs (blur shadows included) and
this script writes the XCursor files itself.

Usage: gen_cursors.py /path/to/modernXP-cursor-theme OUT_DIR
"""
import io
import os
import re
import shutil
import struct
import sys

import resvg_py
from PIL import Image

SRC = os.path.join(sys.argv[1], "src")
OUT = sys.argv[2]
CUR = os.path.join(OUT, "cursors")

XCURSOR_IMAGE = 0xFFFD0002


def svg_path(name):
    for cand in (name, name.replace("_", "-"), name.replace("-", "_")):
        p = os.path.join(SRC, "svg", cand + ".svg")
        if os.path.exists(p):
            return p
    return None


def render(svg_name, size, cache={}):
    key = (svg_name, size)
    if key not in cache:
        with open(svg_path(svg_name)) as f:
            data = f.read()
        png = bytes(resvg_py.svg_to_bytes(svg_string=data, width=size, height=size))
        cache[key] = Image.open(io.BytesIO(png)).convert("RGBA")
    return cache[key]


def image_chunk(img, nominal, xhot, yhot, delay):
    w, h = img.size
    px = img.load()
    out = bytearray(struct.pack("<9I", 36, XCURSOR_IMAGE, nominal, 1, w, h, xhot, yhot, delay))
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            # XCursor stores premultiplied ARGB
            r, g, b = (r * a + 127) // 255, (g * a + 127) // 255, (b * a + 127) // 255
            out += struct.pack("<I", (a << 24) | (r << 16) | (g << 8) | b)
    return bytes(out)


def build_cursor(cfg_path, out_path):
    chunks = []
    with open(cfg_path) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 4:
                continue
            nominal, xhot, yhot = int(parts[0]), int(parts[1]), int(parts[2])
            # tolerate upstream typos like "96 /right-arrow.png"
            rest = " ".join(parts[3:])
            m = re.search(r"([\w.\-]+)\.png(?:\s+(\d+))?\s*$", rest)
            if not m:
                continue
            svg_name, delay = m.group(1), int(m.group(2) or 0)
            if svg_path(svg_name) is None:
                print("  skipping", os.path.basename(cfg_path), "- no", svg_name + ".svg")
                return False
            chunks.append((nominal, image_chunk(render(svg_name, nominal), nominal, xhot, yhot, delay)))
    ntoc = len(chunks)
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, ntoc)
    pos = 16 + ntoc * 12
    toc = bytearray()
    for nominal, data in chunks:
        toc += struct.pack("<III", XCURSOR_IMAGE, nominal, pos)
        pos += len(data)
    with open(out_path, "wb") as f:
        f.write(header + toc + b"".join(d for _, d in chunks))
    return True


if os.path.exists(OUT):
    shutil.rmtree(OUT)
os.makedirs(CUR)
cfgs = sorted(c for c in os.listdir(os.path.join(SRC, "config")) if c.endswith(".cursor"))
for c in cfgs:
    build_cursor(os.path.join(SRC, "config", c), os.path.join(CUR, c[:-7]))

# aliases: each line is "<alias> <existing cursor>"
with open(os.path.join(SRC, "cursorList")) as f:
    for line in f:
        parts = line.split()
        if len(parts) != 2:
            continue
        alias, target = parts
        if os.path.exists(os.path.join(CUR, alias)) or not os.path.exists(os.path.join(CUR, target)):
            continue
        os.symlink(target, os.path.join(CUR, alias))

with open(os.path.join(OUT, "index.theme"), "w") as f:
    f.write("[Icon Theme]\nName=ModernXP\nComment=Windows XP style cursors by na0miluv (GPL-3.0)\n")
shutil.copy(os.path.join(sys.argv[1], "LICENSE"), os.path.join(OUT, "LICENSE"))
print("cursors ->", OUT, len(cfgs), "cursors")
