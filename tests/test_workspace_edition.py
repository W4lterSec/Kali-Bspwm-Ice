import configparser
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import appearance


class EightWorkspaceTests(unittest.TestCase):
    def test_eight_icons_with_symmetric_spacing(self):
        with tempfile.TemporaryDirectory() as td:
            config=Path(td)
            appearance.render(config,ROOT,{'style':'glass','ui_scale':'auto'},(3840,2160))
            ini=configparser.ConfigParser(interpolation=None)
            ini.read(config/'polybar/shapes/config.ini',encoding='utf-8')
            module=ini['module/bspwm']
            indices=sorted(key for key in module if key.startswith('ws-icon-') and key!='ws-icon-default')
            self.assertEqual(indices,[f'ws-icon-{i}' for i in range(8)])
            self.assertEqual(module['ws-icon-7'],'VIII;'+chr(0xf327))
            for state in ('focused','occupied','empty','urgent'):
                self.assertEqual(module[f'label-{state}-padding'],'1')
            self.assertIn('Hack Nerd Font Propo',ini['bar/dragon']['font-1'])
            self.assertIn('-d I II III IV V VI VII VIII\n',(ROOT/'templates/bspwmrc').read_text(encoding='utf-8'))
            self.assertNotIn('VIII IX X',(ROOT/'templates/bspwmrc').read_text(encoding='utf-8'))

    def test_dragon_outline_fits_its_allocated_width(self):
        data=(ROOT/'fonts/HackNerdFontPropo-Regular.ttf').read_bytes()
        u16=lambda o:struct.unpack_from('>H',data,o)[0]
        s16=lambda o:struct.unpack_from('>h',data,o)[0]
        u32=lambda o:struct.unpack_from('>I',data,o)[0]
        table={data[12+i*16:16+i*16].decode():u32(20+i*16) for i in range(u16(4))}
        cmap=table['cmap'];point=0xf327;glyph=None
        for i in range(u16(cmap+2)):
            offset=cmap+u32(cmap+8+i*8)
            if u16(offset)==12:
                for j in range(u32(offset+12)):
                    start,end,index=struct.unpack_from('>III',data,offset+16+j*12)
                    if start<=point<=end:glyph=index+point-start
            elif u16(offset)==4:
                count=u16(offset+6)//2
                for j in range(count):
                    end=u16(offset+14+j*2);start=u16(offset+16+count*2+j*2)
                    if start<=point<=end:
                        delta=s16(offset+16+count*4+j*2);pos=offset+16+count*6+j*2;distance=u16(pos)
                        glyph=(u16(pos+distance+2*(point-start))+delta)&65535 if distance else (point+delta)&65535
        self.assertIsNotNone(glyph)
        count=u16(table['hhea']+34)
        advance=u16(table['hmtx']+min(glyph,count-1)*4)
        offset=u32(table['loca']+4*glyph) if s16(table['head']+50) else u16(table['loca']+2*glyph)*2
        left,bottom,right,top=struct.unpack_from('>hhhh',data,table['glyf']+offset+2)
        self.assertLessEqual(right-left,advance+8)
        self.assertLessEqual(abs((left+right)/2-advance/2),8)


if __name__=='__main__':unittest.main()
