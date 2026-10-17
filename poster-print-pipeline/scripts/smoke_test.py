"""Offline integration checks; Pillow + Poppler. No GPU/model download."""
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from PIL import Image

script=Path(__file__).with_name('poster_pdf.py')
assert script.is_file(), 'Missing reusable poster PDF CLI'

def run(*args,ok=True):
    p=subprocess.run([sys.executable,str(script),*map(str,args)],capture_output=True,text=True)
    assert (p.returncode==0)==ok,(p.stdout,p.stderr)
    return p

with tempfile.TemporaryDirectory(prefix='poster-skill-check-') as folder:
    root=Path(folder)
    pixels=random.Random(17).randbytes(64*90*3)
    im=Image.frombytes('RGB',(64,90),pixels)
    source=root/'source.tif'
    im.save(source,compression='tiff_adobe_deflate',tiffinfo={317:2})
    lossless=root/'lossless.pdf'
    run('lossless','--src',source,'--out',lossless,'--paper','A0')
    info=subprocess.check_output(['pdfinfo',str(lossless)],text=True)
    assert '(A0)' in info and 'Pages:           1' in info, info
    subprocess.run(['pdfimages','-png',str(lossless),str(root/'extract')],check=True)
    with Image.open(root/'extract-000.png') as actual:
        assert actual.mode=='RGB' and actual.size==im.size
        assert actual.tobytes()==pixels, 'Lossless image pixels changed'
    print('PASS: lossless PDF, A0 geometry, independent exact pixel extraction')
    before=lossless.read_bytes()
    run('lossless','--src',source,'--out',lossless,ok=False)
    assert lossless.read_bytes()==before
    print('PASS: existing output preserved')
    unsupported=root/'unsupported.tif'
    im.save(unsupported,compression='tiff_lzw')
    run('lossless','--src',unsupported,'--out',root/'bad.pdf',ok=False)
    assert not (root/'bad.pdf').exists()
    print('PASS: unsupported compression rejected without output')
    noisy=Image.frombytes('RGB',(512,725),random.Random(23).randbytes(512*725*3))
    noisy.save(root/'noise.png')
    upload=root/'upload.pdf'
    run('upload','--src',root/'noise.png','--out',upload,'--max-mb','0.7')
    assert 0<upload.stat().st_size<700000
    print('PASS: strict decimal MB cap with actual JPEG encoding')
    run('upload','--src',root/'noise.png','--out',root/'impossible.pdf','--max-mb','0.0001',ok=False)
    assert not (root/'impossible.pdf').exists()
    run('upload','--src',root/'noise.png','--out',root/'oversized.pdf','--max-input-pixels','1000',ok=False)
    assert not (root/'oversized.pdf').exists()
    print('PASS: impossible byte budget and oversized decode fail clearly')
print('All 6 integration checks passed')
