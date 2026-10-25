#!/usr/bin/env python3
"""Unit harvests (حصاد الوحدات), owner 2026-10-25:
1. Every question's ideal time («الوقت المثالي») is SEC = 3 seconds, in every subject (points fall after it, see the engine's pts()).
2. Arabic: the grammar of each lesson (النحو / الصرف / الأساليب) is asked in the harvest too. Its questions come from the grammar
   slides added to the interactive decks (tools/grammar_slides.json, slides with `add`): quiz / balloons / race items become
   multiple-choice questions, tf items become «صح / خطأ» (the fix as the explanation). They go right after the lesson's own
   questions (the harvest lesson ids are the deck's), up to PER_LESSON per lesson, fewer when the lesson already asks grammar.
   Added questions carry "g": 1, so rerunning replaces them (idempotent).
Usage: python3 tools/tune_harvest.py [grade/subject ...]   (default: every harvest)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
SEC = 3
PER_LESSON = 6
KW = re.compile(r'إعراب|أعرب|مرفوع|منصوب|مجرور|مبتدأ|خبر|فاعل|مفعول|حرف جر|حروف الجر|جملة اسمية|جملة فعلية|الجملة الاسمية|الجملة الفعلية|'
                r'مثنى|المضاف|نعت|معطوف|ممنوع من الصرف|مبني|معرب|نائب|ظرف|اسم إشارة|أسماء الإشارة|ضمير|الميزان|وزن|مجزوم|المضارع|الحال|'
                r'تمييز|التعجب|المدح|الإغراء|كاد|ظن')
TASHKEEL = re.compile(r'[ً-ْٰ]')

def load(p):
    h = open(p, encoding='utf8').read(); m = re.search(r'const H=', h)
    o, e = json.JSONDecoder().raw_decode(h, m.end()); return h, o, m.end(), e

def deck_of(g):
    f = R + ('%d/arabic/interactive/index.html' if g <= 5 else '%d/arabic/slides/index.html') % g
    if not os.path.exists(f): return None
    h = open(f, encoding='utf8').read(); m = re.search(r'window\.DECK=', h)
    return json.JSONDecoder().raw_decode(h, m.end())[0]

def txt(s): return re.sub(r'\s+', ' ', re.sub(r'\[\[(.*?)\]\]', r'(\1)', str(s))).strip()
def bare(s): return TASHKEEL.sub('', txt(s))

# a game slide's item may be only a sentence or a word: its question was the slide title. The harvest asks it in full.
SELF = re.compile(r'^(حول|اختر)|إعراب|علامة|شبه الجملة في|نوع الخبر|؟|___|\.\.\.|…|:$')
ASK = {'تحدي نوع الجملة': 'ما نَوْعُ الْجُمْلَةِ؟', 'سباق أقسام الكلام': 'اسْمٌ أَمْ فِعْلٌ أَمْ حَرْفٌ؟',
       'ما علامة إعراب الكلمة الملونة؟': 'ما عَلامَةُ إِعْرابِ الْكَلِمَةِ الَّتي بَيْنَ الْقَوْسَيْنِ؟',
       'أفرقع الفاعل': 'ما الْفاعِلُ في الْجُمْلَةِ؟', 'أفرقع المفعول به': 'ما الْمَفْعولُ بِهِ في الْجُمْلَةِ؟',
       'أستخرج الاسم المجرور': 'ما الِاسْمُ الْمَجْرورُ في الْجُمْلَةِ؟', 'سباق حالات المضارع': 'ما حالَةُ الْفِعْلِ الْمُضارِعِ الَّذي بَيْنَ الْقَوْسَيْنِ؟'}
def ask(title, q):
    if SELF.search(bare(q)): return q
    t = re.sub(r'^سِباقٌ\s*:\s*', '', txt(title))
    a = ASK.get(bare(title)) or (t if t.endswith('؟') else None)
    if not a: return q
    return a + ' ' + (q if q.startswith('«') else '«' + q.rstrip('.') + '»')

def grammar_qs(deck):
    """{lesson id: [harvest questions]} from the deck's added grammar slides, choice questions first"""
    out = {}
    for L in deck['lessons']:
        mc, tf = [], []
        for s in L['slides']:
            if 'add' not in s: continue
            t = s['type']
            if t in ('quiz', 'balloons', 'race'):
                for q in s.get('qs') or s.get('rounds') or []:
                    o = q.get('o') or q.get('options') or []
                    if len(o) >= 2 and isinstance(q.get('a'), int) and 0 <= q['a'] < len(o) and len(set(map(bare, o))) == len(o):
                        mc.append({'q': ask(s.get('title', ''), txt(q['q'])), 'o': [txt(x) for x in o], 'a': q['a'], 'why': '', 't': 'mc'})
            elif t == 'tf':
                for it in s.get('items') or []:
                    if isinstance(it.get('a'), bool):
                        tf.append({'q': txt(it['text']), 'o': ['صح', 'خطأ'], 'a': 0 if it['a'] else 1, 'why': txt(it.get('fix', '')), 't': 'tf'})
        seen, qs = set(), []
        for q in mc[:5] + tf[:2] + mc[5:] + tf[2:]:   # mostly choice questions, a true/false or two among them
            k = bare(q['q'])
            if k not in seen: seen.add(k); qs.append(q)
        if qs: out[L['id']] = qs
    return out

def tune(p, gq):
    h, o, i, e = load(p); qs = [q for q in o['qs'] if not q.get('g')]
    added = 0
    if gq:
        res = []
        for k, q in enumerate(qs):
            res.append(q)
            last = k + 1 == len(qs) or qs[k + 1]['l'] != q['l']
            if last and q['l'] in gq:
                have = sum(1 for x in qs if x['l'] == q['l'] and KW.search(x['q'] + ' ' + x.get('why', '')))
                for n in gq[q['l']][:max(0, PER_LESSON - have)]:
                    res.append(dict(n, l=q['l'], g=1)); added += 1
        qs = res
    for q in qs: q['sec'] = SEC
    o['qs'] = qs
    t = h[:i] + json.dumps(o, ensure_ascii=False).replace('</', '<\\/') + h[e:]
    if t != h: open(p, 'w', encoding='utf8').write(t)
    return added, len(qs)

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    tot = 0
    for d in sorted(glob.glob(R + '[0-9]*/*/harvest/')):
        rel = d[len(R):-len('harvest/')].strip('/')
        if only and rel not in only: continue
        g, s = rel.split('/')
        deck = deck_of(int(g)) if s == 'arabic' and int(g) <= 8 else None   # grades 9–12: grammar lessons are harvest lessons of their own
        gq = grammar_qs(deck) if deck else {}
        rows = []
        for p in sorted(glob.glob(d + 'u*/index.html'), key=lambda x: int(re.search(r'/u(\d+)/', x).group(1))):
            a, n = tune(p, gq); tot += a
            rows.append('%s+%d=%d' % (p.split('/')[-2], a, n) if a else p.split('/')[-2])
        print('%-16s %s' % (rel, ' '.join(rows)))
    print('done: %d grammar questions added, ideal time %d s' % (tot, SEC))

if __name__ == '__main__': main()
