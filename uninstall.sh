#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if (( EUID == 0 )); then echo 'Ejecuta sin sudo.' >&2; exit 1; fi
python3 setup.py restore
fc-cache -f
