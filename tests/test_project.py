import ast
import configparser
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import appearance
import metrics
import network


def load_setup():
    spec = importlib.util.spec_from_file_location('dragon_setup', ROOT / 'setup.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_ini(path):
    value = configparser.ConfigParser(interpolation=None)
    value.read(path, encoding='utf-8')
    return value


class SourceTests(unittest.TestCase):
    def test_original_hotkeys(self):
        fixture = json.loads((ROOT / 'tests/keymaps.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256((ROOT / 'config/sxhkd/sxhkdrc').read_bytes()).hexdigest(), fixture['sxhkd_sha256'])
        for filename, word, key in (('config/kitty/kitty.conf', 'map ', 'kitty_maps'), ('.zshrc', 'bindkey ', 'zsh_bindkeys')):
            lines = [x.strip() for x in (ROOT / filename).read_text(encoding='utf-8').splitlines() if x.strip().startswith(word)]
            self.assertEqual(lines, fixture[key])

    def test_python_syntax(self):
        for path in [ROOT / 'setup.py', *(ROOT / 'scripts').glob('*.py')]:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))

    def test_no_forced_resolution(self):
        text = (ROOT / 'templates/bspwmrc').read_text(encoding='utf-8') + (ROOT / 'scripts/appearance.py').read_text(encoding='utf-8')
        self.assertNotIn('--mode', text)
        self.assertNotIn('setvideomodehint', text)

    def test_png_integrity(self):
        images = list((ROOT / 'wallpapers').glob('*.png'))
        self.assertEqual(len(images), 4)
        for path in images:
            with path.open('rb') as stream:
                self.assertEqual(stream.read(8), b'\x89PNG\r\n\x1a\n')
                while True:
                    length = struct.unpack('>I', stream.read(4))[0]
                    kind, data = stream.read(4), stream.read(length)
                    crc = struct.unpack('>I', stream.read(4))[0]
                    self.assertEqual(zlib.crc32(kind + data) & 0xffffffff, crc)
                    if kind == b'IEND':
                        self.assertEqual(stream.read(), b'')
                        break

    def test_font_contains_dragon_and_status_icons(self):
        data = (ROOT / 'fonts/HackNerdFont-Regular.ttf').read_bytes()
        u16 = lambda o: struct.unpack_from('>H', data, o)[0]
        u32 = lambda o: struct.unpack_from('>I', data, o)[0]
        tables = {data[12+i*16:16+i*16].decode('ascii'):u32(20+i*16) for i in range(u16(4))}
        cmap = tables['cmap']
        points = set()
        for i in range(u16(cmap+2)):
            offset = cmap + u32(cmap+8+i*8)
            if u16(offset) == 4:
                count = u16(offset+6)//2
                for j in range(count):
                    end = u16(offset+14+j*2)
                    start = u16(offset+16+count*2+j*2)
                    points.update(range(start, end+1))
            elif u16(offset) == 12:
                for j in range(u32(offset+12)):
                    start, end = struct.unpack_from('>II', data, offset+16+j*12)
                    points.update(range(start, end+1))
        for point in (0xf327,0xf063,0xf062,0xf0a0,0xf2db,0xf233,0xf028,0xf026,0xf0e8,0xf127,0xf012,0xf1eb):
            self.assertIn(point, points, hex(point))


class AppearanceTests(unittest.TestCase):
    def test_transparency_has_one_owner(self):
        with tempfile.TemporaryDirectory() as td:
            config=Path(td)
            for style,percent in (('glass',90),('solid',100),('light',100)):
                appearance.render(config,ROOT,{'style':style,'ui_scale':'100'},(1920,1080))
                kitty=(config/'kitty/dragon-ice.conf').read_text(encoding='utf-8')
                picom=(config/'picom/picom.conf').read_text(encoding='utf-8')
                self.assertIn('background_opacity 1.0',kitty)
                self.assertIn('dynamic_background_opacity no',kitty)
                self.assertIn(f'"{percent}:class_g = \'kitty\'"',picom)
                self.assertIn('use-damage = false;',picom)
                self.assertIn('active-opacity = 1.0;',picom)
                self.assertIn('inactive-opacity = 1.0;',picom)

    def test_all_styles_and_scales(self):
        with tempfile.TemporaryDirectory() as td:
            config = Path(td)
            for style in appearance.STYLES:
                for scale in appearance.SCALES:
                    result = appearance.render(config, ROOT, {'style':style,'ui_scale':scale}, (3840,2160))
                    ini = read_ini(config / 'polybar/shapes/config.ini')
                    module = ini['module/bspwm']
                    for i in range(8):
                        self.assertEqual(module[f'ws-icon-{i}'].split(';')[1], chr(0xf327))
                    self.assertEqual(module['label-focused'], '%{T2}%icon%%{T-}')
                    self.assertEqual(ini['bar/dragon']['modules-right'], 'status pulseaudio link date')
                    self.assertGreater(result['gap'], 0)
                    picom = (config / 'picom/picom.conf').read_text(encoding='utf-8')
                    if style == 'light':
                        self.assertIn('shadow = false', picom)
                        self.assertIn('corner-radius = 0', picom)
                    else:
                        self.assertIn('shadow = true', picom)
            result = appearance.render(config, ROOT, {'style':'glass','ui_scale':'auto'}, (3840,2160))
            self.assertEqual(result['scale'], 2.0)
            self.assertEqual(read_ini(config / 'polybar/shapes/config.ini')['bar/dragon']['font-1'], 'Hack Nerd Font Propo:size=36;6')
            result = appearance.render(config, ROOT, {'style':'glass','ui_scale':'auto'}, (1280,800))
            self.assertEqual(result['scale'], 1.0)
            self.assertEqual(read_ini(config / 'polybar/shapes/config.ini')['module/bspwm']['label-empty-padding'], '1')

    def test_invalid_preferences(self):
        with self.assertRaises(ValueError):
            appearance.factor('900', (3840,2160))
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                appearance.render(Path(td), ROOT, {'style':'invalid'}, (1920,1080))


class MetricsTests(unittest.TestCase):
    def test_cpu_memory_and_traffic(self):
        self.assertEqual(metrics.cpu_times('cpu  10 0 20 70 0 0 0 0 99 0\n'), (100,70))
        self.assertEqual(metrics.cpu_percent((100,70),(200,120)), 50)
        self.assertEqual(metrics.cpu_percent((100,70),(100,70)), 0)
        self.assertEqual(metrics.memory_percent('MemTotal: 1000 kB\nMemAvailable: 700 kB\n'), 30)
        self.assertEqual(metrics.net_bytes('eth0: 1024 0 0 0 0 0 0 0 2048 0 0 0 0 0 0 0', 'eth0'), (1024,2048))
        self.assertEqual(metrics.rates((100,200),(1124,2248),2), (512,1024))
        self.assertEqual(metrics.rates((100,200),(0,0),2), (0,0))
        self.assertEqual(metrics.human_rate(1024), '1 KiB/s')
        self.assertIn(chr(0xf127), metrics.link_label(''))

    def test_vpn_full_tunnel_and_disconnect(self):
        links = [{'ifname':'eth0','flags':['UP']},{'ifname':'tun0','flags':['UP'],'linkinfo':{'info_kind':'tun'}}]
        addresses = [{'ifname':name,'addr_info':[{'family':'inet','scope':'global','local':ip}]} for name,ip in [('eth0','10.0.2.15'),('tun0','10.8.0.2')]]
        routes = [{'dst':'default','dev':'tun0','metric':0},{'dst':'default','dev':'eth0','metric':100}]
        self.assertEqual(network.choose(links,addresses,routes,{}), ('10.0.2.15','10.8.0.2'))
        self.assertEqual(network.choose(links[:1],addresses,routes,{}), ('10.0.2.15','desconectada'))
        self.assertEqual(network.choose([],[],[],{}), ('sin red','desconectada'))


class InstallTests(unittest.TestCase):
    def test_fresh_install_restore_and_rollback(self):
        setup = load_setup()
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            setup.HOME = home
            setup.STATE = home / '.local/state/kali-dragon-ice'
            vendor = home / 'downloads'
            theme = vendor / 'oh-my-zsh/custom/themes/powerlevel10k'
            theme.mkdir(parents=True)
            (vendor / 'oh-my-zsh/oh-my-zsh.sh').write_text('# fixture')
            (theme / 'powerlevel10k.zsh-theme').write_text('# fixture')
            previous = home / '.config/bspwm/bspwmrc'
            previous.parent.mkdir(parents=True)
            previous.write_text('old desktop')
            (home / '.zshrc').write_text('old shell')
            unrelated = home / '.config/unrelated/note'
            unrelated.parent.mkdir()
            unrelated.write_text('keep')
            with patch.object(appearance, 'display_size', return_value=(3840,2160)):
                setup.install(vendor)
            active = read_ini(home / '.config/polybar/shapes/config.ini')
            self.assertIn('36;', active['bar/dragon']['font-1'])
            self.assertTrue((home / '.local/share/kali-dragon-ice/templates/polybar.ini').is_file())
            self.assertEqual((home / '.config/sxhkd/sxhkdrc').read_bytes(), (ROOT / 'config/sxhkd/sxhkdrc').read_bytes())
            self.assertEqual(active['module/bspwm']['ws-icon-0'], 'I;' + chr(0xf327))
            setup.restore()
            self.assertEqual(previous.read_text(), 'old desktop')
            self.assertEqual((home / '.zshrc').read_text(), 'old shell')
            self.assertEqual(unrelated.read_text(), 'keep')
            self.assertFalse((home / '.local/share/kali-dragon-ice').exists())
            copytree = setup.shutil.copytree
            def fail(src,dst,*args,**kwargs):
                if Path(dst) == home / '.config/kitty':
                    raise OSError('simulated failure')
                return copytree(src,dst,*args,**kwargs)
            with patch.object(setup.shutil, 'copytree', fail):
                with self.assertRaises(OSError):
                    setup.install(vendor)
            self.assertEqual(previous.read_text(), 'old desktop')
            self.assertEqual((home / '.zshrc').read_text(), 'old shell')
            self.assertEqual(unrelated.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
