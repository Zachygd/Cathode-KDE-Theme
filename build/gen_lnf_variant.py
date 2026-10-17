#!/usr/bin/env python3
"""Derive a colour variant of the Cathode global theme from the light one.

Usage: gen_lnf_variant.py VARIANT
  dark -> plasma/look-and-feel/org.cathode.desktop.dark

Everything except the colour choices is shared with the light package, so the
layout, logout dialog and previews stay in sync. The boot splash is reused from
the light package (it is black either way).
"""
import json
import os
import shutil
import sys

VARIANTS = {
    "dark": dict(
        suffix=".dark", name="Cathode Dark",
        description="Cathode - a Windows 98 style desktop, dark",
        scheme="Cathode98Dark", plasma="Cathode98Dark", aurorae="Cathode98Dark",
        desktop="0,72,72",
    ),
}

v = VARIANTS[sys.argv[1]]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "plasma/look-and-feel/org.cathode.desktop")
DST = SRC + v["suffix"]

if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("splash", "previews"))
os.makedirs(os.path.join(DST, "contents", "previews"), exist_ok=True)

with open(os.path.join(SRC, "metadata.json")) as f:
    meta = json.load(f)
meta["KPlugin"]["Id"] = "org.cathode.desktop" + v["suffix"]
meta["KPlugin"]["Name"] = v["name"]
meta["KPlugin"]["Description"] = v["description"]
with open(os.path.join(DST, "metadata.json"), "w") as f:
    json.dump(meta, f, indent=4)

p = os.path.join(DST, "contents", "defaults")
s = open(p).read()
s = s.replace("ColorScheme=Cathode98\n", f"ColorScheme={v['scheme']}\n")
s = s.replace("[plasmarc][Theme]\nname=Cathode98\n", f"[plasmarc][Theme]\nname={v['plasma']}\n")
s = s.replace("theme=__aurorae__svg__Cathode98\n", f"theme=__aurorae__svg__{v['aurorae']}\n")
assert v["scheme"] in s and v["plasma"] in s and v["aurorae"] in s, "defaults not updated"
open(p, "w").write(s)

for name in os.listdir(os.path.join(DST, "contents", "layouts")):
    p = os.path.join(DST, "contents", "layouts", name)
    s = open(p).read()
    s = s.replace('d.writeConfig("Color", "0,128,128");', f'd.writeConfig("Color", "{v["desktop"]}");')
    # (the Start button picks its dark image by itself)
    assert v["desktop"] in s, "layout not updated: " + name
    open(p, "w").write(s)

print("global theme ->", DST)
