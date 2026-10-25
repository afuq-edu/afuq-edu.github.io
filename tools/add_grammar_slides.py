#!/usr/bin/env python3
"""More slides for the grammar parts of interactive decks (the uploaded decks gave grammar only 2–5 slides: rule, examples,
one or two drills). tools/grammar_slides.json holds, per deck and lesson, the slides to add and the ORIGINAL index each group
goes before: discovery from the lesson text, the two parts of the rule, a worked إعراب model, guided إعراب (fill / word order),
drills (sort, true-false, choice), a game and a recap. Every added slide carries add=<part title>; the deck's own slides keep
their order. tools/add_lesson_links.py then grows the part (lesson_parts.json keeps the original indices) so the part entry,
its Noor link and the student page show the new slides, and the whole lesson still leaves them out.
Idempotent: earlier added slides are taken out first. Run add_lesson_links.py and add_games.py afterwards
(add_interactive.py does all of it). Usage: python3 tools/add_grammar_slides.py [grade/subject ...]"""
import re, os, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
from add_lesson_links import deck_of, js

def main():
    only = [a.strip('/') for a in sys.argv[1:]]
    spec = json.load(open(R + 'tools/grammar_slides.json', encoding='utf8'))
    for deck, lessons in spec.items():
        if deck == '_' or (only and '/'.join(deck.split('/')[:2]) not in only): continue
        p = R + deck + '/index.html'
        if not os.path.exists(p): continue
        h = open(p, encoding='utf8').read(); d, i, e = deck_of(h)
        if not d: continue
        n = 0
        for L in d['lessons']:
            sl = [s for s in L['slides'] if 'add' not in s]   # the deck's own slides
            sp = lessons.get(L.get('id'))
            if sp:
                for at, new in sorted(sp['insert'], key=lambda x: -x[0]):
                    sl[at:at] = [dict(s, add=sp['part']) for s in new]; n += len(new)
            L['slides'] = sl
        t = h[:i] + js(d) + h[e:]
        if t != h: open(p, 'w', encoding='utf8').write(t)
        print('%-24s %d grammar slides added' % (deck, n))
        g = int(deck.split('/')[0])
        if g <= 8 and os.path.isdir(R + '%d/arabic/harvest' % g): __import__('tune_harvest').main(['%d/arabic' % g])   # the harvest asks the same grammar

if __name__ == '__main__': main()
