#!/usr/bin/env python3
"""/add-files: sort the owner's uploads (zips and PDFs) for the add tools (owner, 2026-10-30).
  • subject apps (folders with index.html + manifest.webmanifest, «الملخصات/» beside): grouped by the grade in the manifest name
    «<المادة> - الصف <…>» → OUT/apps/الصف_<grade>/<subject folder>/   (then: python3 tools/add_apps.py OUT/apps)
  • curriculum stories «قصص_المنهج_<المادة>_الصف_<الصف>.pdf» → OUT/stories/   (then: python3 tools/add_stories.py OUT/stories/*.pdf)
  • anything else → OUT/other/ and listed (books, preps… need a person's decision).
Names are made NFC (Mac zips carry NFD), __MACOSX and .DS_Store dropped, a duplicate (same index.html) skipped.
Usage: python3 -I tools/sort_uploads.py OUT FILE.zip|FILE.pdf ...   (OUT must be outside the repo, e.g. the scratchpad)"""
import zipfile, sys, os, unicodedata, json, shutil, hashlib, re

def nfc(s): return unicodedata.normalize('NFC', s)
def names(i):
    n = i.filename
    if i.flag_bits & 0x800 == 0:
        try: n = n.encode('cp437').decode('utf8')
        except Exception: pass
    return nfc(n)

def main():
    out = os.path.abspath(sys.argv[1]); tmp = out + '_unpacked'; shutil.rmtree(tmp, ignore_errors=True)
    for k, f in enumerate(sys.argv[2:]):
        d = os.path.join(tmp, str(k))
        if f.lower().endswith('.zip'):
            z = zipfile.ZipFile(f)
            for i in z.infolist():
                n = names(i)
                if n.endswith('/') or n.startswith('__MACOSX') or '.DS_Store' in n: continue
                p = os.path.normpath(os.path.join(d, n)); assert p.startswith(d), n
                os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(z.read(i))
        else:
            os.makedirs(d, exist_ok=True); shutil.copyfile(f, os.path.join(d, nfc(os.path.basename(f)).split('-', 1)[-1] if re.match(r'^[0-9a-f]{8}-', os.path.basename(f)) else nfc(os.path.basename(f))))
    apps = stories = other = 0; seen = {}
    for dp, dns, fns in os.walk(tmp):
        if 'manifest.webmanifest' in fns and 'index.html' in fns:
            name = json.load(open(os.path.join(dp, 'manifest.webmanifest'), encoding='utf8')).get('name', '')
            if ' - ' not in name: print('  ? تطبيق بلا صف في اسمه:', name, dp); continue
            subj, grade = [x.strip() for x in name.rsplit(' - ', 1)]
            dst = os.path.join(out, 'apps', grade.replace(' ', '_'), nfc(os.path.basename(dp)))
            h = hashlib.md5(open(os.path.join(dp, 'index.html'), 'rb').read()).hexdigest()
            if os.path.exists(dst):
                print('  = مكرر:', name, '(نفس الملف)' if seen.get(dst) == h else '(مختلف! راجعه)'); continue
            shutil.copytree(dp, dst); seen[dst] = h; apps += 1
            n = len(os.listdir(os.path.join(dp, 'الملخصات'))) if os.path.isdir(os.path.join(dp, 'الملخصات')) else 0
            print('  تطبيق: %s | %d ملخص' % (name, n)); dns[:] = []; continue
        for fn in fns:
            p = os.path.join(dp, fn)
            if re.match(r'^قصص_المنهج_.+_الصف_.+\.pdf$', nfc(fn)):
                os.makedirs(os.path.join(out, 'stories'), exist_ok=True); shutil.copyfile(p, os.path.join(out, 'stories', nfc(fn))); stories += 1
            elif not any(x in dp for x in ('الملخصات', 'icons')):
                os.makedirs(os.path.join(out, 'other'), exist_ok=True); shutil.copyfile(p, os.path.join(out, 'other', nfc(fn))); other += 1
                print('  أخرى:', nfc(fn))
    shutil.rmtree(tmp, ignore_errors=True)
    print('تطبيقات %d، قصص %d، أخرى %d → %s' % (apps, stories, other, out))

if __name__ == '__main__': main()
