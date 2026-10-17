#!/usr/bin/env python3
"""Compose an 800x600 Cathode desktop mockup from the real theme SVGs/icons."""
import configparser
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import schemes  # noqa: E402
SCHEME = os.environ.get("CATHODE_SCHEME", "cathode")
SC = schemes.BY_SLUG[SCHEME]
os.environ["CATHODE_ACCENT"] = SC["sel"]   # framesim recolours highlight pieces like KSvg does
from framesim import SvgFile, FrameSvg, new_image  # noqa: E402
from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QPainter, QColor, QFont, QImage  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SE98 = sys.argv[1]
OUT = sys.argv[2]
DARK = os.environ.get("CATHODE_VARIANT") == "dark"
TID = schemes.theme_id(SCHEME, DARK)
AUR = os.path.join(ROOT, "aurorae/themes", TID)
PL = os.path.join(ROOT, "plasma/desktoptheme", "Cathode98Dark" if DARK else "Cathode98")
C = dict(face="#3a3a3a", view="#2a2a2a", text="#e8e8e8", desk=SC["desk_dark"], inact="#969696") if DARK else \
    dict(face="#c0c0c0", view="#f4f3ef", text="#000000", desk=SC["desk_light"], inact="#c0c0c0")
SB = "start/" + SCHEME + ("-dark" if DARK else "")
SIZE = os.environ.get("PREVIEW_SIZE")   # e.g. "400x300": scale the finished mockup
cfg = configparser.ConfigParser(); cfg.optionxform = str
cfg.read(os.path.join(AUR, TID + "rc"))
L = {k: int(v) for k, v in cfg["Layout"].items()}

deco = SvgFile(f"{AUR}/decoration.svg")
btn = {n: SvgFile(f"{AUR}/{n}.svg") for n in ["minimize", "maximize", "close"]}
font = QFont("Tahoma"); font.setPixelSize(11)
bold = QFont(font); bold.setBold(True)


def icon(rel, size):
    return QImage(os.path.join(SE98, rel.replace("SIZE", str(size))))


def window(p, x, y, cw, ch, title, ic, active=True):
    bl, br, bb = L["BorderLeft"], L["BorderRight"], L["BorderBottom"]
    bt = L["TitleHeight"] + L["TitleEdgeTop"] + L["TitleEdgeBottom"]
    W, H = cw + bl + br, ch + bt + bb
    FrameSvg(deco, "decoration" if active else "decoration-inactive").paint(p, x, y, W, H)
    ix, iy = x + L["TitleEdgeLeft"], y + L["TitleEdgeTop"] + L["ButtonMarginTop"]
    order = ["minimize", "maximize", "_", "close"]
    widths = [L["ButtonWidth"] if b != "_" else L["ExplicitButtonSpacer"] for b in order]
    bx = x + W - L["TitleEdgeRight"] - sum(widths)
    for b, w in zip(order, widths):
        if b != "_":
            FrameSvg(btn[b], "active" if active else "inactive").paint(p, bx, iy, w, L["ButtonHeight"])
        bx += w
    p.drawImage(QRectF(ix + 1, iy, 14, 14), icon(ic, 16))
    p.setFont(bold); p.setPen(QColor("#ffffff" if active else C["inact"]))
    p.drawText(QRectF(ix + 16 + L["TitleBorderLeft"], y + L["TitleEdgeTop"], W - 80, L["TitleHeight"]),
               Qt.AlignLeft | Qt.AlignVCenter, title)
    return x + bl, y + bt, cw, ch


img = new_image(800, 600, C["desk"])
p = QPainter(img)

# desktop icons
for i, (rel, label) in enumerate([("devices/SIZE/computer.png", "My Computer"),
                                  ("places/SIZE/folder-documents.png", "My Documents"),
                                  ("places/SIZE/user-trash.png", "Recycle Bin"),
                                  ("places/SIZE/network-workgroup.png", "Network")]):
    yy = 12 + i * 70
    p.drawImage(QRectF(24, yy, 32, 32), icon(rel, 32))
    p.setFont(font); p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, yy + 34, 80, 28), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, label)

# a background window (inactive) and an active Explorer-style window
cx, cy, cw, ch = window(p, 360, 70, 380, 200, "Untitled - Notepad", "apps/SIZE/accessories-text-editor.png", active=False)
p.fillRect(QRectF(cx, cy, cw, ch), QColor(C["view"]))
cx, cy, cw, ch = window(p, 120, 150, 440, 280, "My Computer", "devices/SIZE/computer.png", active=True)
p.fillRect(QRectF(cx, cy, cw, ch), QColor(C["face"]))
p.setFont(font); p.setPen(QColor(C["text"]))
mx = cx + 8
for m in ["File", "Edit", "View", "Go", "Favorites", "Help"]:
    p.drawText(QRectF(mx, cy + 2, 80, 16), Qt.AlignLeft | Qt.AlignVCenter, m)
    mx += p.fontMetrics().horizontalAdvance(m) + 14
frame = FrameSvg(SvgFile(f"{PL}/widgets/frame.svg"), "sunken")
p.fillRect(QRectF(cx + 2, cy + 22, cw - 4, ch - 46), QColor(C["view"]))
frame.paint(p, cx + 2, cy + 22, cw - 4, ch - 46)
for i, (rel, label) in enumerate([("devices/SIZE/media-floppy.png", "3½ Floppy (A:)"),
                                  ("devices/SIZE/drive-harddisk.png", "Fedora (C:)"),
                                  ("devices/SIZE/drive-optical.png", "CD-ROM (D:)"),
                                  ("apps/SIZE/system-settings.png", "Control Panel")]):
    xx = cx + 20 + i * 100
    p.drawImage(QRectF(xx + 24, cy + 40, 32, 32), icon(rel, 32))
    p.drawText(QRectF(xx, cy + 76, 80, 30), Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, label)
FrameSvg(SvgFile(f"{PL}/widgets/frame.svg"), "sunken").paint(p, cx + 2, cy + ch - 21, cw - 4, 19)
p.drawText(QRectF(cx + 8, cy + ch - 21, 200, 19), Qt.AlignLeft | Qt.AlignVCenter, "4 object(s)")

# taskbar
PH = 34; y0 = 600 - PH; AH = PH - 6
FrameSvg(SvgFile(f"{PL}/widgets/panel-background.svg"), "south").paint(p, -2, y0, 804, PH + 2)
MENU_OPEN = os.environ.get("MENU_OPEN") == "1"
sb = QImage(os.path.join(ROOT, f"share/cathode/{SB}-pressed.png" if MENU_OPEN else f"share/cathode/{SB}.png"))
p.drawImage(QRectF(2, y0 + 3, sb.width() / 4, AH), sb)
x = 2 + sb.width() / 4 + 6
for rel in ["apps/SIZE/system-file-manager.png", "apps/SIZE/utilities-terminal.png"]:
    p.drawImage(QRectF(x, y0 + 9, 16, 16), icon(rel, 16)); x += 22
x += 4
tasks = SvgFile(f"{PL}/widgets/tasks.svg")
for kind, label, rel in [("focus", "My Computer", "devices/SIZE/computer.png"),
                         ("normal", "Untitled - Notepad", "apps/SIZE/accessories-text-editor.png")]:
    w = 160
    FrameSvg(tasks, kind).paint(p, x, y0, w, PH)
    off = 1 if kind == "focus" else 0
    p.drawImage(QRectF(x + 5 + off, y0 + 9 + off, 16, 16), icon(rel, 16))
    p.setFont(bold if kind == "focus" else font); p.setPen(QColor(C["text"]))
    p.drawText(QRectF(x + 25 + off, y0 + 3 + off, w - 34, AH), Qt.AlignLeft | Qt.AlignVCenter, label)
    x += w
p.setFont(font)
# notification area: tray icons + Cathode Clock's sunken box around both
p.drawImage(QRectF(800 - 120, y0 + 9, 16, 16), icon("status/SIZE/audio-volume-high.png", 16))
p.drawImage(QRectF(800 - 100, y0 + 9, 16, 16), icon("devices/SIZE/network-wired.png", 16))
FrameSvg(SvgFile(f"{PL}/widgets/frame.svg"), "sunken").paint(p, 800 - 124, y0 + 3, 122, AH)
p.setPen(QColor(C["text"]))
p.drawText(QRectF(800 - 80, y0 + 3, 72, AH), Qt.AlignRight | Qt.AlignVCenter, "9:51 PM")

if MENU_OPEN:
    from PySide6.QtGui import QLinearGradient, QTransform
    mw, mh = 196, 186
    mx, my = 2, y0 - mh
    FrameSvg(SvgFile(f"{PL}/dialogs/background.svg"), "").paint(p, mx, my, mw, mh)
    g = QLinearGradient(0, my + 3, 0, my + mh - 3)
    for pos, col in SC["title"]:
        g.setColorAt(1 - pos, QColor(col))
    p.fillRect(QRectF(mx + 3, my + 3, 22, mh - 6), g)
    p.save()
    bf = QFont(bold); bf.setPixelSize(17); p.setFont(bf); p.setPen(QColor("#ffffff"))
    p.translate(mx + 3 + 3, my + mh - 3 - 6); p.rotate(-90)
    p.drawText(0, 16, "Cathode")
    p.restore()
    hover = FrameSvg(SvgFile(f"{PL}/widgets/viewitem.svg"), "hover")
    items = [("Programs", "places/SIZE/folder.png", True), ("Documents", "places/SIZE/folder-documents.png", True),
             ("Settings", "apps/SIZE/system-settings.png", True), ("Find", "apps/SIZE/system-search.png", True),
             ("Help", "apps/SIZE/help-browser.png", False), ("Run...", "actions/SIZE/system-run.png", False),
             (None, None, False), ("Shut Down...", "actions/SIZE/system-shutdown.png", False)]
    yy = my + 5
    p.setFont(font)
    for i, (t, ic, arrow) in enumerate(items):
        if t is None:
            SvgFile(f"{PL}/widgets/line.svg").render_element(p, "horizontal-line", QRectF(mx + 30, yy + 3, mw - 36, 2))
            yy += 8
            continue
        if i == 0:
            hover.paint(p, mx + 27, yy, mw - 30, 22)
        im = icon(ic, 16)
        if not im.isNull():
            p.drawImage(QRectF(mx + 32, yy + 3, 16, 16), im)
        p.setPen(QColor(C["text"]))
        p.drawText(QRectF(mx + 54, yy, 120, 22), Qt.AlignLeft | Qt.AlignVCenter, t)
        if arrow:
            p.drawText(QRectF(mx + mw - 20, yy, 12, 22), Qt.AlignCenter, "\u25b8")
        yy += 22
p.end()
if SIZE:
    w, h = (int(v) for v in SIZE.split("x"))
    img = img.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
img.save(OUT)
print("saved", OUT)
