#!/usr/bin/env python3
"""Read-only X11 compositing check; reports live state without assuming success."""
import ctypes
import ctypes.util
import os
from pathlib import Path
import subprocess
import sys


def main():
    print('Dragon Ice · comprobación gráfica')
    if not os.environ.get('DISPLAY'):
        print('SIN DISPLAY: ejecuta esta comprobación en el escritorio de Kali, no por SSH.')
        return 2
    processes = subprocess.run(['pgrep','-a','-u',str(os.getuid()),'-x','picom'], capture_output=True, text=True)
    print('Picom:', processes.stdout.strip() or 'no está ejecutándose')
    print('DISPLAY:', os.environ['DISPLAY'])
    library = ctypes.util.find_library('X11')
    if not library:
        print('No se puede cargar libX11 para comprobar el compositor.')
        return 2
    x11 = ctypes.CDLL(library)
    x11.XOpenDisplay.argtypes=[ctypes.c_char_p]
    x11.XOpenDisplay.restype=ctypes.c_void_p
    x11.XDefaultScreen.argtypes=[ctypes.c_void_p]
    x11.XDefaultScreen.restype=ctypes.c_int
    x11.XInternAtom.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int]
    x11.XInternAtom.restype=ctypes.c_ulong
    x11.XGetSelectionOwner.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
    x11.XGetSelectionOwner.restype=ctypes.c_ulong
    x11.XCloseDisplay.argtypes=[ctypes.c_void_p]
    display=x11.XOpenDisplay(None)
    if not display:
        print('No se puede abrir la sesión X11 actual.')
        return 2
    try:
        screen=x11.XDefaultScreen(display)
        atom=x11.XInternAtom(display,f'_NET_WM_CM_S{screen}'.encode(),0)
        owner=x11.XGetSelectionOwner(display,atom)
    finally:
        x11.XCloseDisplay(display)
    if not owner:
        print('FALLO: X11 no registra un compositor activo en esta pantalla.')
        return 1
    print(f'OK: compositor registrado en X11, ventana {owner:#x}.')
    path=Path.home()/'.config/picom/picom.conf'
    content=path.read_text(encoding='utf-8')
    print('Repintado completo:', 'use-damage = false;' in content)
    print('La transparencia visual todavía debe comprobarse cambiando entre ventanas.')
    return 0


if __name__=='__main__':
    sys.exit(main())
