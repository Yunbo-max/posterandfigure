"""Overlay reviewed text/vector shapes on a single-page PDF without rasterizing it.

Dependencies: reportlab, pypdf. JSON coordinates use a top-left reference canvas;
text y is its baseline. This is a compositor, not OCR or automatic layout repair.
"""
import argparse
import io
import json
import math
import os
from pathlib import Path
import tempfile

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor

BUILTIN={'Helvetica','Helvetica-Bold','Helvetica-Oblique','Times-Roman','Times-Bold','Courier'}

def positive(value,label):
    value=float(value)
    if not math.isfinite(value) or value<=0:raise ValueError(f'{label} must be positive and finite')
    return value

def number(value):
    value=float(value)
    if not math.isfinite(value):raise ValueError('Non-finite coordinate')
    return value

def compose(src,spec_path,out,max_mb=20,force=False):
    src,spec_path,out=map(Path,(src,spec_path,out))
    if out.resolve() in (src.resolve(),spec_path.resolve()):raise ValueError('Output must differ from inputs')
    if out.exists() and not force:raise ValueError('Output exists; choose another name or use --force')
    cap=int(positive(max_mb,'max-mb')*1_000_000)
    spec=json.loads(spec_path.read_text())
    rw,rh=[positive(v,'reference dimension') for v in spec['reference_size']]
    reader=PdfReader(src)
    if reader.is_encrypted or len(reader.pages)!=1:raise ValueError('Requires an unencrypted single-page PDF')
    page=reader.pages[0]
    if page.rotation or tuple(page.mediabox)!=tuple(page.cropbox) or tuple(page.mediabox)[:2]!=(0,0) or float(page.get('/UserUnit',1))!=1:
        raise ValueError('Normalize page rotation, boxes and UserUnit before composing')
    pw,ph=float(page.mediabox.width),float(page.mediabox.height)
    for name,path in spec.get('fonts',{}).items():
        if name in BUILTIN:raise ValueError('Custom font names cannot shadow built-in fonts')
        pdfmetrics.registerFont(TTFont(name,str((spec_path.parent/path).resolve())))
    allowed=BUILTIN|set(spec.get('fonts',{}))
    buffer=io.BytesIO();c=Canvas(buffer,pagesize=(pw,ph),pageCompression=1)
    c.translate(0,ph);c.scale(pw/rw,-ph/rh)
    for op in spec['operations']:
        kind=op['type'];x=number(op['x']);y=number(op['y'])
        c.saveState()
        if kind=='rect':
            w=positive(op['w'],'width');h=positive(op['h'],'height')
            radius=number(op.get('radius',0))
            if not 0<=radius<=min(w,h)/2:raise ValueError('Invalid corner radius')
            c.setFillColor(HexColor(op.get('fill','#ffffff')))
            stroke=op.get('stroke')
            if stroke:c.setStrokeColor(HexColor(stroke));c.setLineWidth(positive(op.get('width',1),'stroke width'))
            c.roundRect(x,y,w,h,radius,stroke=int(bool(stroke)),fill=1)
        elif kind=='line':
            c.setStrokeColor(HexColor(op.get('color','#000000')))
            c.setLineWidth(positive(op.get('width',1),'line width'))
            c.line(x,y,number(op['x2']),number(op['y2']))
        elif kind=='text':
            text=op['text'];font=op.get('font','Helvetica');size=positive(op['size'],'font size')
            if not isinstance(text,str) or any(ord(ch)<32 for ch in text):raise ValueError('Each text operation must contain one printable line')
            if font not in allowed:raise ValueError(f'Unknown font {font}')
            if font in BUILTIN:
                text.encode('cp1252')  # Unsupported glyphs need a supplied TrueType font.
            else:
                coverage=pdfmetrics.getFont(font).face.charToGlyph
                if any(ord(ch) not in coverage for ch in text):raise ValueError(f'{font} lacks required glyphs')
            if 'max_width' in op and pdfmetrics.stringWidth(text,font,size)>positive(op['max_width'],'max_width'):
                raise ValueError(f'Text exceeds max_width: {text!r}; reflow explicitly')
            c.setFillColor(HexColor(op.get('color','#0d2a5b')))
            c.translate(x,y);c.scale(1,-1);c.setFont(font,size);c.drawString(0,0,text)
        else:raise ValueError(f'Unsupported operation {kind}')
        c.restoreState()
    c.showPage();c.save();buffer.seek(0)
    writer=PdfWriter();writer.clone_document_from_reader(reader)
    writer.pages[0].merge_page(PdfReader(buffer).pages[0])
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.vector-',suffix='.pdf',dir=out.parent,delete=False) as f:
        tmp=Path(f.name)
    try:
        with tmp.open('wb') as f:writer.write(f)
        size=tmp.stat().st_size
        if size>=cap:raise ValueError(f'Final PDF is {size} bytes; must be below {cap}. Reduce raster background separately.')
        if force:os.replace(tmp,out)
        else:
            # Atomic no-clobber publication, including a concurrent creator.
            os.link(tmp,out);tmp.unlink()
    finally:tmp.unlink(missing_ok=True)
    return {'output':str(out.resolve()),'bytes':size,'page_points':[pw,ph],
            'operations':len(spec['operations']),'raster_reencoded':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--src',type=Path,required=True)
    p.add_argument('--spec',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--max-mb',type=float,default=20)
    p.add_argument('--force',action='store_true')
    args=p.parse_args()
    try:print(json.dumps(compose(args.src,args.spec,args.out,args.max_mb,args.force)))
    except (ValueError,KeyError,TypeError,OSError) as e:p.error(str(e))

if __name__=='__main__':main()
