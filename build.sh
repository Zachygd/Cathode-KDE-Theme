#!/usr/bin/env bash
# Regenerate every generated asset from the Python sources in build/.
# Needs: python3, Pillow, numpy. Optional inputs:
#   SE98=/path/to/Win98SE/SE98            render previews (also needs PySide6)
#   MODERNXP=/path/to/modernXP-cursor-theme rebuild the cursors (needs resvg-py)
set -euo pipefail
cd "$(dirname "$0")"
# ---- colour schemes (defined in build/schemes.py) ----------------------------
LOGOS="$(mktemp -d)"
python3 build/gen_logos.py build/logo/cathode-logo.png "$LOGOS"
rm -rf icons/Cathode icons/Cathode-* aurorae/themes/* plasma/desktoptheme/* share/cathode/start share/cathode/start-button*.png
python3 build/gen_colors.py color-schemes
python3 build/gen_icons.py "$LOGOS/cathode.png" icons/Cathode
# one line per scheme: slug  LightThemeId  DarkThemeId  IconThemeName
python3 -c 'import sys; sys.path.insert(0, "build"); import schemes as s
for x in s.ALL: print(x["slug"], s.theme_id(x["slug"], False), s.theme_id(x["slug"], True), "Cathode-" + x["name"])' > "$LOGOS/list"
for variant in light dark; do
    pid=$([ "$variant" = light ] && echo Cathode98 || echo Cathode98Dark)
    CATHODE_VARIANT="$variant" python3 build/gen_plasma.py "plasma/desktoptheme/$pid"
done
# the standard scheme is first in the list, so its caption buttons exist before others link to them
while read -r slug light_id dark_id icon_name; do
    for variant in light dark; do
        id=$([ "$variant" = light ] && echo "$light_id" || echo "$dark_id")
        CATHODE_VARIANT="$variant" CATHODE_SCHEME="$slug" python3 build/gen_aurorae.py "aurorae/themes/$id" >/dev/null
        CATHODE_VARIANT="$variant" CATHODE_SCHEME="$slug" python3 build/gen_startbutton.py "$LOGOS/$slug.png" share/cathode/start >/dev/null
    done
    if [ "$slug" != cathode ]; then
        python3 build/gen_icons.py "$LOGOS/$slug.png" "icons/$icon_name" "$icon_name" Cathode >/dev/null
    fi
done < "$LOGOS/list"
# scheme table for QML, and the lock screen logo in every scheme colour
python3 build/schemes.py --json share/cathode/schemes.json
python3 build/schemes.py --js plasma/shells/org.cathode.desktop/contents/components/CathodeSchemes.js
LOCKLOGO=plasma/shells/org.cathode.desktop/contents/lockscreen/images/logos
rm -rf "$LOCKLOGO"; mkdir -p "$LOCKLOGO"
python3 -c 'import sys, os; from PIL import Image
src, out = sys.argv[1], sys.argv[2]
for f in os.listdir(src):
    if f.endswith(".png"):
        im = Image.open(os.path.join(src, f)); im.thumbnail((288, 141), Image.LANCZOS); im.save(os.path.join(out, f), optimize=True)' "$LOGOS" "$LOCKLOGO"
rm -rf plasma/shells/org.cathode.desktop/contents/logout/images/logos
cp -a "$LOCKLOGO" plasma/shells/org.cathode.desktop/contents/logout/images/logos
rm -rf "$LOGOS"
echo "schemes: $(ls aurorae/themes | wc -l) window themes, $(ls share/cathode/start | wc -l) Start buttons"

FRAMES="$(mktemp -d)"
python3 build/gen_frames.py build/logo/cathode-storyboard.png "$FRAMES"
python3 build/gen_brand.py "$FRAMES" build/logo/cathode-logo.png \
    plasma/look-and-feel/org.cathode.desktop/contents/splash/images share/plymouth/cathode
rm -rf "$FRAMES"
if [ -n "${MODERNXP:-}" ]; then
    python3 build/gen_cursors.py "$MODERNXP" share/cursors/ModernXP
fi
if [ -n "${SE98:-}" ]; then
    python3 build/preview_window.py aurorae/themes/Cathode98 build/preview-window.png
    MENU_OPEN=1 python3 build/preview_desktop.py "$SE98" build/preview-desktop.png
    CATHODE_VARIANT=dark MENU_OPEN=1 python3 build/preview_desktop.py "$SE98" build/preview-desktop-dark.png
    # small previews for Cathode Display Properties, one per scheme and mode
    rm -rf share/cathode/previews; mkdir -p share/cathode/previews
    for slug in $(python3 -c 'import sys; sys.path.insert(0, "build"); import schemes; print(" ".join(x["slug"] for x in schemes.ALL))'); do
        for variant in light dark; do
            suffix=$([ "$variant" = dark ] && echo "-dark" || true)
            CATHODE_SCHEME="$slug" CATHODE_VARIANT="$variant" MENU_OPEN=1 PREVIEW_SIZE=400x300 \
                python3 build/preview_desktop.py "$SE98" "share/cathode/previews/$slug$suffix.png" >/dev/null 2>&1
        done
    done
    echo "previews: $(ls share/cathode/previews | wc -l)"
fi
# The sign-out dialog lives in the Cathode shell package (Plasma 6.8+) and is
# mirrored into the global theme for Plasma 6.7 and older.
L=plasma/look-and-feel/org.cathode.desktop/contents
SH=plasma/shells/org.cathode.desktop/contents
rm -rf "$L/logout" "$L/components"
cp -a "$SH/logout" "$SH/components" "$L/"
# Plasma looks for "<shell id>-layout.js"; keep the layout for both shell ids.
cp "$L/layouts/org.kde.plasma.desktop-layout.js" "$L/layouts/org.cathode.desktop-layout.js"
# Dark global theme, derived from the light one
python3 build/gen_lnf_variant.py dark
echo "Rebuilt."
