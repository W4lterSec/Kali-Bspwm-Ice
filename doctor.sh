#!/usr/bin/env bash
set -u
echo 'Kali Dragon Ice · diagnóstico'
printf '\nSistema: '; . /etc/os-release; echo "${PRETTY_NAME:-desconocido}"
for app in bspwm bspc sxhkd kitty rofi polybar picom python3 feh pamixer; do
    if command -v "$app" >/dev/null; then printf 'OK  %s\n' "$app"; else printf 'FALTA  %s\n' "$app"; fi
done
printf '\nFuente: '; fc-match 'Hack Nerd Font' 2>/dev/null || true
printf '\nBarra activa:\n'; pgrep -a -u "$(id -u)" -x polybar || true
printf '\nCompositor activo:\n'; pgrep -a -u "$(id -u)" -x picom || true
printf '\nResolución:\n'; xrandr --current 2>/dev/null | head -8 || true
printf '\nPreferencias:\n'; cat "$HOME/.config/kali-dragon-ice/settings.json" 2>/dev/null || true
printf '\nRed:\n'; python3 "$HOME/.local/share/kali-dragon-ice/scripts/network.py" 2>/dev/null || true
printf '\nRegistros: %s/kali-dragon-ice/\n' "${XDG_RUNTIME_DIR:-$HOME/.cache}"
python3 "$HOME/.local/share/kali-dragon-ice/scripts/check-graphics.py" || true
