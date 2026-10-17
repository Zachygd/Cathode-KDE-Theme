"""Tiny helpers for writing pixel-exact SVGs for KDE themes (Aurorae / Plasma).

Approach: paint a picture into a pixel Grid, then cut the grid into named
FrameSvg elements (prefix-topleft, prefix-top, ... prefix-center). Each element is
emitted as run-length rects, so edges stay crisp at 100% scale.
"""

import os

# ---------------------------------------------------------------------------
# Palettes. Pick one with the CATHODE_VARIANT environment variable before
# importing (default "light"). New colour variants only need a new entry here.
# ---------------------------------------------------------------------------
PALETTES = {
    "light": dict(
        LT="#dfdfdf",      # 3D light
        HI="#ffffff",      # 3D highlight
        FACE="#c0c0c0",    # button / window face
        SH="#808080",      # 3D shadow
        DK="#000000",      # 3D dark shadow
        TEXT="#000000",    # glyphs and text drawn into artwork
        FIELD="#f4f3ef",   # text fields / views (soft off-white)
        INFO="#ffffe1",    # tooltip
        INACT1="#808080", INACT2="#c0c0c0",   # inactive title gradient
        HOVER=("ACCENT", 0.30),   # menu hover: accent tint, black text stays readable
        THEME_ID="Cathode98", THEME_NAME="Cathode 98",
    ),
    "dark": dict(
        LT="#4a4a4a",
        HI="#686868",
        FACE="#3a3a3a",
        SH="#242424",
        DK="#000000",
        TEXT="#e8e8e8",
        FIELD="#2a2a2a",
        INFO="#30302a",
        INACT1="#2c2c2c", INACT2="#4e4e4e",
        HOVER=("ACCENT", 0.55),   # deeper accent tint: readable with light text
        THEME_ID="Cathode98Dark", THEME_NAME="Cathode 98 Dark",
    ),
}
VARIANT = os.environ.get("CATHODE_VARIANT", "light")
PAL = PALETTES[VARIANT]
globals().update(PAL)

NAVY = "#000080"
BLUE = "#1084d0"

# Cathode accents, sampled from the Cathode "C" logo
C_DEEP = "#01118d"    # deep navy
C_ROYAL = "#064ed8"   # royal blue  (selection)
C_AZURE = "#0c6eec"   # azure       (links, focus)
C_SKY = "#28aff3"     # sky         (title gradient tip)
C_CYAN = "#0cecfb"    # cyan        (sparks, splash bar)
C_ICE = "#acf0fa"     # ice
TITLE_STOPS = [(0.0, C_DEEP), (0.45, C_ROYAL), (1.0, C_SKY)]

# "ACCENT" in artwork means "the active colour scheme's highlight colour".
# KSvg recolours elements with class ColorScheme-Highlight at runtime, so one
# Plasma style follows whichever Cathode colour scheme is selected.
ACCENT = "ACCENT"
ACCENT_DEFAULT = os.environ.get("CATHODE_ACCENT", "#064ed8")   # used by previews only

# Optional per-scheme title gradient (CATHODE_SCHEME=<slug>)
SCHEME = os.environ.get("CATHODE_SCHEME", "cathode")
try:
    import schemes as _schemes
    TITLE_STOPS = _schemes.BY_SLUG[SCHEME]["title"]
except Exception:
    pass


class Grid:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def rect(self, x, y, w, h, c):
        for j in range(max(0, y), min(self.h, y + h)):
            for i in range(max(0, x), min(self.w, x + w)):
                self.px[j][i] = c

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def bevel(self, x, y, w, h, otl, obr, itl, ibr, face=None):
        if face is not None:
            self.rect(x, y, w, h, face)
        self.hline(x, y, w - 1, otl)
        self.vline(x, y, h - 1, otl)
        self.hline(x, y + h - 1, w, obr)
        self.vline(x + w - 1, y, h, obr)
        self.hline(x + 1, y + 1, w - 3, itl)
        self.vline(x + 1, y + 1, h - 3, itl)
        self.hline(x + 1, y + h - 2, w - 2, ibr)
        self.vline(x + w - 2, y + 1, h - 2, ibr)

    def raised(self, x, y, w, h, face=""):
        self.bevel(x, y, w, h, HI, DK, LT, SH, FACE if face == "" else face)

    def sunken(self, x, y, w, h, face=""):
        self.bevel(x, y, w, h, DK, HI, SH, LT, FACE if face == "" else face)

    def field(self, x, y, w, h, face=""):
        face = FIELD if face == "" else face
        self.bevel(x, y, w, h, SH, HI, DK, LT, face)

    def thin_raised(self, x, y, w, h, face=None):
        if face is not None:
            self.rect(x, y, w, h, face)
        self.hline(x, y, w - 1, HI)
        self.vline(x, y, h - 1, HI)
        self.hline(x, y + h - 1, w, SH)
        self.vline(x + w - 1, y, h, SH)

    def thin_sunken(self, x, y, w, h, face=None):
        if face is not None:
            self.rect(x, y, w, h, face)
        self.hline(x, y, w - 1, SH)
        self.vline(x, y, h - 1, SH)
        self.hline(x, y + h - 1, w, HI)
        self.vline(x + w - 1, y, h, HI)

    def bitmap(self, rows, x0, y0, c):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == "x":
                    self.rect(x0 + i, y0 + j, 1, 1, c)

    def dither(self, x, y, w, h, c1, c2):
        for j in range(h):
            for i in range(w):
                self.rect(x + i, y + j, 1, 1, c1 if (i + j) % 2 == 0 else c2)

    def runs(self, x0, y0, w, h, ox, oy):
        """Rects for the region (x0,y0,w,h) placed at (ox,oy) in the SVG.

        Two things keep scaled elements seamless (Plasma stretches these pieces,
        often by fractional factors):
          * identical runs on consecutive rows are merged into one tall rect,
            so solid areas are a single shape instead of 1px strips;
          * the opaque part of the element gets an underlay in its most common
            colour, so antialiased edges between shapes can never let the
            desktop show through.
        """
        def fill(c):
            col, op = (c if isinstance(c, tuple) else (c, None))
            opacity = f' fill-opacity="{op}"' if op is not None else ""
            if col == ACCENT:
                return f'class="ColorScheme-Highlight" style="fill:currentColor"{opacity}'
            return f'fill="{col}"{opacity}'

        # row runs
        rows = []
        for j in range(h):
            row = self.px[y0 + j]
            runs, i = [], 0
            while i < w:
                c = row[x0 + i]
                k = i
                while k < w and row[x0 + k] == c:
                    k += 1
                if c is not None:
                    runs.append((i, k - i, c))
                i = k
            rows.append(runs)

        # opaque underlay: bounding box of opaque pixels, if fully opaque inside
        out = []
        opaque = [(i, j) for j in range(h) for i in range(w)
                  if self.px[y0 + j][x0 + i] is not None and not isinstance(self.px[y0 + j][x0 + i], tuple)]
        if opaque:
            xs = [p[0] for p in opaque]
            ys = [p[1] for p in opaque]
            bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
            if len(opaque) == (bx1 - bx0 + 1) * (by1 - by0 + 1):
                counts = {}
                for i, j in opaque:
                    c = self.px[y0 + j][x0 + i]
                    counts[c] = counts.get(c, 0) + 1
                base = max(counts, key=counts.get)
                out.append(f'<rect x="{ox + bx0}" y="{oy + by0}" width="{bx1 - bx0 + 1}" height="{by1 - by0 + 1}" {fill(base)}/>')
            else:
                base = None
        else:
            base = None

        # merge identical runs vertically
        open_rects = {}
        merged = []
        for j, runs in enumerate(rows + [[]]):
            keys = set(runs)
            for key in list(open_rects):
                if key not in keys:
                    merged.append((key, open_rects.pop(key), j))
            for key in runs:
                if key not in open_rects:
                    open_rects[key] = j
        for (i, rw, c), ys, ye in merged:
            if c == base:
                continue
            out.append(f'<rect x="{ox + i}" y="{oy + ys}" width="{rw}" height="{ye - ys}" {fill(c)}/>')
        return out


class Svg:
    def __init__(self):
        self.defs = []
        self.body = []
        self.cursor_y = 0
        self.max_w = 0

    def gradient(self, gid, c1, c2=None, horizontal=True):
        """c1 may be a list of (offset, color) stops; otherwise c1 -> c2."""
        stops = c1 if isinstance(c1, list) else [(0.0, c1), (1.0, c2)]
        x2, y2 = ("1", "0") if horizontal else ("0", "1")
        self.defs.append(
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
            + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
            + "</linearGradient>"
        )

    def element(self, eid, items, transparent_box=None):
        """Add a named element. transparent_box=(x,y,w,h) forces element bounds
        (an invisible rect) so fully transparent regions still have a size."""
        if transparent_box:
            x, y, w, h = transparent_box
            items = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000000" fill-opacity="0"/>'] + list(items)
        self.body.append(f'<g id="{eid}">' + "".join(items) + "</g>")

    def frame(self, prefix, grid, borders, oy=None, ox=0, gap=4, center_items=None, side_items=None):
        """Cut a grid into the nine FrameSvg elements for `prefix`, laid out in a
        3x3 arrangement with gaps so element bounds never touch.

        borders = (left, top, right, bottom). center_items: optional extra
        svg (e.g. gradient rect) appended to the center element in local coords.
        side_items: dict name -> function(ox, oy, w, h) -> list of svg strings to
        append to that element (used for gradients).
        """
        if oy is None:
            oy = self.cursor_y
        L, T, R, B = borders
        W, H = grid.w, grid.h
        cw, ch = W - L - R, H - T - B
        cols = [(0, L), (L, cw), (L + cw, R)]
        rows = [(0, T), (T, ch), (T + ch, B)]
        names = [["topleft", "top", "topright"], ["left", "center", "right"], ["bottomleft", "bottom", "bottomright"]]
        y = oy
        side_items = side_items or {}
        for ri, (sy, sh) in enumerate(rows):
            x = ox
            for ci, (sx, sw) in enumerate(cols):
                name = names[ri][ci]
                if sw > 0 and sh > 0:
                    items = grid.runs(sx, sy, sw, sh, x, y)
                    if name in side_items:
                        items += side_items[name](x, y, sw, sh)
                    eid = f"{prefix}-{name}" if prefix else name
                    self.element(eid, items, transparent_box=(x, y, sw, sh))
                x += sw + gap
            y += sh + gap
        self.max_w = max(self.max_w, ox + W + 2 * gap)
        self.cursor_y = y + gap
        return y + gap

    def hint(self, name, w=4, h=4):
        y = self.cursor_y
        self.element(name, [], transparent_box=(0, y, w, h))
        self.cursor_y += h + 4

    def margins(self, prefix, left, top, right, bottom):
        """FrameSvg content-margin hints: element size = margin."""
        p = f"{prefix}-" if prefix else ""
        self.hint(f"{p}hint-left-margin", left, 1)
        self.hint(f"{p}hint-top-margin", 1, top)
        self.hint(f"{p}hint-right-margin", right, 1)
        self.hint(f"{p}hint-bottom-margin", 1, bottom)

    def write(self, path):
        w = max(self.max_w, 64)
        h = max(self.cursor_y, 16)
        with open(path, "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                f'viewBox="0 0 {w} {h}" shape-rendering="crispEdges">\n'
            )
            f.write('<defs><style type="text/css" id="current-color-scheme">'
                    f'.ColorScheme-Highlight {{ color:{ACCENT_DEFAULT}; }}</style>' + "".join(self.defs) + "</defs>\n")
            for b in self.body:
                f.write(b + "\n")
            f.write("</svg>\n")
