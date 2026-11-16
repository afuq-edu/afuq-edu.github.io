#!/usr/bin/env python3
"""Tanween damm (U+064C) in Baloo Bhaijaan 2 looks like a single damma with a small hook: on classroom screens
teachers and children read «بَحْرٌ» as «بَحْرُ» (owner, 2026-11-16, grade 1 Arabic interactive deck).
This redraws the dammatan glyph of every Baloo Bhaijaan 2 file in /assets/f/ as two dammas side by side,
the way it is taught in the textbooks, so every page that uses the font (all decks, games, harvests,
the files repo /afuq/ which loads the same /assets/f/ files) shows it clearly.

The glyph becomes a composite of two scaled copies of the font's own damma, so it keeps the weight and
style of the font (and follows the weight axis in the variable files). Composites that use it
(shadda + dammatan, hamza + dammatan) follow automatically; mark positioning (GPOS) is unchanged.
Files keep their names, so dedupe_fonts.py (which never overwrites an existing name) keeps the fixed copy.
Usage: python3 tools/fix_tanween.py   (rerunning is a no-op: patched files are recognised and skipped)."""
import glob, os, sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent
from fontTools.pens.boundsPen import BoundsPen

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SCALE = 0.78     # each damma relative to the font's damma
GAP = 0.06       # space between the two dammas, relative to one damma's width


def bounds(gs, name):
    p = BoundsPen(gs); gs[name].draw(p); return p.bounds


def patch(path):
    try:
        f = TTFont(path)
    except Exception:
        return None
    if 'Baloo' not in (f['name'].getDebugName(1) or '') or 'glyf' not in f:
        return None
    cm = f.getBestCmap()
    tan, dam = cm.get(0x064C), cm.get(0x064F)
    if not tan or not dam:
        return None
    glyf = f['glyf']
    g = glyf[tan]
    if g.isComposite() and all(c.glyphName == dam for c in g.components):
        return 'already'
    gs = f.getGlyphSet()
    tx0, ty0, tx1, ty1 = bounds(gs, tan)
    dx0, dy0, dx1, dy1 = bounds(gs, dam)
    w, h = (dx1 - dx0) * SCALE, (dy1 - dy0) * SCALE
    gap = (dx1 - dx0) * GAP
    cx, cy = (tx0 + tx1) / 2, (ty0 + ty1) / 2          # keep the mark where the old one was
    left = cx - (2 * w + gap) / 2
    bottom = cy - h / 2
    comps = []
    for x in (left, left + w + gap):
        c = GlyphComponent()
        c.glyphName = dam
        c.x = round(x - dx0 * SCALE)
        c.y = round(bottom - dy0 * SCALE)
        c.transform = [[SCALE, 0], [0, SCALE]]
        c.flags = 0x4              # ROUND_XY_TO_GRID
        comps.append(c)
    ng = Glyph()
    ng.numberOfContours = -1
    ng.components = comps
    glyf[tan] = ng
    if 'gvar' in f and tan in f['gvar'].variations:
        del f['gvar'].variations[tan]   # offsets stay fixed; the damma components carry the weight variation
    ng.recalcBounds(glyf)
    adv, _ = f['hmtx'][tan]
    f['hmtx'][tan] = (adv, ng.xMin)
    f.save(path)
    return 'patched'


def main():
    files = sys.argv[1:] or sorted(glob.glob(R + 'assets/f/*'))
    n = {'patched': 0, 'already': 0}
    for p in files:
        r = patch(p)
        if r:
            n[r] += 1
            if r == 'patched':
                print('patched', os.path.relpath(p, R))
    print('tanween: %(patched)d patched, %(already)d already fixed' % n)


if __name__ == '__main__':
    main()
