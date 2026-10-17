#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from framesim import SvgFile, FrameSvg, new_image
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QColor, QFont, QImage
base = sys.argv[1]; out = sys.argv[2]
icons = sys.argv[3]
Wd, PH = 640, 28
img = new_image(Wd, 120)
p = QPainter(img)
panel = FrameSvg(SvgFile(f"{base}/widgets/panel-background.svg"), "south")
y0 = 120 - PH
panel.paint(p, -2, y0, Wd + 4, PH + 2)
sb = QImage("share/cathode/start-button.png")
p.drawImage(QRectF(2, y0 + 3, sb.width() / 2, 22), sb)
tasks = SvgFile(f"{base}/widgets/tasks.svg")
f = QFont("DejaVu Sans"); f.setPixelSize(11); p.setFont(f)
x = 2 + sb.width() / 2 + 4
for kind, label, ic in [("focus", "My Computer", "devices/16/computer.png"), ("normal", "Untitled - Notepad", "apps/16/accessories-text-editor.png"), ("minimized", "Konsole", "apps/16/utilities-terminal.png")]:
    w = 150
    FrameSvg(tasks, kind).paint(p, x, y0, w, PH)
    icon = QImage(f"{icons}/{ic}")
    off = 1 if kind == "focus" else 0
    p.drawImage(QRectF(x + 5 + off, y0 + 6 + off, 16, 16), icon)
    ff = QFont(f); ff.setBold(kind == "focus"); p.setFont(ff)
    p.setPen(QColor("#000000"))
    p.drawText(QRectF(x + 25 + off, y0 + 3 + off, w - 30, 22), Qt.AlignLeft | Qt.AlignVCenter, label)
    x += w
# tray: thin sunken box with clock
frame = FrameSvg(SvgFile(f"{base}/widgets/frame.svg"), "sunken")
frame.paint(p, Wd - 70, y0 + 3, 66, 22)
p.setFont(f); p.drawText(QRectF(Wd - 70, y0 + 3, 62, 22), Qt.AlignRight | Qt.AlignVCenter, "9:51 PM")
# start menu popup preview above start button
dlg = FrameSvg(SvgFile(f"{base}/dialogs/background.svg"), "")
dlg.paint(p, 2, 4, 170, y0 - 6)
vi = FrameSvg(SvgFile(f"{base}/widgets/viewitem.svg"), "hover")
items = [("Programs", "places/16/folder.png"), ("Documents", "places/16/folder-documents.png"), ("Settings", "apps/16/system-settings.png")]
yy = 8
for i, (t, ic) in enumerate(items):
    if i == 0: vi.paint(p, 5, yy, 164, 22)
    p.drawImage(QRectF(10, yy + 3, 16, 16), QImage(f"{icons}/{ic}"))
    p.setPen(QColor("#000000")); p.drawText(QRectF(32, yy, 120, 22), Qt.AlignLeft | Qt.AlignVCenter, t)
    yy += 22
line = SvgFile(f"{base}/widgets/line.svg")
line.render_element(p, "horizontal-line", QRectF(6, yy + 2, 162, 2))
p.end()
img.scaled(img.width() * 2, img.height() * 2, Qt.IgnoreAspectRatio, Qt.FastTransformation).save(out)
