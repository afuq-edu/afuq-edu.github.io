#!/usr/bin/env python3
"""/sync-links: the links program's packages → p/packages.json (owner, 2026-10-30). The program keeps one document per
package (collection «packages»: code, items, all, plain, nameOverride, cancelled, to); the site's link page reads
p/packages.json {code: value}. Value = ("!" if plain) + ("*" if all else items) + ("@@"+nameOverride), or "-" when cancelled.
Usage: python3 tools/sync_packages.py DIR [--write]
  DIR: the package documents saved as JSON files (ArtifactData list/query with out_dir; any depth).
  Prints the new and changed links (an existing value differing only in where «!» sits is left as it is); --write applies them.
  Codes that are on the site but not in the program are listed and kept."""
import os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = R + 'p/packages.json'

def value(P):
    if P.get('cancelled'): return '-'
    v = ('!' if P.get('plain') else '') + ('*' if P.get('all') else (P.get('items') or ''))
    return v + ('@@' + P['nameOverride'] if P.get('nameOverride') else '')

def norm(v):
    if v is None: return None
    a, b = (v.split('@@', 1) + [''])[:2]
    return ('!' if (a.startswith('!') or a.endswith('!')) else '') + a.strip('!') + ('@@' + b if '@@' in v else '')

def main():
    src = sys.argv[1]; write = '--write' in sys.argv
    raw = open(F, encoding='utf8').read(); site = json.loads(raw)
    prog, who = {}, {}
    for f in glob.glob(os.path.join(src, '**', '*.json'), recursive=True):
        try: P = json.load(open(f, encoding='utf8'))
        except Exception: continue
        if isinstance(P, dict) and P.get('code'): prog[P['code']] = value(P); who[P['code']] = P.get('to', '')
    new = [k for k in prog if k not in site]
    chg = [k for k in prog if k in site and norm(site[k]) != norm(prog[k])]
    gone = [k for k in site if k not in prog]
    print('في البرنامج %d باقة، وفي الموقع %d.' % (len(prog), len(site)))
    print('جديدة (%d):' % len(new)); [print('  + %s  %s  →  %s' % (k, who[k], prog[k])) for k in new]
    print('متغيرة (%d):' % len(chg)); [print('  ~ %s  %s  :  %s  →  %s' % (k, who[k], site[k], prog[k])) for k in chg]
    if gone: print('في الموقع وليست في البرنامج (تُترك كما هي) (%d): %s' % (len(gone), ' '.join(gone[:20])))
    if write and (new or chg):
        for k in new + chg: site[k] = prog[k]
        ind = 2 if '\n  "' in raw else (1 if '\n "' in raw else None)
        open(F, 'w', encoding='utf8').write(json.dumps(site, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
        print('كُتب p/packages.json: %d رابط.' % len(site))
    elif not (new or chg): print('✔ الموقع مطابق للبرنامج.')

if __name__ == '__main__': main()
