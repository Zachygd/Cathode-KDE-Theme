#!/usr/bin/env python3
"""Render a preview of the Aurorae decoration the way aurorae v2 lays it out."""
import os
import sys
import configparser

sys.path.insert(0, os.path.dirname(__file__))
from framesim import SvgFile, FrameSvg, new_image  # noqa: E402
from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QImage  # noqa: E402

THEME = sys.argv[1]
OUT = sys.argv[2]
cfg = configparser.ConfigParser()
cfg.optionxform = str
cfg.read(os.path.join(THEME, "Cathode98rc"))
L = {k: int(v) for k, v in cfg["Layout"].items()}

deco = SvgFile(os.path.join(THEME, "decoration.svg"))
btn = {n: SvgFile(os.path.join(THEME, f"{n}.svg")) for n in ["minimize", "maximize", "restore", "close", "help"]}
for n, f in btn.items():
    for pre in ["active", "pressed", "inactive", "deactivated"]:
        miss = FrameSvg(f, pre).missing
        assert not miss, (n, pre, miss)
for pre in ["decoration", "decoration-inactive"]:
    miss = FrameSvg(deco, pre).missing
    assert not miss, (pre, miss)
assert deco.has("decoration-maximized-center") and deco.has("decoration-maximized-inactive-center")


def window(p, x, y, cw, ch, title, active=True, pressed=None, maximized=False, outer_w=None):
    """cw/ch = client size; draws decoration around it at (x, y)."""
    bl = 0 if maximized else L["BorderLeft"]
    br = 0 if maximized else L["BorderRight"]
    bb = 0 if maximized else L["BorderBottom"]
    edges = (L["TitleEdgeLeftMaximized"], L["TitleEdgeTopMaximized"], L["TitleEdgeRightMaximized"], L["TitleEdgeBottomMaximized"]) if maximized \
        else (L["TitleEdgeLeft"], L["TitleEdgeTop"], L["TitleEdgeRight"], L["TitleEdgeBottom"])
    title_h = max(L["TitleHeight"], L["ButtonHeight"] + L["ButtonMarginTop"])
    bt = title_h + edges[1] + edges[3]
    W, H = cw + bl + br, ch + bt + bb
    if maximized:
        pre = "decoration-maximized" if active else "decoration-maximized-inactive"
        FrameSvg(deco, pre).paint(p, x, y, W, H, borders=False)
    else:
        pre = "decoration" if active else "decoration-inactive"
        FrameSvg(deco, pre).paint(p, x, y, W, H)
    # client
    p.fillRect(QRectF(x + bl, y + bt, cw, ch), QColor("#ffffff"))
    # buttons (right group: minimize, maximize, spacer, close); left: window icon
    inner_x, inner_y = x + edges[0], y + edges[1]
    inner_w = W - edges[0] - edges[2]
    margin = L["ButtonMarginTopMaximized"] if maximized else L["ButtonMarginTop"]
    order = ["minimize", "restore" if maximized else "maximize", "_", "close"]
    widths = [L["ButtonWidth"] if b != "_" else L["ExplicitButtonSpacer"] for b in order]
    total = sum(widths) + L["ButtonSpacing"] * (len(order) - 1)
    bx = inner_x + inner_w - total
    for b, w in zip(order, widths):
        if b != "_":
            state = "pressed" if pressed == b else ("active" if active else "inactive")
            FrameSvg(btn[b], state).paint(p, bx, inner_y + margin, w, L["ButtonHeight"])
        bx += w + L["ButtonSpacing"]
    # window icon (menu button) on the left
    icon = QImage(os.path.join(os.path.dirname(THEME), "..", "..", "icons", "Cathode", "apps", "16", "cathode-logo.png"))
    p.drawImage(QRectF(inner_x + 1, inner_y + margin, 14, 14), icon)
    # caption
    cap_left = inner_x + L["ButtonWidthMenu"] + L["TitleBorderLeft"]
    cap_right = x + W - edges[2] - total - L["TitleBorderRight"]
    f = QFont("DejaVu Sans")
    f.setPixelSize(11)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#ffffff" if active else "#c0c0c0"))
    p.drawText(QRectF(cap_left, y + edges[1], cap_right - cap_left, title_h), Qt.AlignLeft | Qt.AlignVCenter, title)
    return W, H


img = new_image(760, 330)
p = QPainter(img)
window(p, 20, 20, 300, 160, "My Computer", active=True)
window(p, 350, 20, 300, 160, "Untitled - Notepad", active=False)
window(p, 20, 240, 300, 40, "Pressed close", active=True, pressed="close")
window(p, 350, 240, 390, 40, "Maximized window", active=True, maximized=True)
p.end()
big = img.scaled(img.width() * 2, img.height() * 2, Qt.IgnoreAspectRatio, Qt.FastTransformation)
big.save(OUT)
print("saved", OUT)
