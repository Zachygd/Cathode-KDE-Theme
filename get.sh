#!/usr/bin/env bash
# One-line install of the latest Cathode KDE Theme release:
#
#   curl -fsSL https://raw.githubusercontent.com/Zachygd/Cathode-KDE-Theme/main/get.sh | bash
#
# Options go after "bash -s --", for example:
#   curl -fsSL https://raw.githubusercontent.com/Zachygd/Cathode-KDE-Theme/main/get.sh | bash -s -- --scheme teal --dark
set -euo pipefail
URL="https://github.com/Zachygd/Cathode-KDE-Theme/releases/latest/download/Cathode-KDE-Theme.tar.gz"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
echo "Downloading the latest Cathode release..."
curl -fL --progress-bar "$URL" -o "$WORK/cathode.tar.gz"
tar -xzf "$WORK/cathode.tar.gz" -C "$WORK"
DIR="$(find "$WORK" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
# when piped into bash, questions have to be read from the terminal
if [ ! -t 0 ] && [ -r /dev/tty ]; then
    exec </dev/tty
fi
bash "$DIR/install.sh" "$@"
