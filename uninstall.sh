#!/usr/bin/env bash
# Remove the Cathode 98 theme and switch back to Breeze.
#   ./uninstall.sh            remove from your user
#   sudo ./uninstall.sh --system
set -euo pipefail

SYSTEM=0
[ "${1:-}" = "--system" ] && SYSTEM=1

if [ "$SYSTEM" = 1 ]; then
    DATA=/usr/share
else
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
    if command -v plasma-apply-lookandfeel >/dev/null 2>&1; then
        plasma-apply-lookandfeel --apply org.kde.breeze.desktop || true
    fi
    if command -v kwriteconfig6 >/dev/null 2>&1; then
        CONF="${XDG_CONFIG_HOME:-$HOME/.config}"
        kwriteconfig6 --file "$CONF/kwinrc" --group org.kde.kdecoration2 --key library org.kde.breeze
        kwriteconfig6 --file "$CONF/kwinrc" --group org.kde.kdecoration2 --key theme Breeze
        kwriteconfig6 --file "$CONF/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnLeft "MS"
        kwriteconfig6 --file "$CONF/kwinrc" --group org.kde.kdecoration2 --key ButtonsOnRight "HIAX"
        kwriteconfig6 --file "$CONF/kdeglobals" --group KDE --key widgetStyle Breeze
        command -v plasma-apply-colorscheme >/dev/null 2>&1 && plasma-apply-colorscheme BreezeLight >/dev/null 2>&1 || true
        [ -x /usr/libexec/plasma-changeicons ] && /usr/libexec/plasma-changeicons breeze >/dev/null 2>&1 || true
        kwriteconfig6 --file "$CONF/kdeglobals" --group WM --key activeFont --delete
        for k in font menuFont toolBarFont smallestReadableFont; do
            kwriteconfig6 --file "$CONF/kdeglobals" --group General --key "$k" --delete
        done
        kwriteconfig6 --file "$CONF/kdeglobals" --group Sounds --key Theme ocean
        kwriteconfig6 --file "$CONF/kcminputrc" --group Mouse --key cursorTheme breeze_cursors
        command -v plasma-apply-cursortheme >/dev/null 2>&1 && plasma-apply-cursortheme breeze_cursors >/dev/null 2>&1 || true
        # KDE's light/dark global themes and day/night switching back to Breeze
        kwriteconfig6 --file "$CONF/kdeglobals" --group KDE --key AutomaticLookAndFeel --notify false
        kwriteconfig6 --file "$CONF/kdeglobals" --group KDE --key DefaultLightLookAndFeel --notify --delete
        kwriteconfig6 --file "$CONF/kdeglobals" --group KDE --key DefaultDarkLookAndFeel --notify --delete
        # back to Plasma's standard desktop shell (its panels were left untouched)
        kwriteconfig6 --file "$CONF/plasmashellrc" --group Shell --key ShellPackage --delete
        systemctl --user restart plasma-plasmashell.service >/dev/null 2>&1 || true
    fi
fi

rm -rf "${DATA:?}/icons/Cathode" "${DATA:?}"/icons/Cathode-* "$DATA/icons/ModernXP" "$DATA/cathode" \
       "${DATA:?}"/color-schemes/Cathode98*.colors "${DATA:?}"/aurorae/themes/Cathode98* \
       "$DATA/plasma/desktoptheme/Cathode98" "$DATA/plasma/desktoptheme/Cathode98Dark" \
       "$DATA/plasma/look-and-feel/org.cathode.desktop" "$DATA/plasma/look-and-feel/org.cathode.desktop.dark" \
       "$DATA/plasma/plasmoids/org.cathode.clock" "$DATA/plasma/plasmoids/org.cathode.startmenu" "$DATA/sounds/KDE-3-Sounds" \
       "$DATA/plasma/shells/org.cathode.desktop" "$DATA/applications/org.cathode.display.desktop"
pkill -f "cathode_display.py --watch" >/dev/null 2>&1 || true
if [ "$SYSTEM" = 1 ]; then
    rm -f /usr/local/bin/cathode-display /etc/xdg/autostart/org.cathode.display-helper.desktop
else
    rm -f "$HOME/.local/bin/cathode-display" "${XDG_CONFIG_HOME:-$HOME/.config}/cathoderc" \
          "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/org.cathode.display-helper.desktop"
fi
[ "$SYSTEM" = 1 ] && command -v kwriteconfig6 >/dev/null 2>&1 && kwriteconfig6 --file /etc/xdg/plasmashellrc --group Shell --key ShellPackage --delete
if [ -d /usr/share/plymouth/themes/cathode ] && command -v plymouth-set-default-theme >/dev/null 2>&1; then
    echo "The Cathode boot animation is still installed. To remove it:"
    echo "  sudo plymouth-set-default-theme -R bgrt && sudo rm -rf /usr/share/plymouth/themes/cathode"
fi
echo "Cathode removed. The SE98 icon theme was left in $DATA/icons/SE98; delete it too if you don't want it."
