"""Minimal emulation of KSvg::FrameSvg using Qt's QSvgRenderer (same engine KDE uses).

Used only for previews/validation of the theme SVGs.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, QPointF, QSizeF, Qt
from PySide6.QtGui import QImage, QPainter, QColor, QFont, QGuiApplication
from PySide6.QtSvg import QSvgRenderer

_app = QGuiApplication.instance() or QGuiApplication([])

NAMES = ["topleft", "top", "topright", "left", "center", "right", "bottomleft", "bottom", "bottomright"]


ACCENT = os.environ.get("CATHODE_ACCENT")   # emulate KSvg recolouring for previews


class SvgFile:
    def __init__(self, path, accent=None):
        self.path = path
        accent = accent or ACCENT
        if accent:
            import re
            from PySide6.QtCore import QByteArray
            data = open(path, encoding="utf-8").read()
            data = re.sub(r"(\.ColorScheme-Highlight \{ color:)#[0-9a-fA-F]{6}", r"\g<1>" + accent, data)
            self.r = QSvgRenderer(QByteArray(data.encode()))
        else:
            self.r = QSvgRenderer(path)
        assert self.r.isValid(), path

    def has(self, eid):
        return self.r.elementExists(eid)

    def rect(self, eid):
        b = self.r.boundsOnElement(eid)
        m = self.r.transformForElement(eid)
        return m.mapRect(b)

    def render_element(self, p, eid, target):
        self.r.render(p, eid, target)

    def element_image(self, eid, w, h):
        img = QImage(max(1, int(w)), max(1, int(h)), QImage.Format_ARGB32_Premultiplied)
        img.fill(0)
        p = QPainter(img)
        self.r.render(p, eid, QRectF(0, 0, w, h))
        p.end()
        return img


class FrameSvg:
    def __init__(self, svgfile, prefix):
        self.s = svgfile
        self.prefix = prefix
        pre = prefix + "-" if prefix else ""
        self.pre = pre
        self.missing = [n for n in NAMES if not svgfile.has(pre + n)]
        self.stretch = svgfile.has("hint-stretch-borders") or svgfile.has(pre + "hint-stretch-borders")
        self.tile_center = svgfile.has("hint-tile-center") or svgfile.has(pre + "hint-tile-center")

    def size(self, n):
        if not self.s.has(self.pre + n):
            return QSizeF(0, 0)
        return self.s.rect(self.pre + n).size()

    def margins(self):
        l = self.size("left").width()
        t = self.size("top").height()
        r = self.size("right").width()
        b = self.size("bottom").height()
        return l, t, r, b

    def _tile(self, p, n, target):
        sz = self.size(n)
        if sz.width() <= 0 or sz.height() <= 0:
            return
        img = self.s.element_image(self.pre + n, sz.width(), sz.height())
        p.save()
        p.setClipRect(target)
        y = target.top()
        while y < target.bottom():
            x = target.left()
            while x < target.right():
                p.drawImage(QPointF(x, y), img)
                x += sz.width()
            y += sz.height()
        p.restore()

    def paint(self, p, x, y, w, h, borders=True):
        if not borders:
            self.s.render_element(p, self.pre + "center", QRectF(x, y, w, h))
            return
        l, t, r, b = self.margins()
        cw, ch = w - l - r, h - t - b
        cells = {
            "topleft": QRectF(x, y, l, t), "top": QRectF(x + l, y, cw, t), "topright": QRectF(x + w - r, y, r, t),
            "left": QRectF(x, y + t, l, ch), "center": QRectF(x + l, y + t, cw, ch), "right": QRectF(x + w - r, y + t, r, ch),
            "bottomleft": QRectF(x, y + h - b, l, b), "bottom": QRectF(x + l, y + h - b, cw, b), "bottomright": QRectF(x + w - r, y + h - b, r, b),
        }
        for n, rc in cells.items():
            if rc.width() <= 0 or rc.height() <= 0 or not self.s.has(self.pre + n):
                continue
            corner = n in ("topleft", "topright", "bottomleft", "bottomright")
            if corner or (n != "center" and self.stretch) or (n == "center" and not self.tile_center):
                # render element image at native size, then scale (like KSvg)
                sz = self.size(n)
                if corner:
                    self.s.render_element(p, self.pre + n, rc)
                else:
                    img = self.s.element_image(self.pre + n, sz.width(), sz.height())
                    p.drawImage(rc, img)
            else:
                self._tile(p, n, rc)


def new_image(w, h, color="#008080"):
    img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    img.fill(QColor(color))
    return img
