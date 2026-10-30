#!/usr/bin/env python3
"""/check-preps: every prep page against the owner's rules, with a report (owner, 2026-10-30):
  • outcomes: every outcome has its time «(N دقائق)», adding up to the period (40, prep35 35);
  • التهيئة: one time only, «(5 دقائق)» / «(5 minutes)» at its end;
  • procedures: the steps add up to the period − 15 (grade 6 Arabic/Islamic labelled fields: their own minutes); a lesson has
    exactly one closing step «غلق الدرس – …» / «Finishing stage – …», the last step of its last period;
  • التقويم التكويني starts «تفريد التعليم (5 دقائق):» (English «Formative questions (5 minutes):»);
  • التقويم الختامي starts «أسئلة التقويم الختامي (5 دقائق):» («Summative questions (5 minutes):»).
Usage: python3 tools/check_preps.py [grade/subject ...] [--all]    (prints a summary per page with problems; --all lists every one)"""
import re, os, sys, glob, json
from collections import Counter, defaultdict
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B, proc_style as P, outcome_times as O, form_heading  # the last two register the proc/warm and form/summ fields
TIME = re.compile(r'\(([0-9٠-٩]+) (?:دقيقة|دقيقتان|دقائق|minutes?)\)')
END = re.compile(r'\(([0-9٠-٩]+) (?:دقيقة|دقيقتان|دقائق|minutes?)\)(?=[ \t]*(?:\n|$|<))')
CLOSE = re.compile(r'^[0-9٠-٩]+\.\s*(?:غلق الدرس|Finishing stage)')
def n(s): return P.toN(s)
def labelled(c):   # grade 6 Arabic / Islamic: [«التهيئة (5 دقائق)», text] — the time sits in the label
    return isinstance(c, list) and len(c) == 2 and isinstance(c[0], str) and bool(TIME.search(c[0]))
def text(v):
    if isinstance(v, str): return v
    if isinstance(v, dict): return v.get('t') if isinstance(v.get('t'), str) else None
    if isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v): return v[1]
    return None

def check_page(p, rel):
    T = 35 if '/prep35' in rel else 40; en = rel.split('/')[1] == 'english'
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    try: les, kmap = B.page_lessons(lits)
    except Exception: return None, Counter()
    probs = defaultdict(list); tot = Counter(); closing = defaultdict(int)
    seen = set()
    def bad(kind, li, msg): probs[kind].append((li, msg))
    for li, c, k in B.field_targets(lits, kmap, 'proc'):
        v = c[k]; tot['proc'] += 1
        if isinstance(v, list) and v and isinstance(v[0], dict) and 'min' in v[0]:           # math 2-4 sessions
            key = (li, json.dumps(v, ensure_ascii=False))
            if key in seen: continue
            seen.add(key); closing[li] = max(closing[li], sum(1 for y in v if y.get('id')))
            s = sum(y['min'] for y in v)
            if s not in (T - 15,): bad('مجموع أزمنة الإجراءات', li, '%d بدل %d' % (s, T - 15))
            continue
        t = text(v)
        if not isinstance(t, str) or t.lstrip().startswith('<') or not P.is_new(t): continue
        if (li, t) in seen: continue      # the same field kept twice on the page (35-minute / two-shift copies)
        seen.add((li, t))
        nc = len(re.findall(r'^[0-9٠-٩]+\.\s*(?:غلق الدرس|Finishing stage)', t, re.M))
        closing[li] = max(closing[li], nc)        # a page may also keep the whole lesson in one text: count per text, not summed
        if nc > 1 and not en: bad('أكثر من «غلق الدرس» في نص واحد', li, str(nc))   # English: one Finishing stage per period
        lab = isinstance(c, list) and len(c) == 2 and isinstance(c[0], str) and TIME.search(c[0])
        want = n(TIME.search(c[0]).group(1)) if lab else T - 15
        for seg in O.steps_of(t):
            s = sum(d for _, d in seg)
            if s not in (want, want - 5 if '/prep35' in rel else want): bad('مجموع أزمنة الإجراءات', li, '%d بدل %d' % (s, want))
            cl = [i for i, (l, _) in enumerate(seg) if CLOSE.match(l)]
            if cl and cl[-1] != len(seg) - 1: bad('غلق الدرس ليس آخر خطوة', li, seg[cl[-1]][0][:60])
    for li in range(len(les)):
        if closing.get(li, 0) == 0: bad('درس بلا «غلق الدرس»', li, B.lesson_title(les[li]) if hasattr(B, 'lesson_title') else '')
    for li, c, k in B.field_targets(lits, kmap, 'out'):
        if li is None: continue
        t = text(c[k]); tot['out'] += 1
        if not isinstance(t, str) or t.lstrip().startswith('<'): continue
        ms = [n(x) for x in END.findall(t)]
        if not ms: bad('مخرجات بلا أزمنة', li, t[:60])
        elif sum(ms) % T: bad('مجموع أزمنة المخرجات', li, '%d (ليس من مضاعفات %d)' % (sum(ms), T))
    for li, c, k in B.field_targets(lits, kmap, 'warm'):
        if li is None or labelled(c): continue
        t = text(c[k]); tot['warm'] += 1
        if not isinstance(t, str) or t.lstrip().startswith('<') or len(t.strip()) < 10: continue
        for part in re.split(r'\n\n(?=(?:الحصة|Period|Lesson)\s*[0-9٠-٩])', t):
            ts = END.findall(part)          # times closing a line (a time inside a sentence is content)
            if len(ts) != 1 or not END.search(part.rstrip()): bad('التهيئة: زمن واحد في آخرها', li, '%d أزمنة' % len(ts))
    heads = {'form': ('Formative questions (5 minutes):' if en else 'تفريد التعليم (5 دقائق):'),
             'summ': ('Summative questions (5 minutes):' if en else 'أسئلة التقويم الختامي (5 دقائق):')}
    for which, head in heads.items():
        for li, c, k in B.field_targets(lits, kmap, which):
            if li is None or labelled(c): continue
            t = text(c[k]); tot[which] += 1
            if not isinstance(t, str) or t.lstrip().startswith('<') or not t.strip(): continue
            for part in re.split(r'\n\n(?=(?:الحصة|Period|Lesson)\s*[0-9٠-٩])', t.strip()):
                if not re.sub(r'^(?:الحصة|Period|Lesson)\s*[0-9٠-٩]+[^\n]*\n', '', part).lstrip().startswith(head):
                    bad(('التكويني لا يبدأ بـ «%s»' if which == 'form' else 'الختامي لا يبدأ بـ «%s»') % head, li, part[:50]); break
    return probs, tot

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; full = '--all' in sys.argv
    only = [a.strip('/') for a in args]
    pages = sorted(set(glob.glob(R + '[0-9]*/*/prep*/index.html') + glob.glob(R + '[0-9]*/*/prep/u*/index.html')))
    grand = Counter(); totals = Counter(); bad_pages = 0
    for p in pages:
        rel = p[len(R):-len('/index.html')]
        if only and '/'.join(rel.split('/')[:2]) not in only: continue
        probs, tot = check_page(p, rel); totals.update(tot)
        if probs is None or not probs: continue
        bad_pages += 1
        print('\n== %s' % rel)
        for kind, items in probs.items():
            grand[kind] += len(items)
            show = items if full else items[:3]
            print('  %-40s %4d   %s' % (kind, len(items), ' | '.join('درس %s: %s' % (li + 1 if isinstance(li, int) else li, m) for li, m in show)))
    print('\nفُحصت %d صفحة تحضير (%s)' % (len([p for p in pages if not only or '/'.join(p[len(R):].split('/')[:2]) in only]), ', '.join('%s %d' % kv for kv in sorted(totals.items()))))
    if not grand: print('✔ لا أخطاء: كل التحاضير مطابقة للقواعد.')
    else:
        print('✘ %d صفحة فيها ملاحظات:' % bad_pages)
        for kind, c in grand.most_common(): print('   %-40s %d' % (kind, c))
    return 1 if grand else 0

if __name__ == '__main__': sys.exit(main())
