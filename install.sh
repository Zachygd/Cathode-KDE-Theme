#!/usr/bin/env bash
# Cathode 98 theme installer for KDE Plasma 6 (Fedora).
#
#   ./install.sh                 install for your user and apply it
#   ./install.sh --dark          start in dark mode
#   ./install.sh --scheme brick  start with another colour scheme (see the list below);
#                                change it any time in Display Properties
#   ./install.sh --keep-layout   apply colors/frames/icons but leave your panels alone
#   ./install.sh --no-apply      just copy the files
#   ./install.sh --extras        also install the Chicago95 GTK theme (for GTK apps)
#   ./install.sh --plymouth      also install the Cathode boot animation (asks for sudo)
#   sudo ./install.sh --system   install to /usr/share (for the Cathode spin / all users)
#   sudo ./install.sh --system --make-default   ...and make it the default for new users
#
#   Schemes: cathode brick pumpkin wheat ember spruce meadow marine teal plum
#            eggplant rose storm slate spectrum sunset
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SE98_REPO="https://github.com/nestoris/Win98SE.git"
SE98_ZIP="https://github.com/nestoris/Win98SE/archive/refs/heads/main.zip"
CHICAGO95_REPO="https://github.com/grassmunk/Chicago95.git"

SYSTEM=0 APPLY=1 RESET_LAYOUT=1 MAKE_DEFAULT=0 EXTRAS=0 PLYMOUTH=0 ASSUME_YES=0 ICONS_FROM="" DARK=0 SCHEME=cathode SCHEME_SET=0
PLASMA_DESKTOP_REPO="https://github.com/KDE/plasma-desktop.git"

usage() { sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
    case "$1" in
        --system) SYSTEM=1; APPLY=0 ;;
        --make-default) MAKE_DEFAULT=1 ;;
        --no-apply) APPLY=0 ;;
        --keep-layout) RESET_LAYOUT=0 ;;
        --extras) EXTRAS=1 ;;
        --plymouth) PLYMOUTH=1 ;;
        --dark) DARK=1 ;;
        --scheme) SCHEME="$(echo "${2:-}" | tr '[:upper:]' '[:lower:]')"; SCHEME_SET=1; shift ;;
        --icons-from) ICONS_FROM="$2"; shift ;;
        -y|--yes) ASSUME_YES=1 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
    esac
    shift
done

# Every scheme is installed, light and dark; this picks which one gets applied.
# Ids: Cathode98[Dark] for the standard blue, Cathode98<Name>[Dark] for the rest.
if ! grep -q "\"slug\": \"$SCHEME\"" "$HERE/share/cathode/schemes.json"; then
    echo "Unknown scheme '$SCHEME'. Schemes: $(grep -o '"slug": "[a-z]*"' "$HERE/share/cathode/schemes.json" | cut -d'"' -f4 | tr '\n' ' ')" >&2
    exit 1
fi
SCHEME_NAME="$(echo "${SCHEME:0:1}" | tr '[:lower:]' '[:upper:]')${SCHEME:1}"
if [ "$SCHEME" = cathode ]; then
    THEME_ID="Cathode98"; ICON_THEME="Cathode"
else
    THEME_ID="Cathode98$SCHEME_NAME"; ICON_THEME="Cathode-$SCHEME_NAME"
fi
if [ "$DARK" = 1 ]; then
    LNF_ID="org.cathode.desktop.dark"; THEME_ID="${THEME_ID}Dark"; PLASMA_ID="Cathode98Dark"
else
    LNF_ID="org.cathode.desktop"; PLASMA_ID="Cathode98"
fi
PLASMA_THEMES=(Cathode98 Cathode98Dark)
LNFS=(org.cathode.desktop org.cathode.desktop.dark)

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }

if [ "$SYSTEM" = 1 ]; then
    [ "$(id -u)" = 0 ] || { echo "--system needs root (run with sudo)" >&2; exit 1; }
    DATA=/usr/share
else
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
fi
ICONS="$DATA/icons"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/cathode-theme"
[ "$SYSTEM" = 1 ] && CACHE="/var/cache/cathode-theme"
mkdir -p "$ICONS" "$DATA/color-schemes" "$DATA/aurorae/themes" "$DATA/plasma/desktoptheme" \
         "$DATA/plasma/look-and-feel" "$DATA/plasma/plasmoids" "$DATA/plasma/shells" "$DATA/sounds" "$DATA/cathode" \
         "$DATA/applications" "$CACHE"

# ---------------------------------------------------------------------------
# 1. SE98 icon theme (nestoris/Win98SE, GPL-2.0)
# ---------------------------------------------------------------------------
install_se98() {
    local src=""
    if [ -n "$ICONS_FROM" ]; then
        src="$ICONS_FROM"
        [ -f "$src/index.theme" ] || src="$ICONS_FROM/SE98"
    elif command -v git >/dev/null 2>&1; then
        if [ -d "$CACHE/Win98SE/.git" ]; then
            say "Updating SE98 icons"
            git -C "$CACHE/Win98SE" pull --ff-only --quiet || warn "could not update SE98, using cached copy"
        else
            say "Downloading SE98 icons (about 50 MB)"
            git clone --depth 1 --quiet "$SE98_REPO" "$CACHE/Win98SE"
        fi
        src="$CACHE/Win98SE/SE98"
    else
        say "Downloading SE98 icons (zip)"
        curl -fL --retry 2 -o "$CACHE/se98.zip" "$SE98_ZIP"
        rm -rf "$CACHE/Win98SE-main"
        (cd "$CACHE" && unzip -q -o se98.zip)
        src="$CACHE/Win98SE-main/SE98"
    fi
    [ -f "$src/index.theme" ] || { echo "SE98 icon theme not found at $src" >&2; exit 1; }
    rm -rf "$ICONS/SE98"
    cp -a "$src" "$ICONS/SE98"
    if [ -f "$(dirname "$src")/LICENSE" ]; then
        cp "$(dirname "$src")/LICENSE" "$ICONS/SE98/LICENSE"
    fi
}

if [ -f "$ICONS/SE98/index.theme" ] && [ -z "$ICONS_FROM" ] && [ ! -d "$CACHE/Win98SE/.git" ]; then
    say "SE98 icons already installed"
else
    install_se98
fi

# ---------------------------------------------------------------------------
# 2. Cathode pieces
# ---------------------------------------------------------------------------
say "Installing Cathode theme files into $DATA"
# (old copies first, so a scheme removed from the theme doesn't linger)
rm -rf "$ICONS"/Cathode "$ICONS"/Cathode-* "$ICONS/ModernXP" "$DATA/plasma/plasmoids/org.cathode.clock" \
       "$DATA/sounds/KDE-3-Sounds" "$DATA/plasma/shells/org.cathode.desktop" \
       "${DATA:?}"/aurorae/themes/Cathode98* "${DATA:?}"/color-schemes/Cathode98*.colors \
       "$DATA/cathode/app" "$DATA/cathode/start" "$DATA/cathode/previews" "$DATA"/cathode/start-button*.png
cp -a "$HERE"/icons/Cathode "$HERE"/icons/Cathode-*         "$ICONS/"
cp -a "$HERE"/color-schemes/Cathode98*.colors               "$DATA/color-schemes/"
cp -a "$HERE"/aurorae/themes/Cathode98*                     "$DATA/aurorae/themes/"   # keeps the shared-button links
for t in "${PLASMA_THEMES[@]}"; do
    rm -rf "${DATA:?}/plasma/desktoptheme/$t"
    cp -a "$HERE/plasma/desktoptheme/$t"                    "$DATA/plasma/desktoptheme/"
done
for l in "${LNFS[@]}"; do
    rm -rf "${DATA:?}/plasma/look-and-feel/$l"
    cp -a "$HERE/plasma/look-and-feel/$l"                   "$DATA/plasma/look-and-feel/"
done
cp -a "$HERE/plasma/plasmoids/org.cathode.clock"            "$DATA/plasma/plasmoids/"
cp -a "$HERE/plasma/shells/org.cathode.desktop"             "$DATA/plasma/shells/"
cp -a "$HERE/share/cathode/."                               "$DATA/cathode/"
cp -a "$HERE/share/cursors/ModernXP"                        "$ICONS/ModernXP"
cp -a "$HERE/share/sounds/KDE-3-Sounds"                     "$DATA/sounds/KDE-3-Sounds"

# Cathode Display Properties (colour scheme switcher)
APP="$DATA/cathode/app/cathode_display.py"
chmod +x "$APP"
if [ "$SYSTEM" = 1 ]; then BIN=/usr/local/bin; else BIN="$HOME/.local/bin"; fi
mkdir -p "$BIN"
printf '#!/bin/sh\nexec python3 "%s" "$@"\n' "$APP" > "$BIN/cathode-display"
chmod +x "$BIN/cathode-display"
sed "s|@APP@|python3 \"$APP\"|" "$HERE/share/applications/org.cathode.display.desktop" \
    > "$DATA/applications/org.cathode.display.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q "$DATA/applications" 2>/dev/null || true
# (stop a helper left running by an older version; Display Properties starts the new one)
[ "$SYSTEM" = 1 ] || pkill -f "cathode_display.py --watch" >/dev/null 2>&1 || true
# Small login helper: when KDE switches light/dark (day and night, or the Brightness
# and Color menu), it sets the matching desktop colour, which global themes can't carry.
if [ "$SYSTEM" = 1 ]; then AUTOSTART=/etc/xdg/autostart; else AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"; fi
mkdir -p "$AUTOSTART"
cat > "$AUTOSTART/org.cathode.display-helper.desktop" <<EOF2
[Desktop Entry]
Type=Application
Name=Cathode desktop colour helper
Comment=Keeps the desktop colour in step with the Cathode colour scheme
Exec=python3 "$APP" --watch
OnlyShowIn=KDE;
NoDisplay=true
X-KDE-autostart-phase=2
EOF2

# It needs Qt for Python (Fedora: python3-pyside6).
have_pyside() { python3 -c 'import PySide6.QtWidgets' >/dev/null 2>&1 || python3 -c 'import PyQt6.QtWidgets' >/dev/null 2>&1; }
if ! have_pyside && command -v dnf >/dev/null 2>&1 && { [ "$(id -u)" = 0 ] || [ -t 0 ]; }; then
    say "Installing Qt for Python, for Display Properties$([ "$(id -u)" = 0 ] || echo " (asks for your password)")"
    $([ "$(id -u)" = 0 ] || echo sudo) dnf install -y -q python3-pyside6 || true
fi
have_pyside || warn "Display Properties needs Qt for Python: sudo dnf install python3-pyside6"

# ---------------------------------------------------------------------------
# Cathode Start: Plasma's Application Menu (Kicker) patched so the Start button
# stays pushed in while open. Kicker changes between Plasma releases, so it is
# built from the Kicker source matching the Plasma version installed here.
# ---------------------------------------------------------------------------
build_start_menu() {
    local ver tag src
    command -v plasmashell >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1 && command -v git >/dev/null 2>&1 || return 1
    ver="$(plasmashell --version 2>/dev/null | awk '{print $NF}')"
    [ -n "$ver" ] || return 1
    for tag in "v$ver" "v${ver%.*}.0"; do
        src="$CACHE/kicker-$tag"
        if [ ! -f "$src/applets/kicker/main.qml" ]; then
            rm -rf "$src"
            if ! git clone --quiet --depth 1 --branch "$tag" --filter=blob:none --sparse "$PLASMA_DESKTOP_REPO" "$src" >/dev/null 2>&1 \
                || ! git -C "$src" sparse-checkout set applets/kicker >/dev/null 2>&1; then
                rm -rf "$src"
                continue
            fi
        fi
        if python3 "$HERE/build/make_startmenu.py" "$src/applets/kicker" "$DATA/plasma/plasmoids/org.cathode.startmenu" >/dev/null; then
            say "Built Cathode Start for Plasma $ver"
            return 0
        fi
    done
    return 1
}
if ! build_start_menu; then
    rm -rf "$DATA/plasma/plasmoids/org.cathode.startmenu"
    warn "could not build Cathode Start; using Plasma's standard menu (the Start button won't press in)"
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    for t in "$ICONS"/Cathode "$ICONS"/Cathode-*; do gtk-update-icon-cache -q -f -t "$t" 2>/dev/null || true; done
    gtk-update-icon-cache -q -f -t "$ICONS/SE98" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 3. Optional: Chicago95 GTK theme (GTK apps such as Firefox, Steam)
# ---------------------------------------------------------------------------
if [ "$EXTRAS" = 1 ]; then
    say "Downloading Chicago95 (GTK theme)"
    if [ -d "$CACHE/Chicago95/.git" ]; then
        git -C "$CACHE/Chicago95" pull --ff-only --quiet || true
    else
        git clone --depth 1 --quiet "$CHICAGO95_REPO" "$CACHE/Chicago95"
    fi
    mkdir -p "$DATA/themes"
    rm -rf "$DATA/themes/Chicago95"
    cp -a "$CACHE/Chicago95/Theme/Chicago95" "$DATA/themes/Chicago95"
fi

# ---------------------------------------------------------------------------
# Optional: Plymouth boot animation (system-wide, rebuilds the initramfs)
# ---------------------------------------------------------------------------
if [ "$PLYMOUTH" = 1 ]; then
    if command -v plymouth-set-default-theme >/dev/null 2>&1; then
        SUDO=""
        [ "$(id -u)" = 0 ] || SUDO="sudo"
        say "Installing the Cathode boot animation (this rebuilds your initramfs; it takes a minute)"
        $SUDO rm -rf /usr/share/plymouth/themes/cathode
        $SUDO mkdir -p /usr/share/plymouth/themes
        $SUDO cp -a "$HERE/share/plymouth/cathode" /usr/share/plymouth/themes/cathode
        $SUDO plymouth-set-default-theme -R cathode
    else
        warn "plymouth isn't installed; skipping the boot animation"
    fi
fi

# ---------------------------------------------------------------------------
# 4. Pick the right Aurorae engine for this Plasma version
# ---------------------------------------------------------------------------
AURORAE_LIB="org.kde.kwin.aurorae"
for dir in /usr/lib64/qt6/plugins /usr/lib/qt6/plugins /usr/lib/x86_64-linux-gnu/qt6/plugins; do
    if ls "$dir"/org.kde.kdecoration*/org.kde.kwin.aurorae.v2.so >/dev/null 2>&1; then
        AURORAE_LIB="org.kde.kwin.aurorae.v2"
        break
    fi
done

# The global themes name the frame engine; point them at the one this Plasma has,
# so switching themes in System Settings works too.
for l in "${LNFS[@]}"; do
    sed -i "s/^library=org\.kde\.kwin\.aurorae.*/library=$AURORAE_LIB/" "$DATA/plasma/look-and-feel/$l/contents/defaults"
done

# ---------------------------------------------------------------------------
# Font: Wine Tahoma (LGPL, packaged by Fedora as wine-tahoma-fonts)
# ---------------------------------------------------------------------------
have_tahoma() { command -v fc-list >/dev/null 2>&1 && fc-list : family | grep -qx "Tahoma"; }
# Fedora 44 names the package wine-tahoma-fonts-system; older releases use
# wine-tahoma-fonts. (wine-tahoma-winefonts only installs it for Wine itself.)
install_tahoma() {
    local pkg sudo_cmd=""
    [ "$(id -u)" = 0 ] || sudo_cmd="sudo"
    for pkg in wine-tahoma-fonts-system wine-tahoma-fonts; do
        if dnf -q list --available "$pkg" >/dev/null 2>&1 || dnf -q list --installed "$pkg" >/dev/null 2>&1; then
            $sudo_cmd dnf install -y -q "$pkg" && return 0
        fi
    done
    return 1
}
if ! have_tahoma && command -v dnf >/dev/null 2>&1; then
    if [ "$(id -u)" = 0 ] || [ -t 0 ]; then
        say "Installing the Wine Tahoma font$([ "$(id -u)" = 0 ] || echo " (asks for your password)")"
        install_tahoma || true
    fi
    command -v fc-cache >/dev/null 2>&1 && fc-cache -f >/dev/null 2>&1 || true
fi
if have_tahoma; then
    UI_FONT="Tahoma"
else
    UI_FONT="Noto Sans"
    warn "Wine Tahoma isn't installed (sudo dnf install wine-tahoma-fonts-system); keeping Noto Sans"
fi
font_spec() { echo "$UI_FONT,$1,-1,5,$2,0,0,0,0,0,0,0,0,0,0,1"; }

KWC=""
for k in kwriteconfig6 kwriteconfig5; do command -v "$k" >/dev/null 2>&1 && { KWC="$k"; break; }; done
QDBUS=""
for q in qdbus6 qdbus-qt6 qdbus; do command -v "$q" >/dev/null 2>&1 && { QDBUS="$q"; break; }; done

# The Cathode shell package carries the lock screen and Shut Down dialog
# (Plasma 6.8 loads both from the shell package, not the global theme). It
# falls back to Plasma's standard desktop shell for everything else.
SHELL_ID="org.cathode.desktop"

stop_plasma() {
    systemctl --user stop plasma-plasmashell.service >/dev/null 2>&1 || kquitapp6 plasmashell >/dev/null 2>&1 || true
    sleep 1
}
start_plasma() {
    systemctl --user start plasma-plasmashell.service >/dev/null 2>&1 || (nohup plasmashell >/dev/null 2>&1 &)
}
wait_plasma() {
    [ -n "$QDBUS" ] || { sleep 5; return 0; }
    for _ in $(seq 1 40); do
        "$QDBUS" org.kde.plasmashell /PlasmaShell >/dev/null 2>&1 && { sleep 2; return 0; }
        sleep 0.5
    done
    return 1
}

# 16px tray icons, like 98. Written straight into the panel config so it also
# applies to a tray that already exists.
fix_tray() {
    local f="$1" line
    [ -f "$f" ] && command -v python3 >/dev/null 2>&1 || return 0
    while IFS= read -r line; do
        local args=() part
        IFS=$'\t' read -r -a parts <<< "$line"
        for part in "${parts[@]}"; do args+=(--group "$part"); done
        $KWC --file "$f" "${args[@]}" --group General --key iconSize 0
        $KWC --file "$f" "${args[@]}" --group General --key scaleIconsToFit --type bool false
        $KWC --file "$f" "${args[@]}" --group General --key iconSpacing 1
    done < <(python3 - "$f" <<'PY'
import re, sys
group = None
for raw in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = raw.strip()
    if line.startswith("["):
        group = re.findall(r"\[([^\]]*)\]", line)
    elif group and line == "plugin=org.kde.plasma.systemtray":
        print("\t".join(group))
PY
)
}

write_settings() {
    # $1 = extra args for kwriteconfig (e.g. --file /etc/xdg/kwinrc)
    local kwin="$1" globals="$2" plasmarc="$3" splash="$4" input="$5"
    $KWC --file "$kwin" --group org.kde.kdecoration2 --key library "$AURORAE_LIB"
    $KWC --file "$kwin" --group org.kde.kdecoration2 --key theme "__aurorae__svg__$THEME_ID"
    $KWC --file "$kwin" --group org.kde.kdecoration2 --key ButtonsOnLeft "M"
    $KWC --file "$kwin" --group org.kde.kdecoration2 --key ButtonsOnRight "IA_X"
    $KWC --file "$kwin" --group org.kde.kdecoration2 --key BorderSize "Normal"
    $KWC --file "$kwin" --group org.kde.kdecoration2 --key BorderSizeAuto --type bool false
    $KWC --file "$globals" --group KDE --key widgetStyle "Windows"
    $KWC --file "$globals" --group General --key ColorScheme "$THEME_ID"
    $KWC --file "$globals" --group Icons --key Theme "$ICON_THEME"
    $KWC --file "$globals" --group General --key font "$(font_spec 9 400)"
    $KWC --file "$globals" --group General --key menuFont "$(font_spec 9 400)"
    $KWC --file "$globals" --group General --key toolBarFont "$(font_spec 9 400)"
    $KWC --file "$globals" --group General --key smallestReadableFont "$(font_spec 8 400)"
    $KWC --file "$globals" --group WM --key activeFont "$(font_spec 9 700)"
    $KWC --file "$plasmarc" --group Theme --key name "$PLASMA_ID"
    $KWC --file "$splash" --group KSplash --key Theme "org.cathode.desktop"
    $KWC --file "$globals" --group Sounds --key Theme "KDE-3-Sounds"
    $KWC --file "$input" --group Mouse --key cursorTheme "ModernXP"
}

# Copy a .colors file's colour groups into a kdeglobals file (what applying a
# colour scheme does), for new-user defaults where no session is running.
apply_colors_file() {
    local src="$1" dst="$2" group key value
    while IFS=$'\t' read -r group key value; do
        local args=() part
        IFS=$'\x1f' read -r -a parts <<< "$group"
        for part in "${parts[@]}"; do args+=(--group "$part"); done
        $KWC --file "$dst" "${args[@]}" --key "$key" "$value"
    done < <(python3 - "$src" <<'PY'
import re, sys
group = None
for raw in open(sys.argv[1], encoding="utf-8"):
    line = raw.strip()
    if line.startswith("["):
        group = re.findall(r"\[([^\]]*)\]", line)
        if not (group[0].startswith(("Colors:", "ColorEffects:", "WM")) or group[0] in ("General", "KDE")):
            group = None
    elif group and "=" in line:
        k, v = line.split("=", 1)
        print("\x1f".join(group) + "\t" + k + "\t" + v)
PY
)
}

# ---------------------------------------------------------------------------
# 5a. System install: optionally make Cathode the default for new users
# ---------------------------------------------------------------------------
if [ "$SYSTEM" = 1 ]; then
    if [ "$MAKE_DEFAULT" = 1 ]; then
        [ -n "$KWC" ] || { echo "kwriteconfig6 is required for --make-default" >&2; exit 1; }
        say "Making Cathode the default look for new users (/etc/xdg)"
        mkdir -p /etc/xdg
        write_settings /etc/xdg/kwinrc /etc/xdg/kdeglobals /etc/xdg/plasmarc /etc/xdg/ksplashrc /etc/xdg/kcminputrc
        # the scheme's colours themselves (the global theme only carries the standard blue)
        apply_colors_file "$DATA/color-schemes/$THEME_ID.colors" /etc/xdg/kdeglobals
        $KWC --file /etc/xdg/plasmashellrc --group Shell --key ShellPackage "$SHELL_ID"
        $KWC --file /etc/xdg/kdeglobals --group KDE --key LookAndFeelPackage "$LNF_ID"
        $KWC --file /etc/xdg/kdeglobals --group KDE --key DefaultLightLookAndFeel "org.cathode.desktop"
        $KWC --file /etc/xdg/kdeglobals --group KDE --key DefaultDarkLookAndFeel "org.cathode.desktop.dark"
    fi
    say "Done. Installed system-wide."
    exit 0
fi

# ---------------------------------------------------------------------------
# 5b. Per-user: apply it now
# ---------------------------------------------------------------------------
if [ "$APPLY" = 0 ]; then
    say "Files installed. Pick 'Cathode' in System Settings > Colors & Themes > Global Theme."
    exit 0
fi

command -v plasma-apply-lookandfeel >/dev/null 2>&1 || { warn "plasma-apply-lookandfeel not found; files are installed, apply the Global Theme manually"; exit 0; }
[ -n "$KWC" ] || { warn "kwriteconfig6 not found; files are installed, apply the Global Theme manually"; exit 0; }

if [ "$RESET_LAYOUT" = 1 ] && [ "$ASSUME_YES" = 0 ] && [ -t 0 ]; then
    echo
    echo "Cathode will replace your current panels and desktop layout with the Windows 98 taskbar."
    echo "(Run with --keep-layout to keep your panels and only change the look.)"
    read -r -p "Continue? [y/N] " ans
    case "$ans" in [yY]*) ;; *) RESET_LAYOUT=0; say "Keeping your current layout." ;; esac
fi

CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
for f in kwinrc kdeglobals kcminputrc plasmashellrc plasma-org.kde.plasma.desktop-appletsrc; do
    [ -f "$CONF/$f" ] && cp -a "$CONF/$f" "$CONF/$f.cathode-backup"
done

# Switch Plasma to the Cathode shell. Plasma keeps panels per shell, so carry the
# current ones over first (that's what --keep-layout keeps).
if [ ! -f "$CONF/plasma-$SHELL_ID-appletsrc" ] && [ -f "$CONF/plasma-org.kde.plasma.desktop-appletsrc" ]; then
    cp -a "$CONF/plasma-org.kde.plasma.desktop-appletsrc" "$CONF/plasma-$SHELL_ID-appletsrc"
fi
if [ "$(kreadconfig6 --file "$CONF/plasmashellrc" --group Shell --key ShellPackage 2>/dev/null)" != "$SHELL_ID" ]; then
    say "Switching Plasma to the Cathode shell"
    stop_plasma
    $KWC --file "$CONF/plasmashellrc" --group Shell --key ShellPackage "$SHELL_ID"
    start_plasma
    wait_plasma || warn "Plasma is taking a while to start; continuing anyway"
fi

say "Applying the $([ "$DARK" = 1 ] && echo "Cathode Dark" || echo "Cathode") global theme"
if [ "$RESET_LAYOUT" = 1 ]; then
    plasma-apply-lookandfeel --apply "$LNF_ID" --resetLayout
else
    plasma-apply-lookandfeel --apply "$LNF_ID"
fi

write_settings "$CONF/kwinrc" "$CONF/kdeglobals" "$CONF/plasmarc" "$CONF/ksplashrc" "$CONF/kcminputrc"
if command -v plasma-apply-cursortheme >/dev/null 2>&1; then
    plasma-apply-cursortheme ModernXP >/dev/null 2>&1 || true
fi
if [ "$EXTRAS" = 1 ]; then
    mkdir -p "$CONF/gtk-3.0" "$CONF/gtk-4.0"
    for g in gtk-3.0 gtk-4.0; do
        $KWC --file "$CONF/$g/settings.ini" --group Settings --key gtk-theme-name "Chicago95"
        $KWC --file "$CONF/$g/settings.ini" --group Settings --key gtk-icon-theme-name "Cathode"
    done
    command -v gsettings >/dev/null 2>&1 && {
        gsettings set org.gnome.desktop.interface gtk-theme Chicago95 2>/dev/null || true
        gsettings set org.gnome.desktop.interface icon-theme Cathode 2>/dev/null || true
    }
fi

# Plasma caches rendered SVG pieces; clear them so the new theme shows up cleanly.
rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}"/ksvg-elements* "${XDG_CACHE_HOME:-$HOME/.cache}"/plasma_theme_* \
       "${XDG_CACHE_HOME:-$HOME/.cache}"/plasma-svgelements* "${XDG_CACHE_HOME:-$HOME/.cache}"/icon-cache.kcache 2>/dev/null || true

say "Reloading KWin and Plasma"
[ -n "$QDBUS" ] && "$QDBUS" org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
wait_plasma || true
stop_plasma
fix_tray "$CONF/plasma-$SHELL_ID-appletsrc"
start_plasma

# Switch to the chosen scheme with Display Properties itself (colours, frames,
# icons, desktop colour) - the same thing it does when you press Apply.
wait_plasma || true
# On a reinstall without --scheme/--dark, your saved light/dark choices are kept.
if [ "$SCHEME_SET" = 1 ] || [ "$DARK" = 1 ] || [ ! -f "$CONF/cathoderc" ]; then
    say "Applying the $SCHEME_NAME$([ "$DARK" = 1 ] && echo " Dark") colour scheme"
    MODE_ARG="--light"; [ "$DARK" = 1 ] && MODE_ARG="--dark"
    python3 "$APP" --apply "$SCHEME" "$MODE_ARG" --solid \
        || warn "some scheme settings didn't apply; open Display Properties and press Apply"
else
    say "Re-applying your saved Display Properties choices"
    python3 "$APP" --reapply || warn "some scheme settings didn't apply; open Display Properties and press Apply"
fi

say "Done. Log out and back in once so every app picks up the Windows widget style."
say "Change colours any time: open 'Display Properties' from the menu (or run cathode-display)."
say "Backups of your old settings were saved next to them with a .cathode-backup suffix."
