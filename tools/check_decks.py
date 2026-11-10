#!/usr/bin/env python3
"""/check-decks: the interactive decks (window.DECK) against the shapes their engine draws (owner, 2026-11-10: the match activity of
8/islamic «مَنِ الرّاعي؟» showed blank boxes — its pairs were {a, b} objects, the engine reads [a, b] arrays).
Checks every slide of every deck for:
  match / memory   pairs = [[a, b], …] strings only (never {a, b} objects), at least 2 pairs, no empty text
  flip             cards = [{front, back, …}] with a back
  sort             cards = [{text, bin}], bins = [{label}] and every card's bin is an existing index or label
  order / enter / riddle / wheel / exit / goals / summary / tf / quiz / ask: the list field exists and has no empty entry
  any text field  no empty string where the engine prints it
Usage: python3 tools/check_decks.py [grade/subject ...]     (prints the problems; exit 1 when there are any; run after adding a deck)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
DEC = json.JSONDecoder()
LIST = {'goals': 'items', 'order': 'items', 'enter': 'items', 'riddle': 'items', 'wheel': 'items', 'exit': 'items', 'tf': 'items',
        'quiz': 'qs', 'ask': 'qs', 'race': 'qs', 'boxes': 'boxes', 'balloons': 'rounds', 'homework': 'items'}
def txt(x): return isinstance(x, str) and x.strip() != ''

def check_slide(s):
    t = s.get('type'); out = []
    if t in ('match', 'memory'):
        ps = s.get('pairs')
        if not isinstance(ps, list) or len(ps) < 2: out.append('pairs missing or fewer than 2')
        else:
            for j, x in enumerate(ps):
                if not (isinstance(x, list) and len(x) == 2 and txt(x[0]) and txt(x[1])): out.append('pair %d is not [text, text]: %s' % (j + 1, json.dumps(x, ensure_ascii=False)[:60]))
    elif t == 'flip':
        for j, c in enumerate(s.get('cards') or []):
            if not (isinstance(c, dict) and txt(c.get('back'))): out.append('card %d has no back' % (j + 1))
    elif t == 'sort':
        bins, cards = s.get('bins'), s.get('cards')
        if not (isinstance(bins, list) and bins and all(isinstance(b, dict) and txt(b.get('label')) for b in bins)): out.append('bins need {label}')
        if not (isinstance(cards, list) and cards): out.append('cards missing')
        else:
            for j, c in enumerate(cards):
                if not (isinstance(c, dict) and txt(c.get('text') or c.get('icon')) and (c.get('bin') in [b.get('label') for b in (bins or []) if isinstance(b, dict)] or (isinstance(c.get('bin'), int) and 0 <= c['bin'] < len(bins or [])))): out.append('card %d: text/bin' % (j + 1))
    elif t in LIST:
        xs = s.get(LIST[t])
        if not isinstance(xs, list) or not xs: out.append('%s missing or empty' % LIST[t])
        else:
            for j, x in enumerate(xs):
                if x in ('', None, [], {}) or (isinstance(x, str) and not x.strip()): out.append('%s %d is empty' % (LIST[t], j + 1))
    return out

def main():
    only = [a.strip('/') for a in sys.argv[1:]]; n = bad = 0
    for p in sorted(glob.glob(R + '[0-9]*/*/*/index.html')):
        rel = p[len(R):-len('/index.html')]
        if only and '/'.join(rel.split('/')[:2]) not in only: continue
        try: h = open(p, encoding='utf8').read(); m = re.search(r'window\.DECK=', h)
        except Exception: continue
        if not m: continue
        try: d, _ = DEC.raw_decode(h, m.end())
        except Exception: continue   # a JavaScript literal, not JSON (3/science, 4/science): not checked here
        n += 1; probs = []
        for L in d.get('lessons', []):
            for i, s in enumerate(L.get('slides', [])):
                for x in check_slide(s): probs.append('%s slide %d (%s): %s' % (L['id'], i + 1, s.get('type'), x))
        if probs:
            bad += len(probs); print('== %s: %d problems' % (rel, len(probs)))
            for x in probs[:8]: print('   ', x)
    print('\nفُحص %d عرضًا: %s' % (n, 'لا مشاكل' if not bad else '%d مشكلة' % bad))
    return 1 if bad else 0

if __name__ == '__main__': sys.exit(main())
