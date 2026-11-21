#!/usr/bin/env python3
"""Render visual settings without changing resolution, workspace names or keys."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
STYLES = {
    'glass': {'opacity': 0.90, 'corner': 20, 'shadow': True, 'gap': 24},
    'solid': {'opacity': 1.0, 'corner': 14, 'shadow': True, 'gap': 20},
    'light': {'opacity': 1.0, 'corner': 0, 'shadow': False, 'gap': 12},
}
SCALES = ('auto', '100', '125', '150', '200')


def display_size():
    try:
        output = subprocess.check_output(['xrandr', '--current'], text=True, timeout=4, stderr=subprocess.DEVNULL)
        primary = re.search(r'^\S+ connected primary (\d+)x(\d+)\+', output, re.M)
        current = primary or re.search(r'current (\d+) x (\d+)', output)
        if current:
            return int(current[1]), int(current[2])
    except (OSError, subprocess.SubprocessError):
        pass
    return 1920, 1080


def factor(value, dimensions):
    if str(value) not in SCALES:
        raise ValueError('Escala válida: auto, 100, 125, 150 o 200.')
    if str(value) != 'auto':
        return int(value) / 100
    width, height = dimensions
    return 2.0 if width >= 3000 and height >= 1600 else 1.25 if width >= 2400 and height >= 1300 else 1.0


def render(config_root, data_root, settings, dimensions=None):
    style_name = settings.get('style', 'glass')
    if style_name not in STYLES:
        raise ValueError('Estilo válido: glass, solid o light.')
    style = STYLES[style_name]
    dimensions = dimensions or display_size()
    scale = factor(settings.get('ui_scale', 'auto'), dimensions)
    compact = dimensions[0] / scale < 1700
    px = lambda number: max(1, round(number * scale))
    dragon = chr(0xf327)
    entries = [f'ws-icon-{i} = {name};{dragon}' for i, name in enumerate('I II III IV V VI VII VIII'.split())]
    entries.append(f'ws-icon-default = {dragon}')
    tokens = {
        'BARHEIGHT': px(48), 'BARMARGIN': px(16), 'BARMARGIN2': px(32), 'BARTOP': px(12),
        'BARRADIUS': px(20), 'BARBORDER': 0, 'TEXTFONT': px(11 if compact else 13),
        'DRAGONFONT': px(18), 'STATUSFONT': px(11), 'FONTBASE': px(3), 'ICONBASE': px(3),
        'WSPADDING': 1, 'WORKSPACEICONS': '\n'.join(entries),
        'VOLUMEICON': '%{T3}' + chr(0xf028) + '%{T-}',
        'MUTEICON': '%{T3}' + chr(0xf026) + '%{T-}',
        'COMPACT': '--compact' if compact else '',
        'TERMFONT': px(15), 'TERMPADDING': px(18), 'OPACITY': 1.0,
        'WINDOWOPACITY': round(style['opacity'] * 100),
        'SHADOW': str(style['shadow']).lower(), 'SHADOWRADIUS': px(22), 'SHADOWOFFSET': px(12),
        'CORNERRADIUS': round(style['corner'] * scale), 'BORDER': px(2),
        'ROFIFONT': px(15), 'ROFIWIDTH': min(px(620), dimensions[0] - px(60)),
        'ROFIPADDING': px(12), 'ROFISPACING': px(8), 'ELEMENTRADIUS': px(8),
    }
    destinations = {
        'polybar.ini': 'polybar/shapes/config.ini', 'kitty.conf': 'kitty/dragon-ice.conf',
        'picom.conf': 'picom/picom.conf', 'launcher.rasi': 'polybar/shapes/scripts/rofi/launcher.rasi',
    }
    for template, destination in destinations.items():
        text = (data_root / 'templates' / template).read_text(encoding='utf-8')
        for key, value in tokens.items():
            text = text.replace('@' + key + '@', str(value))
        if re.search(r'@[A-Z][A-Z0-9_]*@', text):
            raise RuntimeError(f'Plantilla sin completar: {template}')
        path = config_root / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8', newline='\n')
    geometry = config_root / 'kali-dragon-ice/geometry.sh'
    geometry.parent.mkdir(parents=True, exist_ok=True)
    geometry.write_text(f'bspc config window_gap {px(style["gap"])}\nbspc config border_width {px(2)}\n', encoding='utf-8')
    return {'style': style_name, 'scale': scale, 'dimensions': dimensions, 'gap': px(style['gap']), 'border': px(2)}


def reload_owned_services(root):
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', str(HOME / '.cache'))) / 'kali-dragon-ice'
    display = ''.join(c if c.isalnum() else '_' for c in os.environ.get('DISPLAY', ''))
    for name, marker in (('polybar', '/polybar/shapes/config.ini'), ('picom', '/picom/picom.conf')):
        pid_file = runtime / f'{name}-{display}.pid'
        try:
            pid = int(pid_file.read_text())
            cmdline = Path(f'/proc/{pid}/cmdline').read_bytes().decode(errors='replace')
            if marker in cmdline and Path(f'/proc/{pid}').stat().st_uid == os.getuid():
                os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
    time.sleep(0.25)
    subprocess.run(['bash', str(root / 'scripts/session.sh')], check=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--style', choices=tuple(STYLES))
    parser.add_argument('--scale', choices=SCALES)
    parser.add_argument('--render-only', action='store_true')
    args = parser.parse_args()
    settings_file = HOME / '.config/kali-dragon-ice/settings.json'
    settings = json.loads(settings_file.read_text(encoding='utf-8'))
    if args.style:
        settings['style'] = args.style
    if args.scale:
        settings['ui_scale'] = args.scale
    result = render(HOME / '.config', ROOT, settings)
    settings_file.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
    print(f'Dragon Ice: {result["style"]}, escala {round(result["scale"] * 100)} %.')
    if not args.render_only and os.environ.get('DISPLAY'):
        subprocess.run(['bspc', 'config', 'window_gap', str(result['gap'])], check=False)
        subprocess.run(['bspc', 'config', 'border_width', str(result['border'])], check=False)
        reload_owned_services(ROOT)
        print('Abre una terminal nueva para cargar el tamaño y la opacidad de Kitty.')


if __name__ == '__main__':
    main()
