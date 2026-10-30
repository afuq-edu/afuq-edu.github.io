#!/usr/bin/env python3
"""Textbook references in the prep procedures (owner, 2026-10-30: «التحضير كأنه عام» — every step should name the book page and
its activity/exercise). tools/book_refs.json holds, per prep page, [step-prefix, reference] pairs read from the books in the owner's
Downloads; the reference is put at the end of every step line whose text (after «N. ») starts with the prefix, before its time:
    «2. الحلق: …؛ كتاب الطالب ص24: «أفهم وأطبق» (1) … (10 دقائق)»
Re-running changes nothing (a line already carrying its reference is skipped). A prefix matching two different steps is reported
and left alone. Then run build_quiz (the 35-minute and two-shift copies are rebuilt from the one-period data).
Usage: python3 tools/add_book_refs.py [grade/subject ...]"""
import re, os, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
END = re.compile(r'\s*\(([0-9٠-٩]+) (?:دقيقة|دقيقتان|دقائق|minutes?)\)\s*$')
STOP = re.compile(r'\\n|\n|"|<')
NUM = re.compile(r'^[0-9٠-٩]+\.\s*')

def apply(h, prefix, ref):
    hits, i = [], 0
    while True:
        i = h.find(prefix, i)
        if i < 0: break
        m = STOP.search(h, i); j = m.start() if m else len(h)
        hits.append((i, j)); i = j
    if not hits: return h, 'missing'
    base = {END.sub('', h[a:b]).split('؛ ' + ref)[0] for a, b in hits}
    if len(base) > 1: return h, 'ambiguous'
    done = 0
    for a, b in reversed(hits):
        seg = h[a:b]
        if ref in seg: continue
        t = END.search(seg)
        if not t: continue
        seg = seg[:t.start()] + '؛ ' + ref + seg[t.start():]
        h = h[:a] + seg + h[b:]; done += 1
    return h, done

def main():
    refs = json.load(open(R + 'tools/book_refs.json', encoding='utf8'))
    only = [a.strip('/') for a in sys.argv[1:]]
    for page, d in refs.items():
        if page.startswith('_') or (only and '/'.join(page.split('/')[:2]) not in only): continue
        p = R + page + '/index.html'; h = open(p, encoding='utf8').read(); n = 0; bad = []
        for prefix, ref in d['steps']:
            h, r = apply(h, prefix, ref)
            if isinstance(r, int): n += r
            else: bad.append('%s: %s' % (r, prefix[:50]))
        open(p, 'w', encoding='utf8').write(h)
        print('%s: %d مواضع%s' % (page, n, ''.join('\n   ✘ ' + b for b in bad)))

if __name__ == '__main__': main()
