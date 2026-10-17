"""A0/A1 poster PDF exports. Dependencies: Pillow; Poppler for verification."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zlib
from PIL import Image, ImageOps

PAPERS={'A0':(841,1189),'A1':(594,841)}

def pdf(path,width,height,icc,paper,encoding,predictor,write_image):
    """Write one centred image at its original aspect ratio on a white page."""
    pw,ph=(x*72/25.4 for x in PAPERS[paper])
    scale=min(pw/width,ph/height)
    dw,dh=width*scale,height*scale
    positions={}
    with path.open('wb') as f:
        def put(data): f.write(data.encode('ascii') if isinstance(data,str) else data)
        def obj(n,data):
            positions[n]=f.tell()
            put(f'{n} 0 obj\n');put(data);put('\nendobj\n')
        put(b'%PDF-1.7\n%\xe2\xe3\xcf\xd3\n')
        obj(1,'<< /Type /Catalog /Pages 2 0 R >>')
        obj(2,'<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
        obj(3,f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {pw:.8f} {ph:.8f}] /Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>')
        content=f'q\n{dw:.8f} 0 0 {dh:.8f} {(pw-dw)/2:.8f} {(ph-dh)/2:.8f} cm\n/Im0 Do\nQ\n'.encode()
        obj(4,f'<< /Length {len(content)} >>\nstream\n'.encode()+content+b'endstream')
        positions[5]=f.tell()
        color='[/ICCBased 7 0 R]' if icc else '/DeviceRGB'
        params=f'/DecodeParms << /Predictor {predictor} /Colors 3 /BitsPerComponent 8 /Columns {width} >>' if encoding=='FlateDecode' else ''
        put(f'5 0 obj\n<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /BitsPerComponent 8 /ColorSpace {color} /Interpolate false /Filter /{encoding} {params} /Length 6 0 R >>\nstream\n')
        start=f.tell()
        write_image(f)
        length=f.tell()-start
        put('\nendstream\nendobj\n')
        obj(6,str(length))
        obj(7,f'<< /N 3 /Alternate /DeviceRGB /Length {len(icc)} >>\nstream\n'.encode()+icc+b'\nendstream')
        obj(8,f'<< /Title (Poster - {paper}) /Creator (poster-print-pipeline) >>')
        xref=f.tell()
        put('xref\n0 9\n0000000000 65535 f \n')
        for n in range(1,9):put(f'{positions[n]:010d} 00000 n \n')
        put(f'trailer\n<< /Size 9 /Root 1 0 R /Info 8 0 R >>\nstartxref\n{xref}\n%%EOF\n')
    return {'pixels':[width,height],'effective_ppi':round(72/scale,3),'paper':paper}

def lossless(args,tmp):
    # Header inspection only: never decode the complete gigapixel image.
    with Image.open(args.src) as im:
        if im.format!='TIFF':raise ValueError('lossless mode requires an RGB Deflate TIFF')
        t=im.tag_v2
        valid=(t.get(259) in (8,32946) and t.get(262)==2 and t.get(277)==3
               and tuple(t.get(258,()))==(8,8,8) and t.get(284,1)==1
               and t.get(317,1) in (1,2) and t.get(274,1)==1 and 273 in t and 279 in t)
        if not valid:raise ValueError('Need untiled, top-left, 8-bit RGB Deflate TIFF with predictor 1 or 2; convert on a machine with sufficient RAM')
        width,height=im.size
        offsets,counts=tuple(t[273]),tuple(t[279])
        rows_per_strip=t[278]
        if rows_per_strip*width*3>16*1024*1024 or max(counts)>16*1024*1024:
            raise ValueError('TIFF strips exceed the 16 MiB streaming buffer limit; re-save using smaller strips on a sufficiently provisioned machine')
        predictor=t.get(317,1)
        icc=im.info.get('icc_profile',b'')
    digest=hashlib.sha256()
    def stream(out):
        compressor=zlib.compressobj(level=3)
        rows=0
        with args.src.open('rb') as source:
            for index,(offset,count) in enumerate(zip(offsets,counts)):
                source.seek(offset)
                data=zlib.decompress(source.read(count))
                n=min(rows_per_strip,height-rows)
                if len(data)!=n*width*3:raise ValueError('Unexpected TIFF strip size')
                digest.update(data)
                out.write(compressor.compress(data))
                rows+=n
                if (index+1)%10000==0:print(f'Encoded {rows}/{height} rows',flush=True)
        if rows!=height:raise ValueError('Incomplete TIFF strip coverage')
        out.write(compressor.flush())
    result=pdf(tmp,width,height,icc,args.paper,'FlateDecode',predictor,stream)
    return dict(result,lossless=True,predictor_bytes_sha256=digest.hexdigest())

def upload(args,tmp):
    if args.max_mb<=0 or args.dpi<=0 or args.min_dpi<=0:raise ValueError('Positive limits required')
    cap=int(args.max_mb*1_000_000)
    with Image.open(args.src) as original:
        if original.width*original.height>args.max_input_pixels:
            raise ValueError('Source exceeds safe decode pixel limit. Use the 300 DPI master, or resize on a sufficiently provisioned machine; do not decode a gigapixel TIFF on a small laptop')
        if original.mode not in ('RGB','RGBA','P','L','LA'):
            raise ValueError('Convert this color mode with its ICC profile before export')
        icc=original.info.get('icc_profile',b'')
        oriented=ImageOps.exif_transpose(original)
        if oriented.mode in ('RGBA','LA') or 'transparency' in oriented.info:
            rgba=oriented.convert('RGBA')
            image=Image.new('RGB',rgba.size,'white')
            image.paste(rgba,mask=rgba.getchannel('A'))
        else:image=oriented.convert('RGB')
        # Grayscale profiles cannot be attached to the resulting RGB PDF.
        if original.mode in ('L','LA') and icc:
            raise ValueError('Convert the grayscale ICC profile to RGB before export')
    minimum=min(args.min_dpi,args.dpi)
    dpis=sorted({args.dpi,max(minimum,round(args.dpi*.8)),max(minimum,round(args.dpi*2/3)),minimum},reverse=True)
    with tempfile.TemporaryDirectory(prefix='poster-jpeg-') as folder:
        jpg=Path(folder)/'candidate.jpg'
        previous_size=None
        for dpi in dpis:
            bounds=tuple(round(mm*dpi/25.4) for mm in PAPERS[args.paper])
            candidate=image.copy()
            candidate.thumbnail(bounds,Image.Resampling.LANCZOS)
            if candidate.size==previous_size:continue
            previous_size=candidate.size
            for quality in (94,92,90,88,86,84,82,80):
                try:
                    candidate.save(jpg,'JPEG',quality=quality,subsampling=0,optimize=True,icc_profile=icc)
                except OSError as exc:
                    # Pillow's optimized encoder buffer estimate can be too
                    # small for high-entropy 4:4:4 images. Streaming encoding
                    # retains quality and avoids allocating a full RGB buffer.
                    if 'broken data stream when writing image file' not in str(exc):raise
                    candidate.save(jpg,'JPEG',quality=quality,subsampling=0,optimize=False,icc_profile=icc)
                size=jpg.stat().st_size
                print(f'{candidate.width}x{candidate.height}, JPEG Q{quality}: {size} bytes',flush=True)
                if size+len(icc)+8192>cap*.975:continue
                def stream(out):
                    with jpg.open('rb') as source:
                        for data in iter(lambda:source.read(1024*1024),b''):out.write(data)
                result=pdf(tmp,*candidate.size,icc,args.paper,'DCTDecode',None,stream)
                if tmp.stat().st_size<cap:
                    return dict(result,lossless=False,jpeg_quality=quality,max_bytes=cap)
    raise ValueError('Cannot meet size limit within allowed quality/DPI range. Report this instead of silently producing an oversized or unreadable PDF')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='mode',required=True)
    for mode in ('lossless','upload'):
        p=sub.add_parser(mode)
        p.add_argument('--src',type=Path,required=True)
        p.add_argument('--out',type=Path,required=True)
        p.add_argument('--paper',choices=PAPERS,default='A0')
        p.add_argument('--force',action='store_true',help='explicitly replace an existing output')
        if mode=='upload':
            p.add_argument('--max-mb',type=float,default=20)
            p.add_argument('--dpi',type=int,default=300)
            p.add_argument('--min-dpi',type=int,default=150)
            p.add_argument('--max-input-pixels',type=int,default=200_000_000)
    args=ap.parse_args()
    Image.MAX_IMAGE_PIXELS=None
    if args.src.resolve()==args.out.resolve():ap.error('Source and output must differ')
    if args.out.exists() and not args.force:ap.error('Output exists; choose another name or explicitly use --force')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.poster-',suffix='.pdf',dir=args.out.parent,delete=False) as f:
        tmp=Path(f.name)
    try:
        result=(lossless if args.mode=='lossless' else upload)(args,tmp)
        result.update(bytes=tmp.stat().st_size,output=str(args.out.resolve()))
        tmp.replace(args.out)
        print(json.dumps(result),flush=True)
    except (ValueError,OSError,KeyError,zlib.error) as exc:
        ap.error(str(exc))
    finally:
        tmp.unlink(missing_ok=True)

if __name__=='__main__':main()
