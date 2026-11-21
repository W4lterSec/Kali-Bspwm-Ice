#!/usr/bin/env python3
"""Rotate real image files every ten minutes while this X display exists."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    if not os.environ.get('DISPLAY'):
        return
    root = Path(__file__).resolve().parent.parent
    cache = Path(os.environ.get('XDG_RUNTIME_DIR', os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache')))) / 'kali-dragon-ice'
    cache.mkdir(parents=True, exist_ok=True)
    display = ''.join(c if c.isalnum() else '_' for c in os.environ['DISPLAY'])
    with (cache / f'wallpaper-{display}.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        previous = None
        while True:
            if subprocess.run(['xset', 'q'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
                return
            images = sorted(p for p in (root / 'wallpapers').iterdir() if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} and p.is_file())
            if images:
                index = (images.index(previous) + 1) % len(images) if previous in images else 0
                image = images[index]
                result = subprocess.run(['feh', '--no-fehbg', '--bg-fill', str(image)], check=False)
                if result.returncode == 0:
                    previous = image
            config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'kali-dragon-ice/settings.json'
            try:
                interval = max(10, int(json.loads(config.read_text()).get('wallpaper_interval', 600)))
            except (OSError, ValueError, TypeError):
                interval = 600
            # Poll the X session every 5 seconds, exit promptly at logout.
            deadline = time.monotonic() + interval
            while time.monotonic() < deadline:
                time.sleep(min(5, max(0, deadline - time.monotonic())))
                if subprocess.run(['xset', 'q'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
                    return


if __name__ == '__main__':
    main()
