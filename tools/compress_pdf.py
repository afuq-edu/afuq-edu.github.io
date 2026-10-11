#!/usr/bin/env python3
"""Lossless-ish PDF size reduction (no image downsampling): python3 tools/compress_pdf.py in.pdf out.pdf
Keeps the smaller of (original, compressed) and checks that sampled pages render identically before accepting."""
import sys, os, shutil
import pymupdf
src, dst = sys.argv[1], sys.argv[2]
tmp = dst + '.tmp'
d = pymupdf.open(src)
d.save(tmp, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True)
a, b = pymupdf.open(src), pymupdf.open(tmp)
ok = len(a) == len(b)
if ok:
    n = len(a); idx = sorted({0, n // 4, n // 2, (3 * n) // 4, n - 1})
    ok = all(a[i].get_pixmap(dpi=60).samples == b[i].get_pixmap(dpi=60).samples for i in idx)
if ok and os.path.getsize(tmp) < os.path.getsize(src):
    os.replace(tmp, dst); how = 'compressed'
else:
    os.remove(tmp); shutil.copyfile(src, dst); how = 'kept original'
print('%s: %.1f MB -> %.1f MB (%s)' % (os.path.basename(src), os.path.getsize(src)/1e6, os.path.getsize(dst)/1e6, how))
