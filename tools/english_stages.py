#!/usr/bin/env python3
"""English preps in stages (owner, 2026-10-28): the procedures of every English period run Presentation stage → Practice stage
→ Production stage, and the lesson ends with the Finishing stage (tools/add_identity.py: a fun closing activity with a
citizenship part). Each step keeps its text and order and gets its stage in front:
  1. Presentation stage – Warm-up: … (5 minutes)
  3. Practice stage – Read and circle (CB p. 19): … (8 minutes)
  5. Production stage – Act out the story in groups: … (10 minutes)
  6. Finishing stage (fun activity with citizenship) – … (5 minutes)
The stages split the period's steps in order (every stage at least one step when there are three or more): the split that fits
the steps' own words best (warm-up, listen, model, present… / drill, match, complete, workbook… / act out, role play, write
your own, project, game…), the earlier stages first. Html copies are redrawn. Rerunning recomputes them (idempotent).
Usage: python3 tools/english_stages.py [grade/subject ...]   (build_quiz.py runs it after add_identity.py)"""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import build_quiz as B
import proc_style as P
STAGES = ('Presentation stage', 'Practice stage', 'Production stage')
OLD = re.compile(r'^([0-9]+\.\s*)(?:Presentation|Practice|Production) stage – ')
FIN = re.compile(r'^[0-9]+\.\s*(?:Finishing stage|Lesson closing)\b')
KW = [re.compile(x, re.I) for x in (
    r'warm|lead-?in|starter|before you|watch|listen|present|introduc|model|new words|vocabulary|flashcard|story|predict|elicit|'
    r'grammar (?:box|recall|focus)|explain|teach|show|revis|review',
    r'practi|drill|repeat|match|circle|complete|gap|fill|workbook|activity book|exercise|comprehension|chant|song|tick|choose|'
    r'multiple choice|underline|order|sort|spell|pronunc|controlled|check|read and|look and|copy|trace|label',
    r'act out|role|produc|write (?:a |an |your|about|sentences|a paragraph|their own)|own sentences|speak|project|design|create|'
    r'game|discuss|debate|information-gap|interview|survey|personal|free|wrap-?up|plenary|report|values|presentation|poster|'
    r'perform|share|freer')]

def score(line, s): return len(set(m.group(0).lower() for m in KW[s].finditer(line)))

def stages_for(lines):
    m = len(lines)
    if m == 0: return []
    if m == 1: return [0]
    if m == 2: return [0, 2]
    sc = [[score(l, s) for s in range(3)] for l in lines]
    best, cut = None, None
    for i in range(1, m - 1):            # Presentation: [0, i), Practice: [i, j), Production: [j, m)
        for j in range(i + 1, m):
            v = sum(sc[x][0] for x in range(i)) + sum(sc[x][1] for x in range(i, j)) + sum(sc[x][2] for x in range(j, m))
            v -= 0.3 * (abs(i - m / 3) + abs(j - 2 * m / 3))    # near thirds when the words do not tell
            if best is None or v > best: best, cut = v, (i, j)
    i, j = cut
    return [0 if x < i else 1 if x < j else 2 for x in range(m)]

def staged(t):
    """the procedures text with every step's stage in front, or None"""
    blocks = [b for b in t.split('\n\n') if b.strip()]
    segs = [[]]
    for bi, b in enumerate(blocks):
        if re.match(r'^(?:Period|Lesson|الحصة)\s', b) and not re.match(r'^[0-9]+\.\s', b): segs.append([]); continue
        if re.match(r'^[0-9]+\.\s', b) and not FIN.match(b): segs[-1].append(bi)
    for sg in segs:
        first = [OLD.sub(r'\1', blocks[bi].split('\n')[0]) for bi in sg]
        for bi, line, st in zip(sg, first, stages_for([re.sub(r'^[0-9]+\.\s*', '', l)[:220] for l in first])):
            ls = blocks[bi].split('\n'); mm = re.match(r'^([0-9]+\.\s*)', line)
            ls[0] = mm.group(1) + STAGES[st] + ' – ' + line[mm.end():]; blocks[bi] = '\n'.join(ls)
    out = '\n\n'.join(blocks)
    return out if out != t else None

def fix_page(p):
    h = open(p, encoding='utf8').read(); lits = B.literals(h)
    les, kmap = B.page_lessons(lits)
    before = [json.dumps(x[3], ensure_ascii=False) for x in lits]
    n = 0
    for li, cont, k in B.field_targets(lits, kmap, 'proc'):
        v = cont[k]
        if isinstance(v, str) and not v.lstrip().startswith('<') and P.is_new(v):
            new = staged(v)
            if new: cont[k] = new; n += 1
        elif isinstance(v, dict) and isinstance(v.get('t'), str) and isinstance(v.get('h'), str) and P.is_new(v['t']):
            new = staged(v['t'])
            if new: v['t'], v['h'] = new, P.render_html(new); n += 1
        elif isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) for x in v) and P.is_new(v[1]):
            new = staged(v[1])
            if new: v[0], v[1] = P.render_html(new), new; n += 1
    t = h
    for (name, i, e, o), b0 in sorted(zip(lits, before), key=lambda z: -z[0][1]):
        if json.dumps(o, ensure_ascii=False) != b0:
            compact = '", "' not in h[i:i + 3000] and '":"' in h[i:i + 3000]
            t = t[:i] + json.dumps(o, ensure_ascii=False, separators=(',', ':') if compact else (', ', ': ')).replace('</', '<\\/') + t[e:]
    return n, t

def main(only=None):
    only = [a.strip('/') for a in (sys.argv[1:] if only is None else only)]
    tot = 0
    for p in sorted(glob.glob(R + '[0-9]*/english/prep*/index.html')):
        rel = p[len(R):-len('/index.html')]; gs = '/'.join(rel.split('/')[:2])
        if only and gs not in only: continue
        n, t = fix_page(p)
        if t != open(p, encoding='utf8').read(): open(p, 'w', encoding='utf8').write(t)
        print('%-20s %4d procedures in stages' % (rel, n)); tot += n
    print('done', tot)

if __name__ == '__main__': main()
