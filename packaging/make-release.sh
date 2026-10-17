#!/usr/bin/env bash
# Build the release downloads into dist/ (or the folder given):
#   Cathode-Installer.run       self-extracting installer (double-click or run it)
#   Cathode-KDE-Theme.tar.gz    the theme folder, for ./install.sh (also used by get.sh)
#   SHA256SUMS
# and RELEASE_NOTES.md next to them (this version's section of CHANGELOG.md).
# GitHub Actions runs this when a version tag (v1.2.3) is pushed.
set -euo pipefail
cd "$(dirname "$0")/.."
VER="$(cat VERSION)"
OUT="${1:-dist}"
NAME="Cathode-KDE-Theme"

rm -rf "$OUT"
mkdir -p "$OUT"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir "$STAGE/$NAME-$VER"
tar -c --exclude=./.git --exclude=./.github --exclude=./dist --exclude="./$OUT" --exclude=./docs \
       --exclude=__pycache__ --exclude='*.pyc' --exclude=./RELEASE_NOTES.md . \
    | tar -x -C "$STAGE/$NAME-$VER"
# executables stay executable for people who unpack it by hand
chmod +x "$STAGE/$NAME-$VER"/{install.sh,uninstall.sh,build.sh,get.sh} \
         "$STAGE/$NAME-$VER/share/cathode/app/cathode_display.py"
tar -czf "$OUT/$NAME.tar.gz" --owner=0 --group=0 -C "$STAGE" "$NAME-$VER"

sed "s/@VERSION@/$VER/" packaging/installer-stub.sh > "$OUT/Cathode-Installer.run"
cat "$OUT/$NAME.tar.gz" >> "$OUT/Cathode-Installer.run"
chmod +x "$OUT/Cathode-Installer.run"

(cd "$OUT" && sha256sum Cathode-Installer.run "$NAME.tar.gz" > SHA256SUMS)

# release notes: the "## <version>" section of CHANGELOG.md
awk -v v="$VER" '
    /^## / { on = ($2 == v) ; if (on) next }
    on { print }
' CHANGELOG.md > RELEASE_NOTES.md
cat >> RELEASE_NOTES.md <<EOF

### Install

Download **Cathode-Installer.run**, then double-click it (or run \`chmod +x Cathode-Installer.run && ./Cathode-Installer.run\`).
Or in a terminal: \`curl -fsSL https://raw.githubusercontent.com/Zachygd/Cathode-KDE-Theme/main/get.sh | bash\`
EOF
echo "Cathode $VER ->"
ls -la "$OUT"
