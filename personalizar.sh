#!/usr/bin/env bash
set -euo pipefail
if (( EUID == 0 )); then echo 'Ejecuta sin sudo.' >&2; exit 1; fi
exec python3 "$HOME/.local/share/kali-dragon-ice/scripts/appearance.py" \
    --style "${1:-glass}" --scale "${2:-auto}"
