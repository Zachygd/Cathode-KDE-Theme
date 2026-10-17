#!/usr/bin/env python3
"""Tests for Cathode Display Properties. KDE's tools are replaced by stand-ins that
record their calls, so nothing on this machine is changed.
Usage: test_app.py OUT_DIR   (screenshots go to OUT_DIR)"""
import configparser
import os
import shutil
import subprocess
import sys
import tempfile

OUT = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "share/cathode/app/cathode_display.py")
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["CATHODE_NO_WATCHER"] = "1"
results = []


def check(name, ok):
    results.append((name, bool(ok)))


# ---- a fake home with stand-in KDE tools ------------------------------------------
TMP = tempfile.mkdtemp()
HOME_CFG, HOME_DATA, SYS = (os.path.join(TMP, d) for d in ("config", "data", "usr/share"))
BIN, LOG = os.path.join(TMP, "bin"), os.path.join(TMP, "calls.log")
for d in (HOME_CFG, HOME_DATA, SYS, BIN):
    os.makedirs(d)
os.environ.update(XDG_CONFIG_HOME=HOME_CFG, XDG_DATA_HOME=HOME_DATA, XDG_DATA_DIRS=SYS,
                  XDG_RUNTIME_DIR=TMP, CATHODE_LOG=LOG, PATH=BIN + ":" + os.environ["PATH"])
# kwriteconfig6 stand-in really edits the file (so reading it back works) and logs
with open(os.path.join(BIN, "kwriteconfig6"), "w") as f:
    f.write(f"""#!{sys.executable}
import configparser, os, sys
a = sys.argv[1:]; open(os.environ["CATHODE_LOG"], "a").write("kwriteconfig6 " + " ".join(a) + "\\n")
file = a[a.index("--file") + 1]; group = a[a.index("--group") + 1]; key = a[a.index("--key") + 1]
path = file if os.path.isabs(file) else os.path.join(os.environ["XDG_CONFIG_HOME"], file)
c = configparser.ConfigParser(interpolation=None, strict=False); c.optionxform = str; c.read(path)
if not c.has_section(group): c.add_section(group)
if "--delete" in a: c.remove_option(group, key)
else: c[group][key] = a[-1]
c.write(open(path, "w"), space_around_delimiters=False)
""")
for t in ["plasma-apply-colorscheme", "plasma-apply-desktoptheme", "gdbus"]:
    with open(os.path.join(BIN, t), "w") as f:
        f.write('#!/bin/sh\necho "%s $*" >> "$CATHODE_LOG"\n' % t)
for t in os.listdir(BIN):
    os.chmod(os.path.join(BIN, t), 0o755)


def calls():
    return open(LOG).read().splitlines() if os.path.exists(LOG) else []


def reset_log():
    open(LOG, "w").close()


def kdeglobals():
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    c.read(os.path.join(HOME_CFG, "kdeglobals"))
    return c


# a system-wide install of the two global themes
for pid in ("org.cathode.desktop", "org.cathode.desktop.dark"):
    shutil.copytree(os.path.join(ROOT, "plasma/look-and-feel", pid), os.path.join(SYS, "plasma/look-and-feel", pid))
with open(os.path.join(HOME_CFG, "kdeglobals"), "w") as f:
    f.write("[General]\nColorScheme=Cathode98\n\n[KDE]\nLookAndFeelPackage=org.cathode.desktop\n")

sys.path.insert(0, os.path.dirname(APP))
import cathode_display as cd  # noqa: E402

# ---- defaults editing ------------------------------------------------------------
d0 = open(os.path.join(ROOT, "plasma/look-and-feel/org.cathode.desktop/contents/defaults")).read()
d1 = cd.set_ini_value(d0, "[kdeglobals][Icons]", "Theme", "Cathode-Brick")
check("defaults: icon theme changed, splash theme untouched",
      "[kdeglobals][Icons]\nTheme=Cathode-Brick" in d1 and "[ksplashrc][KSplash]\nTheme=org.cathode.desktop" in d1)

# ---- state -------------------------------------------------------------------------
check("first run: state comes from KDE", cd.current_state() ==
      {"light": "cathode", "dark": "cathode", "mode": "light", "background": "solid"})
with open(cd.STATE, "w") as f:                       # saved by the first version of the app
    f.write("[Appearance]\nScheme=plum\nMode=dark\nBackground=solid\n")
st = cd.current_state()
check("old saved choice is carried over", st["light"] == "plum" and st["dark"] == "plum")
os.remove(cd.STATE)

# ---- Apply, manual dark mode, system-wide install -----------------------------------
reset_log()
probs = cd.apply({"light": "wheat", "dark": "storm", "mode": "dark", "background": "solid"})
check("apply (dark): no problems", probs == [])
user_lnf = os.path.join(HOME_DATA, "plasma/look-and-feel")
dark_def = open(os.path.join(user_lnf, "org.cathode.desktop.dark/contents/defaults")).read()
light_def = open(os.path.join(user_lnf, "org.cathode.desktop/contents/defaults")).read()
check("Cathode Dark global theme now carries Storm Dark",
      "ColorScheme=Cathode98StormDark" in dark_def and "theme=__aurorae__svg__Cathode98StormDark" in dark_def
      and "Theme=Cathode-Storm" in dark_def)
check("Cathode global theme now carries Wheat", "ColorScheme=Cathode98Wheat" in light_def)
check("per-user copy links the big pieces back to the system theme",
      os.path.islink(os.path.join(user_lnf, "org.cathode.desktop/contents/splash"))
      and os.path.exists(os.path.join(user_lnf, "org.cathode.desktop/contents/splash/Splash.qml")))
lay = open(os.path.join(user_lnf, "org.cathode.desktop.dark/contents/layouts/org.kde.plasma.desktop-layout.js")).read()
rgb = ",".join(str(int(cd.desk_colour("storm", "dark")[i:i + 2], 16)) for i in (1, 3, 5))
check("Cathode Dark layout uses the Storm dark desktop colour", 'writeConfig("Color", "%s")' % rgb in lay)
check("system theme left alone", "ColorScheme=Cathode98Dark\n" in
      open(os.path.join(SYS, "plasma/look-and-feel/org.cathode.desktop.dark/contents/defaults")).read())
k = kdeglobals()["KDE"]
check("KDE light/dark global themes point at Cathode / Cathode Dark",
      k.get("DefaultLightLookAndFeel") == "org.cathode.desktop" and k.get("DefaultDarkLookAndFeel") == "org.cathode.desktop.dark")
check("automatic switching off, Cathode Dark current",
      k.get("AutomaticLookAndFeel") == "false" and k.get("LookAndFeelPackage") == "org.cathode.desktop.dark")
log = calls()
check("settings written with --notify (KDE's switcher listens for it)",
      any("DefaultDarkLookAndFeel --notify" in c for c in log))
check("Storm Dark colours and dark Plasma style applied",
      "plasma-apply-colorscheme Cathode98StormDark" in log and "plasma-apply-desktoptheme Cathode98Dark" in log)
wp = [c for c in log if "setWallpaper" in c]
check("desktop set live with setWallpaper (solid Storm dark colour)",
      wp and "'org.kde.color'" in wp[0] and cd.desk_colour("storm", "dark") in wp[0])
check("no more evaluateScript-written wallpaper", not any("writeConfig(\"Color\"" in c for c in log))

# the GVariant text gdbus will parse
py312 = shutil.which("python3.12")
if py312:
    arg = "{'Image': <%s>, 'FillMode': <2>}" % cd.gvariant_str("file:///home/z/My Wallpapers/it's.png")
    r = subprocess.run([py312, "-I", "-c", "import sys; from gi.repository import GLib; "
                        "v = GLib.Variant.parse(None, sys.argv[1], None, None); print(v.get_type_string(), v['Image'])", arg],
                       capture_output=True, text=True, cwd="/")
    check("wallpaper arguments are valid D-Bus (GVariant) text", r.stdout.strip() == "a{sv} file:///home/z/My Wallpapers/it's.png")

# ---- Apply, automatic ---------------------------------------------------------------
reset_log()
probs = cd.apply({"light": "wheat", "dark": "storm", "mode": "auto", "background": "solid"})
k = kdeglobals()["KDE"]
check("automatic: KDE's day/night switching turned on", k.get("AutomaticLookAndFeel") == "true")
check("automatic: something applied straight away (switcher not running here)",
      any(c.startswith("plasma-apply-colorscheme Cathode98") for c in calls()))
check("automatic is what the app reads back", cd.current_state()["mode"] == "auto")

# ---- the Brightness and Color switch / day-night switching: desktop follows --------
# What KDE really does (KLookAndFeelManager): LookAndFeelPackage goes in kdeglobals,
# the colour scheme goes in ~/.config/kdedefaults/kdeglobals and is REMOVED from kdeglobals.
import time  # noqa: E402
KDEDEF = os.path.join(HOME_CFG, "kdedefaults", "kdeglobals")
os.makedirs(os.path.dirname(KDEDEF), exist_ok=True)


def kde_switches_to(mode, scheme_id, auto="false"):
    kg = kdeglobals()
    kg["KDE"]["AutomaticLookAndFeel"] = auto
    kg["KDE"]["LookAndFeelPackage"] = cd.LNF[mode]
    kg.remove_option("General", "ColorScheme")
    kg.write(open(os.path.join(HOME_CFG, "kdeglobals"), "w"), space_around_delimiters=False)
    with open(KDEDEF, "w") as f:
        f.write(f"[General]\nColorScheme={scheme_id}\n\n[Icons]\nTheme=Cathode\n")


kde_switches_to("light", "Cathode98Wheat")
reset_log()
cd.check_desktop()
check("helper: desktop follows the light mode switch (scheme stored in kdedefaults)",
      any("setWallpaper" in c and cd.desk_colour("wheat", "light") in c for c in calls()))
check("app reads the switch as light mode", cd.current_state()["mode"] == "light")
reset_log()
cd.check_desktop()
check("helper: leaves the desktop alone when the scheme hasn't changed", not calls())

# the real helper, running in the background, through dark -> light -> dark
reset_log()
helper = subprocess.Popen([sys.executable, APP, "--watch"])
try:
    time.sleep(1)
    kde_switches_to("dark", "Cathode98StormDark", auto="true")    # e.g. sunset
    time.sleep(3)
    got_dark = any("setWallpaper" in c and cd.desk_colour("storm", "dark") in c for c in calls())
    kde_switches_to("light", "Cathode98Wheat")                    # Brightness and Color switch
    time.sleep(3)
    got_light = any("setWallpaper" in c and cd.desk_colour("wheat", "light") in c for c in calls())
    second = subprocess.run([sys.executable, APP, "--watch"], timeout=10).returncode == 0
finally:
    helper.terminate()
    helper.wait()
check("running helper: sunset to Storm Dark sets its desktop", got_dark)
check("running helper: light mode switch back to Wheat sets its desktop", got_light)
check("running helper: a second copy exits straight away", second)

# ---- per-user install: edited in place -----------------------------------------------
shutil.rmtree(user_lnf)
shutil.copytree(os.path.join(SYS, "plasma/look-and-feel"), user_lnf)
cd.write_global_theme("light", "teal")
check("per-user install is edited in place, not replaced",
      "ColorScheme=Cathode98Teal" in open(os.path.join(user_lnf, "org.cathode.desktop/contents/defaults")).read()
      and not os.path.islink(os.path.join(user_lnf, "org.cathode.desktop/contents/splash")))

# ---- command line --------------------------------------------------------------------
r = subprocess.run([sys.executable, APP, "--light-scheme", "rose", "--dark-scheme", "slate", "--auto"],
                   capture_output=True, text=True)
c = configparser.ConfigParser()
c.read(cd.STATE)
check("--light-scheme/--dark-scheme/--auto saved", r.returncode == 0 and dict(c["Appearance"]).get("light") == "rose"
      and dict(c["Appearance"]).get("dark") == "slate" and dict(c["Appearance"]).get("mode") == "auto")
r = subprocess.run([sys.executable, APP, "--apply", "nope"], capture_output=True, text=True)
check("unknown scheme rejected", r.returncode == 2)

# ---- the window ------------------------------------------------------------------------
from PySide6.QtGui import QPalette, QColor, QFont  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402
app = QApplication([])
app.setFont(QFont("Tahoma", 9))
p = QPalette()
for role, col in [(QPalette.Window, "#c0c0c0"), (QPalette.Button, "#c0c0c0"), (QPalette.Base, "#f4f3ef"),
                  (QPalette.Highlight, "#064ed8"), (QPalette.Light, "#ffffff"), (QPalette.Midlight, "#dfdfdf"),
                  (QPalette.Mid, "#808080"), (QPalette.Dark, "#808080"), (QPalette.Shadow, "#000000")]:
    p.setColor(role, QColor(col))
app.setPalette(p)
cd.DRY = True                                   # the window's Apply prints instead of running
os.environ["CATHODE_SCREENSHOT"] = os.path.join(OUT, "app-start.png")
cd.gui({"light": "cathode", "dark": "cathode", "mode": "light", "background": "solid"})
d = app.cathode_dialog
check("window: Apply off until something changes", not d.apply_btn.isEnabled())
check("window: both scheme lists usable in Light mode (for the Brightness menu switch)",
      d.combo["dark"].isEnabled() and d.combo["light"].isEnabled())
d.use["auto"].setChecked(True)
check("window: Automatic selectable", d.state["mode"] == "auto")
first = d.preview.pixmap().toImage()
d.combo["dark"].setCurrentIndex(d.combo["dark"].findData("spruce"))
check("window: picking a dark scheme previews it", d.showing == "dark" and d.preview.pixmap().toImage() != first)
d.combo["light"].setCurrentIndex(d.combo["light"].findData("pumpkin"))
check("window: picking a light scheme previews that", d.showing == "light")
check("window: state", d.state == {"light": "pumpkin", "dark": "spruce", "mode": "auto", "background": "solid"})
d.repaint()
d.grab().save(os.path.join(OUT, "app-appearance-auto.png"))
d.use["dark"].setChecked(True)
check("window: Dark shows the dark scheme", d.showing == "dark" and d.monitor.colour.name() == cd.desk_colour("spruce", "dark"))
# wallpapers
wdir = os.path.join(cd.BASE, "wallpapers")
wp = os.path.join(wdir, "spruce-dark.png")
shutil.copy(os.path.join(cd.BASE, "previews", "spruce-dark.png"), wp)
try:
    d.refresh()
    check("window: wallpaper option enables when the scheme has one", d.wall.isEnabled())
    d.wall.setChecked(True)
    check("window: monitor shows the wallpaper", d.monitor.image is not None and not d.monitor.image.isNull())
    d.tabs.setCurrentIndex(0)
    d.repaint()
    d.grab().save(os.path.join(OUT, "app-background-wallpaper.png"))
finally:
    os.remove(wp)
d.refresh()
check("window: back to solid when the wallpaper goes", d.solid.isChecked() and not d.wall.isEnabled())
d.do_apply()
check("window: Apply turns itself off", not d.apply_btn.isEnabled())
d.tabs.setCurrentIndex(1)
d.use["light"].setChecked(True)
d.repaint()
d.grab().save(os.path.join(OUT, "app-appearance-light.png"))

shutil.rmtree(TMP)
ok = True
for name, passed in results:
    print(("PASS " if passed else "FAIL ") + name)
    ok &= passed
sys.exit(0 if ok else 1)
