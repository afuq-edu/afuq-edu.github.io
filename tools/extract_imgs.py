#!/usr/bin/env python3
"""Store the decks' images once: every data: URI in a page's window.IMGS map is written to /assets/img/<sha1-16>.<ext>
(this repo) and replaced by that URL. The interactive decks carried ~435 MB of base64 images; the teacher deck, its
per-lesson student pages and the Noor games copies (files repo, served at /afuq/ on the same origin) now share one file
per image. Usage: python3 tools/extract_imgs.py [DIR ...]   (default: this repo and the files repo). Rerunning is a no-op.
The content tools run it after writing pages (CLAUDE.md)."""
import re, os, sys, json, base64, hashlib
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
OUT = R + 'assets/img/'
FILES = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'
EXT = {'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png', 'image/webp': 'webp', 'image/gif': 'gif', 'image/svg+xml': 'svg'}
DEC = json.JSONDecoder()

def store(uri):
    m = re.match(r'data:([\w/+.-]+);base64,(.*)$', uri, re.S)
    if not m or m.group(1) not in EXT: return None
    raw = base64.b64decode(re.sub(r'\s', '', m.group(2)))
    name = hashlib.sha1(raw).hexdigest()[:16] + '.' + EXT[m.group(1)]
    if not os.path.exists(OUT + name): open(OUT + name, 'wb').write(raw)
    return '/assets/img/' + name

def fix(path):
    s = open(path, encoding='utf8').read()
    if 'window.IMGS=' not in s or 'data:image' not in s: return 0
    out, pos, n = [], 0, 0
    for m in re.finditer(r'window\.IMGS=', s):
        try: imgs, e = DEC.raw_decode(s, m.end())
        except Exception: continue
        if not isinstance(imgs, dict): continue
        new = {}
        for k, v in imgs.items():
            u = store(v) if isinstance(v, str) and v.startswith('data:') else None
            new[k] = u or v; n += bool(u)
        out.append(s[pos:m.end()]); out.append(json.dumps(new, ensure_ascii=False).replace('</', '<\\/')); pos = e
    if not n: return 0
    out.append(s[pos:]); t = ''.join(out)
    open(path, 'w', encoding='utf8').write(t)
    return len(s.encode()) - len(t.encode())

def main():
    os.makedirs(OUT, exist_ok=True); roots = sys.argv[1:] or [R, FILES]; saved = files = 0
    for root in roots:
        for d, dirs, fs in os.walk(root):
            dirs[:] = [x for x in dirs if x != '.git']
            for f in fs:
                if f.endswith('.html'):
                    k = fix(os.path.join(d, f))
                    if k: saved += k; files += 1
    print('images moved out of %d pages, %.1f MB of html saved' % (files, saved / 1e6))

if __name__ == '__main__': main()
