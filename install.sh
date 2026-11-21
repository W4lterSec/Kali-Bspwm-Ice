#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
style=glass
scale=auto
while (( $# )); do
    case "$1" in
        --style) style=${2:?Falta el estilo}; shift 2 ;;
        --scale) scale=${2:?Falta la escala}; shift 2 ;;
        *) echo 'Uso: bash install.sh [--style glass|solid|light] [--scale auto|100|125|150|200]' >&2; exit 1 ;;
    esac
done
case "$style" in glass|solid|light) ;; *) echo 'Estilo no válido.' >&2; exit 1 ;; esac
case "$scale" in auto|100|125|150|200) ;; *) echo 'Escala no válida.' >&2; exit 1 ;; esac
if (( EUID == 0 )); then
    echo 'Ejecuta bash install.sh como tu usuario normal, sin sudo.' >&2
    exit 1
fi
. /etc/os-release
[[ ${ID:-} == kali ]] || { echo 'Este paquete está preparado para Kali Linux.' >&2; exit 1; }
[[ ${XDG_CONFIG_HOME:-$HOME/.config} == "$HOME/.config" ]] || {
    echo 'Los atajos originales requieren la ruta estándar ~/.config.' >&2; exit 1;
}
stage=$(mktemp -d)
trap 'rm -rf -- "$stage"' EXIT
record="$HOME/.local/state/kali-dragon-ice/apt-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$record"
dpkg-query -W -f '${binary:Package}\n' | sort -u > "$record/before.txt"
packages=(bspwm sxhkd polybar picom kitty rofi feh wmname xclip ranger i3lock-fancy
    scrot scrub imagemagick cmatrix htop fastfetch procps tty-clock fzf lsd bat
    pamixer flameshot thunar zsh zsh-autosuggestions zsh-syntax-highlighting
    fonts-dejavu-core python3 iproute2 util-linux x11-xserver-utils x11-utils
    xdg-utils network-manager-applet nm-connection-editor git ca-certificates
    firefox-esr burpsuite pavucontrol fontconfig)
if [[ $(systemd-detect-virt --vm 2>/dev/null) == oracle ]]; then
    packages+=(virtualbox-guest-x11)
fi
printf '%s\n' "${packages[@]}" > "$record/requested.txt"
sudo apt-get update
sudo apt-get install -y "${packages[@]}"
dpkg-query -W -f '${binary:Package}\n' | sort -u > "$record/after.txt"
comm -13 "$record/before.txt" "$record/after.txt" > "$record/added.txt"
export GIT_TERMINAL_PROMPT=0
git clone --depth 1 https://github.com/ohmyzsh/ohmyzsh.git "$stage/oh-my-zsh"
git clone --depth 1 https://github.com/romkatv/powerlevel10k.git "$stage/oh-my-zsh/custom/themes/powerlevel10k"
python3 setup.py install --vendor "$stage" --packages "$record" --style "$style" --scale "$scale"
fc-cache -f "$HOME/.local/share/fonts/kali-dragon-ice"
printf '\nInstalación terminada. Cierra sesión y selecciona bspwm.\n'
printf 'Los escritorios ya muestran iconos; no es necesario aplicar el parche aparte.\n'
printf 'Atajos originales: Super+Enter terminal; Super+D aplicaciones; Super+flechas navegar.\n'
