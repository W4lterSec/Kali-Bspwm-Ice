#!/usr/bin/env bash
set -eu
export DRAGON_ROOT="$HOME/.local/share/kali-dragon-ice"
runtime="${XDG_RUNTIME_DIR:-$HOME/.cache}/kali-dragon-ice"
mkdir -p "$runtime"
chmod 700 "$runtime"
display_key=${DISPLAY//[^a-zA-Z0-9]/_}
launch() {
    local name=$1
    shift
    flock -w 2 -o "$runtime/$name-$display_key.lock" bash -c \
        'printf "%s\n" "$$" > "$1"; shift; exec "$@"' _ \
        "$runtime/$name-$display_key.pid" "$@" >> "$runtime/$name.log" 2>&1 &
}
launch sxhkd sxhkd -c "$HOME/.config/sxhkd/sxhkdrc"
launch polybar polybar -c "$HOME/.config/polybar/shapes/config.ini" dragon
if ! pgrep -u "$(id -u)" -x picom >/dev/null; then
    launch picom picom --config "$HOME/.config/picom/picom.conf"
fi
if ! pgrep -u "$(id -u)" -x nm-applet >/dev/null; then
    launch nm-applet nm-applet
fi
if command -v VBoxClient-all >/dev/null && ! pgrep -u "$(id -u)" -x VBoxClient >/dev/null; then
    VBoxClient-all >> "$runtime/virtualbox.log" 2>&1 &
fi
python3 "$DRAGON_ROOT/scripts/wallpaper.py" >> "$runtime/wallpaper.log" 2>&1 &
