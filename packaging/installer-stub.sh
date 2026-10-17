#!/usr/bin/env bash
# shellcheck disable=SC2329,SC2317  # functions run from the EXIT trap; the archive marker is never executed
# Cathode KDE Theme - self-extracting installer.
#
#   Double-click it (or run ./Cathode-Installer.run) and follow the prompts.
#
#   ./Cathode-Installer.run --uninstall      remove Cathode, back to Breeze
#   ./Cathode-Installer.run -- [options]     pass options straight to install.sh
#                                            (e.g. -- --scheme teal --dark -y)
#   ./Cathode-Installer.run --extract DIR    just unpack the theme into DIR
#
# The theme itself is a compressed archive appended to the end of this file.
set -euo pipefail
VERSION="@VERSION@"
SELF="$(readlink -f "$0")"

# Double-clicked from the file manager: reopen in a terminal, so you can see what
# it's doing and type your password when it installs the Tahoma font.
if [ $# -eq 0 ] && [ ! -t 0 ] && [ -z "${CATHODE_IN_TERMINAL:-}" ] \
   && { [ -n "${WAYLAND_DISPLAY:-}" ] || [ -n "${DISPLAY:-}" ]; }; then
    export CATHODE_IN_TERMINAL=1
    if command -v konsole >/dev/null 2>&1; then exec konsole -e bash "$SELF" "$@"; fi
    if command -v kgx >/dev/null 2>&1; then exec kgx -- bash "$SELF" "$@"; fi
    if command -v gnome-terminal >/dev/null 2>&1; then exec gnome-terminal -- bash "$SELF" "$@"; fi
    if command -v xterm >/dev/null 2>&1; then exec xterm -e bash "$SELF" "$@"; fi
    command -v kdialog >/dev/null 2>&1 && kdialog --error "Please run Cathode-Installer.run from a terminal."
    exit 1
fi

pause() {
    # keep the window open when we opened it ourselves
    if [ -n "${CATHODE_IN_TERMINAL:-}" ]; then
        echo
        read -r -p "Press Enter to close this window. " _ || true
    fi
}
bold() { printf '\033[1m%s\033[0m\n' "$*"; }

WORK="$(mktemp -d)"
cleanup() { rm -rf "$WORK"; pause; }
trap cleanup EXIT
LINE="$(awk '/^__CATHODE_ARCHIVE_BELOW__$/ { print NR + 1; exit }' "$SELF")"
tail -n +"$LINE" "$SELF" | tar -xz -C "$WORK"
DIR="$(find "$WORK" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

case "${1:-}" in
    --extract)
        dest="${2:?usage: --extract DIR}"
        mkdir -p "$dest"
        cp -a "$DIR/." "$dest/"
        echo "Unpacked Cathode $VERSION into $dest"
        exit 0 ;;
    --uninstall)
        bash "$DIR/uninstall.sh"
        exit 0 ;;
    --)
        shift
        bash "$DIR/install.sh" "$@"
        exit 0 ;;
    -h|--help)
        sed -n '3,13p' "$SELF" | sed 's/^# \{0,1\}//'
        exit 0 ;;
    "") ;;
    *)
        bash "$DIR/install.sh" "$@"
        exit 0 ;;
esac

# ---- interactive ----------------------------------------------------------------
clear 2>/dev/null || true
bold "Cathode $VERSION - a Windows 98 style desktop for KDE Plasma 6"
echo
if command -v plasmashell >/dev/null 2>&1; then
    pv="$(plasmashell --version 2>/dev/null | awk '{print $NF}')"
    case "$pv" in
        6.*) echo "Found KDE Plasma $pv." ;;
        *) echo "Warning: Cathode needs KDE Plasma 6 (found: ${pv:-unknown}). It may not work here." ;;
    esac
else
    echo "Warning: KDE Plasma doesn't seem to be installed. Cathode is a theme for KDE Plasma 6."
fi
echo
echo "  1) Install Cathode"
echo "  2) Uninstall Cathode"
echo "  q) Quit"
echo
read -r -p "Choose [1]: " choice
case "${choice:-1}" in
    1) ;;
    2) bash "$DIR/uninstall.sh"; exit 0 ;;
    *) exit 0 ;;
esac

echo
read -r -p "Light or dark? [L/d]: " mode
args=()
case "$mode" in [dD]*) args+=(--dark) ;; esac

schemes="$(grep -o '"slug": "[a-z]*"' "$DIR/share/cathode/schemes.json" | cut -d'"' -f4 | tr '\n' ' ')"
echo
echo "Colour schemes: $schemes"
echo "(You can change this any time later in Display Properties.)"
while true; do
    read -r -p "Colour scheme [cathode]: " scheme
    scheme="$(echo "${scheme:-cathode}" | tr '[:upper:]' '[:lower:]')"
    case " $schemes " in *" $scheme "*) break ;; esac
    echo "  '$scheme' isn't one of the schemes above."
done
args+=(--scheme "$scheme")

echo
bash "$DIR/install.sh" "${args[@]}"
exit 0
__CATHODE_ARCHIVE_BELOW__
