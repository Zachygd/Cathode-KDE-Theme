#!/usr/bin/env python3
"""Cathode Display Properties - pick a Cathode colour scheme for light mode and
one for dark mode, use either or let KDE switch with the time of day, and pick a
solid desktop colour or the scheme's wallpaper.

Everything goes through KDE's own settings, so KDE does the switching:
  * the "Cathode" and "Cathode Dark" global themes are rewritten (a per-user copy)
    to carry your light and your dark scheme;
  * KDE's light/dark global themes point at them, so KDE's automatic day/night
    switching and the dark mode switch in the Brightness and Color menu flip
    between your two schemes;
  * a tiny helper (--watch, started at login) sets the matching desktop colour
    whenever the scheme changes, since global themes can't carry one.

    cathode-display                          open the window
    cathode-display --list                   list the schemes
    cathode-display --apply brick --dark     use Brick in dark mode
    cathode-display --light-scheme wheat --dark-scheme storm --auto
    cathode-display --reapply                apply the saved choice again
    CATHODE_DRY_RUN=1 cathode-display ...    print what would run instead

SPDX-License-Identifier: GPL-2.0-or-later
"""
import argparse
import configparser
import json
import os
import re
import shutil
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../share/cathode
SCHEMES = json.load(open(os.path.join(BASE, "schemes.json")))
BY_SLUG = {s["slug"]: s for s in SCHEMES}
BY_ID = {s[m]: (s["slug"], m) for s in SCHEMES for m in ("light", "dark")}
CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
DATA_HOME = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
DATA_DIRS = [d for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]
STATE = os.path.join(CONFIG_HOME, "cathoderc")
KDEGLOBALS = os.path.join(CONFIG_HOME, "kdeglobals")
# When KDE applies a global theme (day/night switching, the Brightness and Color dark
# mode switch, System Settings) it writes the values here and removes them from
# kdeglobals, so the effective setting is kdeglobals layered over this file.
KDEDEFAULTS = os.path.join(CONFIG_HOME, "kdedefaults", "kdeglobals")
DRY = os.environ.get("CATHODE_DRY_RUN") == "1"
WALL_EXT = ("png", "jpg", "jpeg", "webp")
LNF = {"light": "org.cathode.desktop", "dark": "org.cathode.desktop.dark"}
OVERLAY_MARK = ".cathode-display"   # marks a per-user global theme copy made by this app
MODES = ("light", "dark", "auto")


# ---- state ---------------------------------------------------------------------
def read_ini(path):
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    try:
        c.read(path)
    except configparser.Error:
        pass
    return c


def read_kdeglobals():
    """kdeglobals as KDE sees it: ~/.config/kdeglobals over ~/.config/kdedefaults/kdeglobals."""
    c = configparser.ConfigParser(interpolation=None, strict=False)
    c.optionxform = str
    for path in (KDEDEFAULTS, KDEGLOBALS):
        try:
            c.read(path)
        except configparser.Error:
            pass
    return c


def kde_state():
    """What KDE is actually set to: (mode or None, colour scheme id)."""
    kg = read_kdeglobals()
    auto = kg.get("KDE", "AutomaticLookAndFeel", fallback="false").lower() == "true"
    ours = (kg.get("KDE", "DefaultLightLookAndFeel", fallback="") == LNF["light"]
            and kg.get("KDE", "DefaultDarkLookAndFeel", fallback="") == LNF["dark"])
    lnf = kg.get("KDE", "LookAndFeelPackage", fallback="")
    mode = "auto" if auto and ours else {LNF["light"]: "light", LNF["dark"]: "dark"}.get(lnf)
    return mode, kg.get("General", "ColorScheme", fallback="")


def current_state():
    """The saved choice (~/.config/cathoderc), corrected by what KDE is set to now
    (for example after the Brightness and Color dark mode switch)."""
    st = {"light": "cathode", "dark": "cathode", "mode": "light", "background": "solid"}
    kmode, scheme_id = kde_state()
    found = BY_ID.get(scheme_id)
    c = read_ini(STATE)
    a = c["Appearance"] if c.has_section("Appearance") else {}
    if a.get("Light") in BY_SLUG and a.get("Dark") in BY_SLUG:
        st["light"], st["dark"] = a["Light"], a["Dark"]
    elif a.get("Scheme") in BY_SLUG:                       # saved by the first version
        st["light"] = st["dark"] = a["Scheme"]
    elif found:
        st["light"] = st["dark"] = found[0]
    if a.get("Mode") in MODES:
        st["mode"] = a["Mode"]
    elif found:
        st["mode"] = found[1]
    if kmode:
        st["mode"] = kmode
    if a.get("Background") in ("solid", "wallpaper"):
        st["background"] = a["Background"]
    return st


def save_state(st, applied_scheme=None):
    c = read_ini(STATE)
    if not c.has_section("Appearance"):
        c.add_section("Appearance")
    g = c["Appearance"]
    for k in ("Scheme",):
        g.pop(k, None)
    g["Light"], g["Dark"], g["Mode"], g["Background"] = st["light"], st["dark"], st["mode"], st["background"]
    if applied_scheme:
        g["DesktopFor"] = applied_scheme          # scheme the desktop colour was last set for
    if DRY:
        print("write", STATE, dict(g))
        return
    os.makedirs(CONFIG_HOME, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        c.write(f, space_around_delimiters=False)
    os.replace(tmp, STATE)


def wallpaper_for(slug, mode):
    """share/cathode/wallpapers/<slug>-dark.png, <slug>.png, ... or None."""
    names = ([slug + "-dark"] if mode == "dark" else []) + [slug]
    for n in names:
        for ext in WALL_EXT:
            p = os.path.join(BASE, "wallpapers", f"{n}.{ext}")
            if os.path.isfile(p):
                return p
    return None


def preview_for(slug, mode):
    p = os.path.join(BASE, "previews", slug + ("-dark" if mode == "dark" else "") + ".png")
    return p if os.path.isfile(p) else None


def desk_colour(slug, mode):
    s = BY_SLUG[slug]
    return s["deskDark"] if mode == "dark" else s["deskLight"]


def theme_id(slug, mode):
    return BY_SLUG[slug]["dark" if mode == "dark" else "light"]


# ---- talking to KDE --------------------------------------------------------------
def run(cmd, capture=False):
    if DRY:
        print("run", " ".join(cmd if len(" ".join(cmd)) < 200 else cmd[:6] + ["..."]))
        return (True, "") if capture else True
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return (str(e), "") if capture else str(e)
    ok = True if r.returncode == 0 else (r.stdout.strip() or f"{cmd[0]} exited with {r.returncode}")
    return (ok, r.stdout) if capture else ok


def tool(*names):
    if DRY:
        return os.path.basename(names[0])
    for n in names:
        if os.path.isabs(n):
            if os.access(n, os.X_OK):
                return n
        elif shutil.which(n):
            return shutil.which(n)
    return None


def kwrite(file, group, key, value=None, notify=True):
    """kwriteconfig6, telling running KDE programs about the change (KDE's day/night
    switcher only reacts to notified changes). value=None deletes the key."""
    kw = tool("kwriteconfig6", "kwriteconfig5")
    if not kw:
        return "kwriteconfig6 not found"
    cmd = [kw, "--file", file, "--group", group, "--key", key]
    if notify:
        cmd.append("--notify")
    cmd += ["--delete"] if value is None else [value]
    return run(cmd)


def gvariant_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def dbus(service, path, method, *args, capture=False):
    """Call a session-bus method with gdbus (part of glib2, always on Fedora).
    args are GVariant text, e.g. gvariant_str("x") or "{'Color': <'#ffffff'>}"."""
    g = tool("gdbus")
    if not g:
        return ("gdbus not found", "") if capture else "gdbus not found"
    return run([g, "call", "--session", "--dest", service, "--object-path", path, "--method", method, *args],
               capture=capture)


def screen_count():
    ok, out = dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript",
                   gvariant_str("print(screenCount)"), capture=True)
    m = re.search(r"(\d+)", out or "") if ok is True else None
    return max(1, int(m.group(1))) if m else 4      # unknown: try a few; extra screens are ignored


def set_desktop(slug, mode, background):
    """Desktop colour or wallpaper on every screen, live (Plasma's setWallpaper)."""
    wall = wallpaper_for(slug, mode) if background == "wallpaper" else None
    if wall:
        plugin = "org.kde.image"
        params = "{'Image': <%s>, 'FillMode': <2>}" % gvariant_str("file://" + wall)
    else:
        plugin = "org.kde.color"
        params = "{'Color': <%s>}" % gvariant_str(desk_colour(slug, mode))
    result = True
    for screen in range(1 if DRY else screen_count()):
        r = dbus("org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.setWallpaper",
                 gvariant_str(plugin), params, str(screen))
        if screen == 0 and r is not True:
            result = r
    return result


def apply_look(slug, mode):
    """Colours, Plasma style, window frames and icons for one scheme, now."""
    tid = theme_id(slug, mode)
    problems = []

    def step(what, result):
        if result is not True:
            problems.append(f"{what}: {result}")

    t = tool("plasma-apply-colorscheme")
    if t:
        # plasma-apply-colorscheme skips a scheme whose name is already recorded, even if
        # its colours were never applied; forget the name so it always applies
        kwrite("kdeglobals", "General", "ColorScheme", None, notify=False)
        r = run([t, tid])
        step("colour scheme", True if r is True or "already set" in str(r) else r)
    else:
        problems.append("colour scheme: plasma-apply-colorscheme not found")
    t = tool("plasma-apply-desktoptheme")
    step("Plasma style", run([t, "Cathode98Dark" if mode == "dark" else "Cathode98"]) if t
         else "plasma-apply-desktoptheme not found")
    step("window frames", kwrite("kwinrc", "org.kde.kdecoration2", "theme", "__aurorae__svg__" + tid))
    step("window frames", dbus("org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"))
    t = tool("/usr/libexec/plasma-changeicons", "/usr/lib/plasma-changeicons",
             "/usr/lib64/libexec/plasma-changeicons", "/usr/lib/x86_64-linux-gnu/libexec/plasma-changeicons")
    step("icons", run([t, BY_SLUG[slug]["icons"]]) if t else kwrite("kdeglobals", "Icons", "Theme", BY_SLUG[slug]["icons"]))
    return problems


# ---- the two global themes carry your light and dark schemes ---------------------
def set_ini_value(text, section, key, value):
    """Set key=value inside [section] of an INI-style text (section like "[kdeglobals][General]")."""
    out, cur, done = [], None, False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("["):
            if cur == section and not done:
                out.append(f"{key}={value}")
                done = True
            cur = line.strip()
        elif cur == section and line.split("=", 1)[0].strip() == key:
            if not done:
                out.append(f"{key}={value}")
                done = True
            continue
        out.append(line)
    if not done:
        if cur != section:
            out += ["", section]
        out.append(f"{key}={value}")
    return "\n".join(out) + "\n"


def find_package(pid, skip_overlay=True):
    for d in [DATA_HOME] + DATA_DIRS:
        p = os.path.join(d, "plasma", "look-and-feel", pid)
        if os.path.isfile(os.path.join(p, "metadata.json")):
            if skip_overlay and os.path.exists(os.path.join(p, OVERLAY_MARK)):
                continue
            return p
    return None


def write_global_theme(mode, slug):
    """Point the Cathode (or Cathode Dark) global theme at a scheme.

    A per-user install is edited in place. For a system install a small per-user
    copy is made (metadata, defaults and layouts; everything else links back), which
    Plasma prefers over the system one."""
    pid = LNF[mode]
    tid = theme_id(slug, mode)
    if DRY:
        print("global theme", pid, "->", tid)
        return True
    src = find_package(pid)
    if not src:
        return f"global theme {pid} is not installed"
    target = os.path.join(DATA_HOME, "plasma", "look-and-feel", pid)
    if os.path.realpath(src) != os.path.realpath(target):
        if os.path.lexists(target):
            shutil.rmtree(target) if not os.path.islink(target) else os.remove(target)
        os.makedirs(os.path.join(target, "contents"))
        shutil.copy(os.path.join(src, "metadata.json"), target)
        for entry in os.listdir(os.path.join(src, "contents")):
            s, t = os.path.join(src, "contents", entry), os.path.join(target, "contents", entry)
            if entry == "defaults":
                shutil.copy(s, t)
            elif entry == "layouts":
                shutil.copytree(s, t)
            else:
                os.symlink(s, t)
        open(os.path.join(target, OVERLAY_MARK), "w").write("made by Cathode Display Properties\n")
    p = os.path.join(target, "contents", "defaults")
    text = open(p).read()
    text = set_ini_value(text, "[kdeglobals][General]", "ColorScheme", tid)
    text = set_ini_value(text, "[kdeglobals][Icons]", "Theme", BY_SLUG[slug]["icons"])
    text = set_ini_value(text, "[kwinrc][org.kde.kdecoration2]", "theme", "__aurorae__svg__" + tid)
    open(p, "w").write(text)
    rgb = ",".join(str(int(desk_colour(slug, mode)[i:i + 2], 16)) for i in (1, 3, 5))
    ldir = os.path.join(target, "contents", "layouts")
    for name in os.listdir(ldir) if os.path.isdir(ldir) else []:
        lp = os.path.join(ldir, name)
        js = open(lp).read()
        js2 = re.sub(r'(writeConfig\("Color", ")[0-9, ]*(")', r"\g<1>" + rgb + r"\g<2>", js)
        if js2 != js:
            open(lp, "w").write(js2)
    return True


def read_lnf():
    return read_kdeglobals().get("KDE", "LookAndFeelPackage", fallback="")


def apply(st):
    """Switch KDE to the chosen setup. Returns a list of problems (empty = all good)."""
    problems = []

    def step(what, result):
        if result is not True:
            problems.append(f"{what}: {result}")

    # a custom accent colour would tint the scheme; Cathode schemes bring their own
    kwrite("kdeglobals", "General", "AccentColor", None)
    kwrite("kdeglobals", "General", "accentColorFromWallpaper", "false")

    for mode in ("light", "dark"):
        step(f"{mode} global theme", write_global_theme(mode, st[mode]))
    step("light/dark themes", kwrite("kdeglobals", "KDE", "DefaultLightLookAndFeel", LNF["light"]))
    step("light/dark themes", kwrite("kdeglobals", "KDE", "DefaultDarkLookAndFeel", LNF["dark"]))

    if st["mode"] == "auto":
        before = read_lnf()
        step("automatic switching", kwrite("kdeglobals", "KDE", "AutomaticLookAndFeel", "true"))
        # KDE's day/night switcher now applies whichever theme fits the time of day
        now = before
        for _ in range(0 if DRY else 30):
            time.sleep(0.1)
            now = read_lnf()
            if now != before:
                break
        if now == LNF["dark"]:
            mode = "dark"
        elif now == LNF["light"]:
            mode = "light"
        else:                                           # switcher not running: guess by the clock
            mode = "light" if 7 <= time.localtime().tm_hour < 19 else "dark"
        if now == before or now not in LNF.values():
            problems += apply_look(st[mode], mode)      # same theme as before: apply the new scheme ourselves
            step("global theme", kwrite("kdeglobals", "KDE", "LookAndFeelPackage", LNF[mode]))
    else:
        mode = st["mode"]
        step("automatic switching", kwrite("kdeglobals", "KDE", "AutomaticLookAndFeel", "false"))
        step("global theme", kwrite("kdeglobals", "KDE", "LookAndFeelPackage", LNF[mode]))
        problems += apply_look(st[mode], mode)

    step("desktop background", set_desktop(st[mode], mode, st["background"]))
    save_state(st, theme_id(st[mode], mode))
    start_watcher()
    return problems


# ---- the login helper: desktop colour follows scheme changes made by KDE ------------
def watch():
    """Run in the background: when KDE switches the colour scheme (day/night, the
    Brightness and Color dark mode switch, or System Settings), set the matching
    desktop colour or wallpaper. Checks kdeglobals every couple of seconds."""
    import fcntl
    lockdir = os.environ.get("XDG_RUNTIME_DIR") or CONFIG_HOME
    lock = open(os.path.join(lockdir, "cathode-display-watch.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0                                        # already running
    me = os.path.abspath(__file__)
    my_mtime = os.stat(me).st_mtime_ns
    last_mtime = None
    while True:
        mtime = []
        for path in (KDEGLOBALS, KDEDEFAULTS):
            try:
                mtime.append(os.stat(path).st_mtime_ns)
            except OSError:
                mtime.append(None)
        if mtime != last_mtime:
            last_mtime = mtime
            check_desktop()
        if os.environ.get("CATHODE_WATCH_ONCE"):
            return 0
        time.sleep(2)
        try:                                            # updated by a reinstall: restart as the new version
            if os.stat(me).st_mtime_ns != my_mtime:
                lock.close()
                os.execv(sys.executable, [sys.executable, me, "--watch"])
        except OSError:
            pass


def check_desktop():
    """Set the desktop for the current scheme if it changed since we last did."""
    _, scheme_id = kde_state()
    found = BY_ID.get(scheme_id)
    if not found:
        return
    c = read_ini(STATE)
    a = c["Appearance"] if c.has_section("Appearance") else {}
    if a.get("DesktopFor") == scheme_id:
        return
    slug, mode = found
    if set_desktop(slug, mode, a.get("Background", "solid")) is True:
        st = current_state()
        save_state(st, scheme_id)


def start_watcher():
    if DRY or os.environ.get("CATHODE_NO_WATCHER"):
        return
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--watch"], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


# ---- the window --------------------------------------------------------------------
def gui(initial):
    try:
        from PySide6.QtCore import Qt, QRectF, QSize
        from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap, QPen
        from PySide6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QDialog, QDialogButtonBox,
                                       QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QRadioButton,
                                       QStyleFactory, QTabWidget, QVBoxLayout, QWidget)
    except ImportError:
        from PyQt6.QtCore import Qt, QRectF, QSize
        from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QPen
        from PyQt6.QtWidgets import (QApplication, QButtonGroup, QComboBox, QDialog, QDialogButtonBox,
                                     QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QRadioButton,
                                     QStyleFactory, QTabWidget, QVBoxLayout, QWidget)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("cathode-display")
    app.setApplicationDisplayName("Display Properties")
    app.setDesktopFileName("org.cathode.display")
    if "Windows" in QStyleFactory.keys():
        app.setStyle("Windows")

    class Monitor(QWidget):
        """The little 98 monitor on the Background tab, showing the desktop."""
        def __init__(self):
            super().__init__()
            self.setFixedSize(200, 170)
            self.colour, self.image = QColor("#008080"), None

        def show_desktop(self, colour, image_path):
            self.colour = QColor(colour)
            self.image = QPixmap(image_path) if image_path else None
            self.update()

        def paintEvent(self, _):
            p = QPainter(self)
            body = QRectF(10, 4, 180, 136)
            p.fillRect(body, QColor("#c0c0c0"))
            for (x1, y1, x2, y2), c in [((10, 4, 189, 4), "#ffffff"), ((10, 4, 10, 139), "#ffffff"),
                                        ((10, 139, 189, 139), "#000000"), ((189, 4, 189, 139), "#000000"),
                                        ((11, 138, 188, 138), "#808080"), ((188, 5, 188, 138), "#808080")]:
                p.setPen(QPen(QColor(c)))
                p.drawLine(x1, y1, x2, y2)
            screen = QRectF(24, 16, 152, 108)
            p.fillRect(screen.adjusted(-2, -2, 2, 2), QColor("#808080"))
            p.fillRect(screen, self.colour)
            if self.image and not self.image.isNull():
                p.drawPixmap(screen.toRect(), self.image)
            p.fillRect(QRectF(160, 130, 6, 3), QColor("#00c000"))           # power light
            for x, y, w, h in [(80, 140, 40, 13), (56, 153, 88, 10)]:          # stand and base
                p.fillRect(QRectF(x, y, w, h), QColor("#c0c0c0"))
                p.setPen(QPen(QColor("#ffffff")))
                p.drawLine(x, y, x + w - 1, y)
                p.drawLine(x, y, x, y + h - 1)
                p.setPen(QPen(QColor("#000000")))
                p.drawLine(x, y + h - 1, x + w - 1, y + h - 1)
                p.drawLine(x + w - 1, y, x + w - 1, y + h - 1)
                p.setPen(QPen(QColor("#808080")))
                p.drawLine(x + 1, y + h - 2, x + w - 2, y + h - 2)
                p.drawLine(x + w - 2, y + 1, x + w - 2, y + h - 2)
            p.end()

    class Dialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Display Properties")
            self.setWindowIcon(QIcon.fromTheme("preferences-desktop-display", QIcon.fromTheme("start-here")))
            self.applied = dict(initial)
            self.state = dict(initial)
            self.showing = "dark" if initial["mode"] == "dark" else "light"   # which one the preview shows
            lay = QVBoxLayout(self)
            lay.setContentsMargins(8, 8, 8, 8)
            self.tabs = QTabWidget()
            lay.addWidget(self.tabs)

            # Background tab
            bg = QWidget()
            self.tabs.addTab(bg, "Background")
            bl = QVBoxLayout(bg)
            self.monitor = Monitor()
            bl.addWidget(self.monitor, 0, Qt.AlignmentFlag.AlignHCenter)
            box = QGroupBox("Desktop")
            gl = QVBoxLayout(box)
            self.solid = QRadioButton("&Solid colour (matches the scheme)")
            self.wall = QRadioButton("&Wallpaper")
            self.wall_note = QLabel()
            self.wall_note.setIndent(20)
            self.wall_note.setWordWrap(True)
            self.wall_note.setMinimumHeight(self.wall_note.fontMetrics().lineSpacing() * 2 + 4)
            gl.addWidget(self.solid)
            gl.addWidget(self.wall)
            gl.addWidget(self.wall_note)
            self.bg_group = QButtonGroup(self)
            self.bg_group.addButton(self.solid)
            self.bg_group.addButton(self.wall)
            bl.addWidget(box)
            bl.addStretch(1)

            # Appearance tab
            ap = QWidget()
            self.tabs.addTab(ap, "Appearance")
            al = QVBoxLayout(ap)
            self.preview = QLabel()
            self.preview.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
            self.preview.setLineWidth(2)
            self.preview.setFixedSize(QSize(404, 304))
            self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview.setObjectName("preview")
            al.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignHCenter)

            grid = QGridLayout()
            grid.setHorizontalSpacing(8)
            self.combo = {}
            for col, (mode, text) in enumerate([("light", "&Light scheme:"), ("dark", "Dar&k scheme:")]):
                lbl = QLabel(text)
                cb = QComboBox()
                cb.setObjectName(mode + "Scheme")
                for sc in SCHEMES:
                    cb.addItem(sc["name"], sc["slug"])
                lbl.setBuddy(cb)
                grid.addWidget(lbl, 0, col * 2)
                grid.addWidget(cb, 0, col * 2 + 1)
                grid.setColumnStretch(col * 2 + 1, 1)
                self.combo[mode] = cb
            al.addLayout(grid)

            use = QGroupBox("Use")
            ul = QHBoxLayout(use)
            self.use = {"light": QRadioButton("Li&ght"), "dark": QRadioButton("&Dark"),
                        "auto": QRadioButton("&Automatic (day and night)")}
            self.use_group = QButtonGroup(self)
            for m in MODES:
                self.use[m].setObjectName("use_" + m)
                self.use_group.addButton(self.use[m])
                ul.addWidget(self.use[m])
            ul.addStretch(1)
            al.addWidget(use)
            self.note = QLabel()
            self.note.setWordWrap(True)
            self.note.setObjectName("note")
            self.note.setMinimumHeight(self.note.fontMetrics().lineSpacing() * 3 + 4)
            self.note.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            al.addWidget(self.note)
            al.addStretch(1)
            self.tabs.setCurrentIndex(1)

            self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                                            | QDialogButtonBox.StandardButton.Apply)
            self.buttons.accepted.connect(self.ok)
            self.buttons.rejected.connect(self.reject)
            self.apply_btn = self.buttons.button(QDialogButtonBox.StandardButton.Apply)
            self.apply_btn.clicked.connect(self.do_apply)
            lay.addWidget(self.buttons)

            self.load(self.state)
            for mode, cb in self.combo.items():
                cb.currentIndexChanged.connect(lambda _i, m=mode: self.changed(show=m))
                cb.activated.connect(lambda _i, m=mode: self.changed(show=m))
            self.use_group.buttonToggled.connect(lambda *_: self.changed())
            self.bg_group.buttonToggled.connect(lambda *_: self.changed())
            self.setFixedSize(self.sizeHint())

        def load(self, st):
            for mode in ("light", "dark"):
                self.combo[mode].setCurrentIndex(max(0, self.combo[mode].findData(st[mode])))
            self.use[st["mode"]].setChecked(True)
            (self.wall if st["background"] == "wallpaper" else self.solid).setChecked(True)
            self.refresh()

        def changed(self, show=None):
            mode = next((m for m in MODES if self.use[m].isChecked()), "light")
            self.state = {"light": self.combo["light"].currentData(), "dark": self.combo["dark"].currentData(),
                          "mode": mode, "background": "wallpaper" if self.wall.isChecked() else "solid"}
            if show:
                self.showing = show          # show whichever scheme you just picked
            elif mode != "auto":
                self.showing = mode          # switching Light/Dark shows that one
            self.refresh()

        def refresh(self):
            st = self.state
            used = ["light", "dark"] if st["mode"] == "auto" else [st["mode"]]
            walls = {m: wallpaper_for(st[m], m) for m in used}
            self.wall.setEnabled(any(walls.values()))
            if not any(walls.values()) and self.wall.isChecked():
                self.solid.setChecked(True)   # re-enters changed()
                return
            show = self.showing
            slug = st[show]
            name = BY_SLUG[slug]["name"] + (" Dark" if show == "dark" else "")
            if any(walls.values()):
                self.wall_note.setText("\n".join(
                    f"{BY_SLUG[st[m]]['name']}{' Dark' if m == 'dark' else ''}: "
                    + (os.path.basename(walls[m]) if walls[m] else "no wallpaper yet, uses its colour") for m in used))
            else:
                self.wall_note.setText(f"No wallpaper for {' or '.join(BY_SLUG[st[m]]['name'] for m in used)} yet.")
            self.monitor.show_desktop(desk_colour(slug, show),
                                      wallpaper_for(slug, show) if st["background"] == "wallpaper" else None)
            pv = preview_for(slug, show)
            if pv:
                self.preview.setPixmap(QPixmap(pv))
            else:
                self.preview.setPixmap(QPixmap())
                self.preview.setText(name)
            self.preview.setToolTip(name)
            if st["mode"] == "auto":
                self.note.setText(f"Showing {name}. KDE switches between your two schemes at sunrise and "
                                  "sunset, using the same day and night times as Night Light.")
            else:
                self.note.setText(f"Showing {name}. The dark mode switch in the Brightness and Color "
                                  "menu flips between your light and dark schemes.")
            self.apply_btn.setEnabled(st != self.applied)

        def do_apply(self):
            app.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                problems = apply(self.state)
            finally:
                app.restoreOverrideCursor()
            self.applied = dict(self.state)
            self.apply_btn.setEnabled(False)
            if problems:
                QMessageBox.warning(self, "Display Properties",
                                    "Some settings could not be changed:\n\n" + "\n".join(problems))
            return not problems

        def ok(self):
            if self.state != self.applied:
                self.do_apply()
            self.accept()

    d = Dialog()
    app.cathode_dialog = d          # keep it alive
    d.show()
    if os.environ.get("CATHODE_SCREENSHOT"):          # used by the test suite
        app.processEvents()
        d.grab().save(os.environ["CATHODE_SCREENSHOT"])
        return 0
    return app.exec()


def main():
    ap = argparse.ArgumentParser(description="Cathode Display Properties")
    ap.add_argument("--list", action="store_true", help="list the colour schemes")
    ap.add_argument("--apply", metavar="SCHEME", help="use SCHEME (with --dark/--light: for that mode; "
                                                      "otherwise for both) and apply without opening the window")
    ap.add_argument("--light-scheme", metavar="SCHEME", help="scheme for light mode")
    ap.add_argument("--dark-scheme", metavar="SCHEME", help="scheme for dark mode")
    ap.add_argument("--light", action="store_true", help="use light mode")
    ap.add_argument("--dark", action="store_true", help="use dark mode")
    ap.add_argument("--auto", action="store_true", help="switch light/dark with the time of day")
    ap.add_argument("--wallpaper", action="store_true", help="use the schemes' wallpapers where they have one")
    ap.add_argument("--solid", action="store_true", help="use solid desktop colours")
    ap.add_argument("--reapply", action="store_true", help="apply the saved choice again")
    ap.add_argument("--watch", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.watch:
        return watch()
    if a.list:
        for sc in SCHEMES:
            walls = [m for m in ("light", "dark") if wallpaper_for(sc["slug"], m)]
            print(f'{sc["slug"]:10} {sc["name"]:10} {sc["light"]} / {sc["dark"]}' + ("  (wallpaper)" if walls else ""))
        return 0
    for name in ("apply", "light_scheme", "dark_scheme"):
        v = getattr(a, name)
        if v and v.lower() not in BY_SLUG:
            print(f"unknown scheme '{v}'. Try --list.", file=sys.stderr)
            return 2
    if a.apply or a.light_scheme or a.dark_scheme or a.light or a.dark or a.auto or a.reapply or a.wallpaper or a.solid:
        st = current_state()
        fresh = not os.path.exists(STATE)
        if a.light or a.dark or a.auto:
            st["mode"] = "auto" if a.auto else ("dark" if a.dark else "light")
        if a.apply:
            slug = a.apply.lower()
            targets = ["dark"] if a.dark else ["light"] if a.light else ["light", "dark"]
            for m in (["light", "dark"] if fresh else targets):
                st[m] = slug
        if a.light_scheme:
            st["light"] = a.light_scheme.lower()
        if a.dark_scheme:
            st["dark"] = a.dark_scheme.lower()
        if a.wallpaper or a.solid:
            st["background"] = "wallpaper" if a.wallpaper else "solid"
        problems = apply(st)
        for p in problems:
            print("warning:", p, file=sys.stderr)
        return 1 if problems else 0
    return gui(current_state())


if __name__ == "__main__":
    sys.exit(main())
