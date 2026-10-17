#!/usr/bin/env python3
"""Turn Plasma's Kicker (Application Menu) source into the "Cathode Start" plasmoid.

Run at install time against the Kicker QML that matches the installed Plasma
version, because Kicker's internals change between releases.

Changes made to Kicker:
  * new plugin id org.cathode.startmenu, packaged as a normal QML plasmoid
  * the custom button image swaps to "<name>-pressed.png" while the mouse is
    down or the menu is open, so the Start button looks pushed in like 98's
  * a vertical "Cathode" banner down the left edge of the menu
  * search shows only applications by default (no extra runner columns)

Usage: make_startmenu.py KICKER_SRC_DIR OUT_PACKAGE_DIR
Exit code 0 on success; non-zero means "fall back to stock Kicker".
"""
import json
import os
import re
import shutil
import sys

SRC, OUT = sys.argv[1], sys.argv[2]

if not os.path.isfile(os.path.join(SRC, "main.qml")) or not os.path.isfile(os.path.join(SRC, "CompactRepresentation.qml")):
    sys.exit("kicker source not found in " + SRC)

if os.path.exists(OUT):
    shutil.rmtree(OUT)
UI = os.path.join(OUT, "contents", "ui")
CFG = os.path.join(OUT, "contents", "config")
os.makedirs(UI)
os.makedirs(CFG)

qml_files = sorted(f for f in os.listdir(SRC) if f.endswith(".qml") and f != "config.qml")
for f in qml_files:
    shutil.copy(os.path.join(SRC, f), os.path.join(UI, f))
if os.path.isdir(os.path.join(SRC, "code")):
    shutil.copytree(os.path.join(SRC, "code"), os.path.join(UI, "code"))
shutil.copy(os.path.join(SRC, "config.qml"), os.path.join(CFG, "config.qml"))
shutil.copy(os.path.join(SRC, "main.xml"), os.path.join(CFG, "main.xml"))

# qmldir: ActionMenu is a singleton (CMake declared it in the compiled applet)
with open(os.path.join(UI, "qmldir"), "w") as f:
    for q in qml_files:
        name = q[:-4]
        if not name[:1].isupper():
            continue  # main.qml is loaded by Plasma directly, not as a type
        with open(os.path.join(UI, q)) as fh:
            is_singleton = "pragma Singleton" in fh.read()
        f.write(f"{'singleton ' if is_singleton else ''}{name} 1.0 {q}\n")

# --- metadata -----------------------------------------------------------------
with open(os.path.join(SRC, "metadata.json")) as f:
    meta = json.load(f)
kp = {k: v for k, v in meta.get("KPlugin", {}).items() if "[" not in k}
kp["Authors"] = [{"Name": "Eike Hein (Kicker)"}, {"Name": "Zach (Cathode changes)"}]
kp.update({
    "Id": "org.cathode.startmenu",
    "Name": "Cathode Start",
    "Description": "Windows 98 style Start menu (based on Plasma's Application Menu)",
    "Icon": "start-here-cathode",
    "License": "GPL-2.0-or-later",
})
kp.pop("BugReportUrl", None)
meta = {k: v for k, v in meta.items() if "[" not in k}
meta["KPlugin"] = kp
meta["KPackageStructure"] = "Plasma/Applet"
meta.setdefault("X-Plasma-API-Minimum-Version", "6.0")
with open(os.path.join(OUT, "metadata.json"), "w") as f:
    json.dump(meta, f, indent=4)

# --- scheme table (shared by the button and the banner) -----------------------------
# The Start button and banner follow the active colour scheme: the scheme is
# recognised from its selection colour (Kirigami.Theme.highlightColor).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from schemes import js_library  # noqa: E402

os.makedirs(os.path.join(UI, "code"), exist_ok=True)
with open(os.path.join(UI, "code", "cathodeschemes.js"), "w") as f:
    f.write(js_library())

# --- pressed Start button --------------------------------------------------------
p = os.path.join(UI, "CompactRepresentation.qml")
src = open(p).read()
old = re.search(r'\n([ \t]*)source: Plasmoid\.icon\.startsWith\("/"\) \? "file:" \+ Plasmoid\.icon\.split\("/"\)\.map\(encodeURIComponent\)\.join\("/"\) : ""', src)
if not old:
    sys.exit("could not find the button image source line in CompactRepresentation.qml")
ind = old.group(1)
new = (f'\n{ind}// Cathode: Start button image in the scheme colour, light/dark, pushed in while pressed or open\n'
       f'{ind}readonly property bool cathodeDark: Kirigami.Theme.backgroundColor.hslLightness < 0.5\n'
       f'{ind}readonly property string cathodeSlug: CathodeSchemes.scheme(Kirigami.Theme.highlightColor).slug\n'
       f'{ind}readonly property string cathodeImage: {{\n'
       f'{ind}    const state = (cathodeDark ? "-dark" : "") + ((mouseArea.pressed || kicker.expanded) ? "-pressed" : "") + ".png";\n'
       f'{ind}    let m = Plasmoid.icon.match(/^(.*\\/cathode\\/start)\\/[a-z]+(-dark)?(-pressed)?\\.png$/);\n'
       f'{ind}    if (m) return m[1] + "/" + cathodeSlug + state;\n'
       f'{ind}    m = Plasmoid.icon.match(/^(.*\\/cathode\\/start-button)(-dark)?(-pressed)?\\.png$/);  // pre-v6 path\n'
       f'{ind}    if (m) return m[1].replace(/start-button$/, "start/" + cathodeSlug) + state;\n'
       f'{ind}    return Plasmoid.icon;\n'
       f'{ind}}}\n'
       f'{ind}source: cathodeImage.startsWith("/") ? "file:" + cathodeImage.split("/").map(encodeURIComponent).join("/") : ""')
if "import org.kde.kirigami as Kirigami" not in src:
    sys.exit("CompactRepresentation.qml does not import Kirigami")
src = src[:old.start()] + new + src[old.end():]
src = src.replace("import org.kde.kirigami as Kirigami", 'import org.kde.kirigami as Kirigami\nimport "code/cathodeschemes.js" as CathodeSchemes', 1)
open(p, "w").write(src)

# --- vertical banner -------------------------------------------------------------
p = os.path.join(UI, "MenuRepresentation.qml")
src = open(p).read()
anchor = re.search(r"\n(\s*)KSvg\.FrameSvgItem \{\n\s*id: sideBar\b", src)
if anchor and "id: mainRow" in src[:anchor.start()]:
    ind = anchor.group(1)
    banner = f"""
{ind}// Cathode: 98-style vertical banner down the left edge of the Start menu
{ind}Rectangle {{
{ind}    id: cathodeBanner
{ind}    Layout.fillHeight: true
{ind}    Layout.preferredWidth: 22
{ind}    Layout.minimumWidth: 22
{ind}    Layout.rightMargin: 2
{ind}    readonly property color cathodeSel: Kirigami.Theme.highlightColor
{ind}    gradient: Gradient {{
{ind}        GradientStop {{ position: CathodeSchemes.stop(cathodeBanner.cathodeSel, 0, true).position; color: CathodeSchemes.stop(cathodeBanner.cathodeSel, 0, true).color }}
{ind}        GradientStop {{ position: CathodeSchemes.stop(cathodeBanner.cathodeSel, 1, true).position; color: CathodeSchemes.stop(cathodeBanner.cathodeSel, 1, true).color }}
{ind}        GradientStop {{ position: CathodeSchemes.stop(cathodeBanner.cathodeSel, 2, true).position; color: CathodeSchemes.stop(cathodeBanner.cathodeSel, 2, true).color }}
{ind}        GradientStop {{ position: CathodeSchemes.stop(cathodeBanner.cathodeSel, 3, true).position; color: CathodeSchemes.stop(cathodeBanner.cathodeSel, 3, true).color }}
{ind}        GradientStop {{ position: CathodeSchemes.stop(cathodeBanner.cathodeSel, 4, true).position; color: CathodeSchemes.stop(cathodeBanner.cathodeSel, 4, true).color }}
{ind}        GradientStop {{ position: CathodeSchemes.stop(cathodeBanner.cathodeSel, 5, true).position; color: CathodeSchemes.stop(cathodeBanner.cathodeSel, 5, true).color }}
{ind}    }}
{ind}    Text {{
{ind}        text: "Cathode"
{ind}        color: "white"
{ind}        font.bold: true
{ind}        font.pixelSize: 17
{ind}        rotation: -90
{ind}        transformOrigin: Item.TopLeft
{ind}        x: Math.round((cathodeBanner.width - height) / 2)
{ind}        y: cathodeBanner.height - 6
{ind}    }}
{ind}}}
"""
    src = src[:anchor.start()] + banner + src[anchor.start():]
    if "code/cathodeschemes.js" not in src:
        src = re.sub(r"(\nimport org\.kde\.kirigami[^\n]*)", r'\1\nimport "code/cathodeschemes.js" as CathodeSchemes', src, count=1)
    if "CathodeSchemes" not in src.split("Rectangle {")[0] or "Kirigami" not in src.split("Rectangle {")[0]:
        sys.exit("MenuRepresentation.qml: could not add the scheme import")
    src = src.replace("Layout.minimumWidth: (sideBar.visible ?", "Layout.minimumWidth: cathodeBanner.Layout.preferredWidth + cathodeBanner.Layout.rightMargin + (sideBar.visible ?", 1)
    # The search field is positioned by hand from the menu edge + sidebar width;
    # shift it past the banner too, or it covers the bottom sidebar button.
    banner_w = "cathodeBanner.Layout.preferredWidth + cathodeBanner.Layout.rightMargin + "
    src = src.replace("anchors.leftMargin: sideBar.visible ? sideBar.width + spacing : 0",
                      "anchors.leftMargin: " + banner_w + "(sideBar.visible ? sideBar.width + spacing : 0)")
    src = src.replace("searchField.anchors.rightMargin: sideBar.visible ? sideBar.width + spacing : 0",
                      "searchField.anchors.rightMargin: " + banner_w + "(sideBar.visible ? sideBar.width + spacing : 0)")
    open(p, "w").write(src)
else:
    print("note: menu layout not recognised; skipping the banner")

# --- search: applications only, one merged list ---------------------------------
# Kicker queries System Settings, sessions, power, calculator... and shows each
# in its own column. Cathode searches apps (plus any runners the user opts into)
# and merges the results into a single list under the search box.
src = open(os.path.join(UI, "main.qml")).read()
src, n = re.subn(r'const results = \[\s*"krunner_services",[^\]]*\];',
                 'const results = ["krunner_services"];  // Cathode: apps only', src)
if n != 1:
    sys.exit("could not find Kicker's runner list in main.qml")
src, n = re.subn(r'(Kicker\.RunnerModel \{\s*\n\s*id: \w+)', r'\1\n        mergeResults: true  // Cathode: one list', src)
if n != 1:
    sys.exit("could not find Kicker's RunnerModel in main.qml")
open(os.path.join(UI, "main.qml"), "w").write(src)

# --- no group separators in the menu list (98's Start menu had none) ------------
p = os.path.join(UI, "main.qml")
src = open(p).read()
src = re.sub(r"\bshowSeparators: [^\n]+", "showSeparators: false  // Cathode", src)
src = re.sub(r"\bshowRootSeparator: [^\n]+", "showRootSeparator: false  // Cathode", src)
open(p, "w").write(src)

# --- defaults: applications-only search ------------------------------------------
p = os.path.join(CFG, "main.xml")
src = open(p).read()
src = re.sub(r'(<entry name="useExtraRunners" type="Bool">.*?<default>)true(</default>)', r"\1false\2", src, flags=re.S)
open(p, "w").write(src)

print("Cathode Start ->", OUT)
