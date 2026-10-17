#!/usr/bin/env python3
"""Build the Cathode icon theme (logo overrides on top of SE98).

Usage: gen_icons.py LOGO.png OUT_DIR [NAME INHERITS]
The Cathode logo replaces every Start / KDE / Fedora / distributor logo icon
(About This System reads LOGO=fedora-logo-icon from /etc/os-release).

With NAME/INHERITS it writes a small hidden icon theme holding only the logo,
used for the colour schemes ("Cathode-Brick" inherits "Cathode"), so the
schemes don't crowd System Settings' icon list.
"""
import os
import sys
from PIL import Image

logo_path, out = sys.argv[1:3]
name = sys.argv[3] if len(sys.argv) > 3 else "Cathode"
inherits = sys.argv[4] if len(sys.argv) > 4 else "SE98,breeze,hicolor"
hidden = len(sys.argv) > 3

NAMES = ["start-here-cathode", "start-here", "start-here-kde", "start-here-kde-plasma",
         "start-here-kde-symbolic", "start-here-symbolic", "start-here-fedora", "start-here-kde-fedora"]
DISTRO_NAMES = ["distributor-logo", "distributor-logo-cathode", "distributor-logo-fedora", "fedora-logo-icon"]
SIZES = [16, 22, 24, 32, 48, 64, 96, 128, 256, 512]


def square(im):
    a = im.getchannel("A").point(lambda v: 255 if v > 16 else 0)
    im = im.crop(a.getbbox())
    w, h = im.size
    s = max(w, h)
    canvas = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    canvas.paste(im, ((s - w) // 2, (s - h) // 2))
    return canvas


logo = square(Image.open(logo_path).convert("RGBA"))
dirs = []
for ctx, folder in [("Places", "places"), ("Applications", "apps")]:
    for s in SIZES:
        d = os.path.join(out, folder, str(s))
        os.makedirs(d, exist_ok=True)
        logo.resize((s, s), Image.LANCZOS).save(os.path.join(d, "cathode-logo.png"))
        for n in NAMES + DISTRO_NAMES:
            link = os.path.join(d, n + ".png")
            if os.path.lexists(link):
                os.remove(link)
            os.symlink("cathode-logo.png", link)
        dirs.append((f"{folder}/{s}", s, ctx))

with open(os.path.join(out, "index.theme"), "w") as f:
    f.write(f"[Icon Theme]\nName={name}\nComment=Cathode branding on top of the SE98 (Windows 98 SE style) icon theme\n")
    f.write(f"Inherits={inherits}\nExample=start-here\n" + ("Hidden=true\n" if hidden else "") + "\n")
    f.write("Directories=" + ",".join(d for d, _, _ in dirs) + "\n\n")
    for d, s, c in dirs:
        f.write(f"[{d}]\nSize={s}\nContext={c}\nType=Fixed\n\n")
print("icons ->", out)
