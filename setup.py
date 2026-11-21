#!/usr/bin/env python3
"""Install supplied configs with an undo journal; do not execute upstream setup."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

SOURCE = Path(__file__).resolve().parent
HOME = Path.home()
STATE = HOME / '.local/state/kali-dragon-ice'


def exists(path):
    return path.exists() or path.is_symlink()


def stamp():
    return datetime.now().strftime('%Y%m%d-%H%M%S-%f')


def save_manifest(folder, manifest):
    temporary = folder / 'manifest.tmp'
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(folder / 'manifest.json')


def install(vendor, packages=None, style='glass', scale='auto'):
    if not (vendor / 'oh-my-zsh/oh-my-zsh.sh').is_file():
        raise RuntimeError('Falta la descarga de Oh My Zsh.')
    if not (vendor / 'oh-my-zsh/custom/themes/powerlevel10k/powerlevel10k.zsh-theme').is_file():
        raise RuntimeError('Falta la descarga de Powerlevel10k.')
    STATE.mkdir(parents=True, exist_ok=True)
    folder = STATE / 'backups' / stamp()
    folder.mkdir(parents=True)
    staging = folder / 'staging'
    staging.mkdir()
    data = staging / 'data'
    data.mkdir()
    for name in ('scripts', 'wallpapers', 'templates'):
        shutil.copytree(SOURCE / name, data / name)
    shutil.copytree(vendor, data / 'vendor', ignore=shutil.ignore_patterns('.git'))
    if packages:
        shutil.copytree(packages, data / 'package-record')
    config = staging / 'config'
    shutil.copytree(SOURCE / 'config', config)
    settings_file = config / 'kali-dragon-ice/settings.json'
    settings = json.loads(settings_file.read_text(encoding='utf-8'))
    settings.update(style=style, ui_scale=scale)
    settings_file.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    extra = config / 'polybar/shapes/scripts'
    for script in (SOURCE / 'original-scripts').glob('*.sh'):
        shutil.copy2(script, extra / script.name)
    (extra / 'target').touch()
    items = [(config / name, HOME / '.config' / name) for name in ('bspwm', 'sxhkd', 'kitty', 'picom', 'polybar', 'kali-dragon-ice')]
    items += [(data, HOME / '.local/share/kali-dragon-ice'),
              (SOURCE / 'fonts', HOME / '.local/share/fonts/kali-dragon-ice'),
              (SOURCE / '.zshrc', HOME / '.zshrc'),
              (SOURCE / '.p10k.zsh', HOME / '.p10k.zsh'),
              (SOURCE / 'original-scripts/whichSystem.py', HOME / '.local/bin/whichSystem.py')]
    for _, target in items:
        if target == HOME / '.local/share/kali-dragon-ice' and target.is_symlink():
            raise RuntimeError('El directorio de datos debe ser una carpeta real.')
        if target in (HOME / '.zshrc', HOME / '.p10k.zsh') and target.is_dir():
            raise RuntimeError(f'Se esperaba un archivo: {target}')
    manifest = {'complete': False, 'restored': False, 'files': [], 'packages': str(packages or '')}
    save_manifest(folder, manifest)
    (STATE / 'latest').write_text(str(folder), encoding='utf-8')
    try:
        for i, (source, target) in enumerate(items):
            target.parent.mkdir(parents=True, exist_ok=True)
            old = folder / str(i)
            entry = {'target': str(target), 'old': str(old), 'existed': exists(target), 'installed': False}
            manifest['files'].append(entry)
            save_manifest(folder, manifest)
            if entry['existed']:
                shutil.move(str(target), str(old))
            entry['installed'] = True
            save_manifest(folder, manifest)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        for directory in (HOME / '.config/bspwm', HOME / '.config/polybar', HOME / '.local/share/kali-dragon-ice/scripts'):
            for path in directory.rglob('*'):
                if path.is_file() and (path.suffix in ('.py', '.sh') or not path.suffix):
                    path.chmod(0o755)
        (HOME / '.local/bin/whichSystem.py').chmod(0o755)
        installed = HOME / '.config/sxhkd/sxhkdrc'
        original = SOURCE / 'config/sxhkd/sxhkdrc'
        assert hashlib.sha256(installed.read_bytes()).digest() == hashlib.sha256(original.read_bytes()).digest()
        sys.path.insert(0, str(SOURCE / 'scripts'))
        from appearance import render
        render(HOME / '.config', HOME / '.local/share/kali-dragon-ice', settings)
        manifest['complete'] = True
        save_manifest(folder, manifest)
    except Exception:
        restore(folder)
        raise
    print(f'Instalado. Copia de seguridad: {folder}')
    print('Atajos sxhkd: archivo original verificado por SHA-256.')


def restore(folder=None):
    if folder is None:
        pointer = STATE / 'latest'
        if not pointer.exists():
            raise RuntimeError('No hay una instalación de Dragon Ice que restaurar.')
        folder = Path(pointer.read_text(encoding='utf-8').strip())
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('restored'):
        raise RuntimeError('La configuración anterior ya fue restaurada.')
    removed = STATE / 'removed' / stamp()
    removed.mkdir(parents=True)
    for i, entry in enumerate(reversed(manifest['files'])):
        target, old = Path(entry['target']), Path(entry['old'])
        if entry['installed'] and exists(target):
            shutil.move(str(target), str(removed / str(i)))
        if entry['existed'] and exists(old):
            shutil.move(str(old), str(target))
    manifest['restored'] = True
    save_manifest(folder, manifest)
    print(f'Configuración anterior restaurada. Archivos de Dragon Ice conservados en {removed}')
    print('Los paquetes de APT permanecen instalados. Vuelve a iniciar sesión en Xfce.')


if __name__ == '__main__':
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        sys.exit('Ejecuta como usuario normal, sin sudo.')
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('install', 'restore'))
    parser.add_argument('--vendor', type=Path)
    parser.add_argument('--packages', type=Path)
    parser.add_argument('--style', choices=('glass', 'solid', 'light'), default='glass')
    parser.add_argument('--scale', choices=('auto', '100', '125', '150', '200'), default='auto')
    args = parser.parse_args()
    if args.action == 'install':
        if args.vendor is None:
            parser.error('Usa bash install.sh para preparar las dependencias.')
        install(args.vendor, args.packages, args.style, args.scale)
    else:
        restore()
