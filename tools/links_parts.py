#!/usr/bin/env python3
"""/sync-links: the links program's subject documents (collection «links»: path, parts [{key, name}], sections) against the
site catalogue CAT in p/index.html — every subject's sections, in the site's order (owner, 2026-10-30).
Usage: python3 tools/links_parts.py DIR [OUT_DIR]
  DIR: the «links» documents saved as JSON files (ArtifactData list with out_dir). Prints the subjects that differ; with
  OUT_DIR writes each corrected document there (<doc_id>.json, ready for an ArtifactData batch «set» pinned to its version).
  Subjects on the site with no document are listed (the program needs a new document for them)."""
import os, re, sys, json, glob, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'

def main():
    src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else None
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', open(R + 'p/index.html', encoding='utf8').read()).group(1))
    docs = {}
    for f in glob.glob(os.path.join(src, '**', '*.json'), recursive=True):
        try: d = json.load(open(f, encoding='utf8'))
        except Exception: continue
        if isinstance(d, dict) and d.get('path'): docs[d['path']] = (os.path.basename(f)[:-5], d)
    n = 0
    for k, c in cat.items():
        if k not in docs: print('  ! %s: لا وثيقة له في البرنامج (%s)' % (k, c['title'])); continue
        did, d = docs[k]; want = [p[0] for p in c['parts']]; have = [p['key'] for p in d.get('parts', [])]
        if want == have: continue
        n += 1
        print('  ~ %s (%s): ينقص %s، زائد %s%s' % (did, k, [x for x in want if x not in have] or '-', [x for x in have if x not in want] or '-',
                                                   '، الترتيب فقط' if set(want) == set(have) else ''))
        if out:
            names = {p['key']: p['name'] for p in d.get('parts', [])}
            d['parts'] = [{'key': p[0], 'name': names.get(p[0], p[1])} for p in c['parts']]
            d['sections'] = ' · '.join(p['name'] for p in d['parts'])
            d['updatedAt'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z')
            os.makedirs(out, exist_ok=True); json.dump(d, open(os.path.join(out, did + '.json'), 'w', encoding='utf8'), ensure_ascii=False)
    for k in docs:
        if k not in cat: print('  - %s: في البرنامج وليس في الموقع' % k)
    print('✔ كل المواد مطابقة للموقع.' if not n else '%d مادة تحتاج تحديثًا%s.' % (n, ' (كُتبت في %s)' % out if out else ''))

if __name__ == '__main__': main()
