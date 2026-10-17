"""Integration checks: keep artwork/JPEG bytes, add readable type, fail safely."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class OverlayTest(unittest.TestCase):
    def test_hybrid_pdf_and_failure_boundaries(self):
        script=Path(__file__).with_name('vector_overlay.py')
        self.assertTrue(script.exists(),'Missing reusable vector overlay capability')
        from PIL import Image,ImageDraw
        from reportlab.pdfgen.canvas import Canvas
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            im=Image.new('RGB',(600,800),'#dbeeff')
            draw=ImageDraw.Draw(im);draw.rectangle((50,500,350,580),fill='#331122')
            im.save(p/'art.jpg',quality=90)
            c=Canvas(str(p/'src.pdf'),pagesize=(600,800))
            c.drawImage(str(p/'art.jpg'),0,0,width=600,height=800);c.save()
            spec={'reference_size':[600,800],'operations':[
                {'type':'rect','x':50,'y':500,'w':300,'h':80,'fill':'#ffffff'},
                {'type':'text','x':60,'y':540,'text':'Score: 72.2','size':20,'max_width':270},
                {'type':'line','x':50,'y':580,'x2':350,'y2':580,'color':'#0000ff','width':1}]}
            (p/'spec.json').write_text(json.dumps(spec))
            def run(out='out.pdf',extra=()):
                return subprocess.run([sys.executable,str(script),'--src',str(p/'src.pdf'),
                    '--spec',str(p/'spec.json'),'--out',str(p/out),*extra],capture_output=True,text=True)
            result=run();self.assertEqual(result.returncode,0,result.stderr)
            src=PdfReader(p/'src.pdf');out=PdfReader(p/'out.pdf')
            self.assertEqual(len(out.pages),1)
            self.assertEqual(tuple(out.pages[0].mediabox),(0,0,600,800))
            self.assertIn('Score: 72.2',out.pages[0].extract_text())
            def streams(reader):
                return [obj.get_object().get_data() for obj in reader.pages[0]['/Resources']['/XObject'].values()]
            self.assertEqual(streams(src),streams(out),'Raster image must not be re-encoded')
            for name in ['src','out']:
                subprocess.run(['pdftoppm','-singlefile','-r','72','-png',str(p/(name+'.pdf')),str(p/name)],check=True,capture_output=True)
            original=Image.open(p/'src.png').convert('RGB');final=Image.open(p/'out.png').convert('RGB')
            self.assertEqual(original.crop((0,0,600,400)).tobytes(),final.crop((0,0,600,400)).tobytes())
            self.assertEqual(final.getpixel((80,510)),(255,255,255))
            saved=(p/'out.pdf').read_bytes()
            self.assertNotEqual(run().returncode,0)
            self.assertEqual((p/'out.pdf').read_bytes(),saved)
            self.assertNotEqual(run(extra=['--force','--max-mb','0.001']).returncode,0)
            self.assertEqual((p/'out.pdf').read_bytes(),saved,'Failed cap must not replace output')
            spec['operations'][1]['max_width']=2
            (p/'spec.json').write_text(json.dumps(spec))
            self.assertNotEqual(run('overflow.pdf').returncode,0)
            self.assertFalse((p/'overflow.pdf').exists())
            spec['operations'][1].update(max_width=270,text='中文')
            (p/'spec.json').write_text(json.dumps(spec))
            self.assertNotEqual(run('missing_glyph.pdf').returncode,0)
            self.assertFalse((p/'missing_glyph.pdf').exists())
            # A portable TrueType font shipped with ReportLab should be embedded.
            import reportlab
            vera=Path(reportlab.__file__).parent/'fonts'/'Vera.ttf'
            self.assertTrue(vera.exists(),'ReportLab test font is missing')
            spec['fonts']={'PosterFont':str(vera)}
            spec['operations'][1].update(text='Score: 72.2',font='PosterFont')
            (p/'spec.json').write_text(json.dumps(spec))
            result=run('embedded.pdf');self.assertEqual(result.returncode,0,result.stderr)
            fonts=PdfReader(p/'embedded.pdf').pages[0]['/Resources']['/Font']
            self.assertTrue(any('/FontFile2' in f.get_object().get('/FontDescriptor',{}) for f in fonts.values()))

if __name__=='__main__':unittest.main()
