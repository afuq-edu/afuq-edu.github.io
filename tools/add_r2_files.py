#!/usr/bin/env python3
"""Add gold-only PDF sections whose files live on Cloudflare R2.

Usage (from the repo root):
    python3 tools/add_r2_files.py tools/r2-manifest.json [--dry-run]

For each item in the manifest this script
  * writes <grade>/<subject>/<type>/index.html  (lock guard + pledge checkbox + one download card per file),
  * adds the portal card (<grade>/<subject>/index.html) and its SECTIONS entry,
  * adds the section to the custom-links page catalogue (p/index.html).
Re-running is safe: pages are rewritten, portal/catalogue entries are only added once.
The PDFs themselves are NOT in the repo: each file's "key" is a path inside the R2 bucket, served from manifest["base"].
"""
import json, re, sys, os
from urllib.parse import quote
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBJ = {'math':'الرياضيات','science':'العلوم','arabic':'أحب لغتي – اللغة العربية','english':'اللغة الإنجليزية','islamic':'التربية الإسلامية','social':'الهوية والمواطنة','it':'تقنية المعلومات','pe':'التربية البدنية','arts':'الفنون البصرية'}
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
TYPES = {'board':'السبورات','recap':'ملخصات الدروس بالصور'}
CARD_TPL_SRC = os.path.join(ROOT,'3/social/index.html')   # portal card markup is copied from a finished portal
PAGE_CSS = re.search(r'<style>.*?</style>', open(os.path.join(ROOT,'3/social/recap/index.html'),encoding='utf8').read(), re.S).group(0)

def read(p): return open(os.path.join(ROOT,p),encoding='utf8').read()
def write(p,t,dry):
    if dry: print('would write',p); return
    os.makedirs(os.path.dirname(os.path.join(ROOT,p)),exist_ok=True); open(os.path.join(ROOT,p),'w',encoding='utf8').write(t)

def lock_prefix(grade,subject):
    cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', read('p/index.html')).group(1))
    return cat['%d/%s/'%(grade,subject)]['lock']

def page(grade,subject,typ,files,base,prefix):
    label = SUBJ[subject]; title = TYPES[typ]
    guard = ("<script>(function(){var k='%s%s';function g(n,x){try{return window[n].getItem(x)==='1'}catch(e){return false}}"
             "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
             "document.documentElement.style.display='none';location.replace('../?lock=%s')})()</script>")%(prefix,typ,typ)
    plural = len(files)>1
    cards = ''
    for f in files:
        url = base.rstrip('/')+'/'+quote(f['key'])
        cards += '''  <div class="card" style="margin-top:14px">
    <h2>%s (PDF)</h2>
    <p>%s</p>
    <a class="dl" href="%s" target="_blank" rel="noopener" aria-disabled="true">⬇ تحميل %s%s</a>
  </div>
'''%(f['title'],f.get('desc',''),url,f['title'],(' (%s)'%f['size']) if f.get('size') else '')
    pledge = 'أتعهد بعدم نشر %s أو مشاركت%s مع أي شخص خارج الباقة الذهبية.'%(('هذه الملفات','ها') if plural else ('هذا الملف','ه'))
    return '''<!doctype html>
<html lang="ar" dir="rtl">
<head>%s
<meta charset="utf-8"><script src="/assets/pkgmode.js" data-role="page"></script>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s – %s – الصف %s</title>
%s
</head>
<body>
<header>
  <a href="../">→ رجوع</a>
  <h1>%s</h1>
  <p>%s · الصف %s · الفصل الدراسي الأول</p>
</header>
<main>
  <label class="pledge"><input type="checkbox" id="cb"><span>%s</span></label>
%s</main>
<script>
(function(){var cb=document.getElementById('cb'),ds=document.querySelectorAll('.dl');
cb.onchange=function(){Array.prototype.forEach.call(ds,function(d){d.setAttribute('aria-disabled',cb.checked?'false':'true')})};
Array.prototype.forEach.call(ds,function(d){d.addEventListener('click',function(e){if(d.getAttribute('aria-disabled')==='true')e.preventDefault()})});})();
</script>
</body>
</html>
'''%(guard,title,label,GRADE[grade],PAGE_CSS,title,label,GRADE[grade],pledge,cards)

def add_portal(grade,subject,typ,dry):
    p='%d/%s/index.html'%(grade,subject); t=read(p)
    if 'data-id="%s"'%typ in t: return
    src=read('3/social/index.html')
    card=re.search(r'    <button class="card" style="--c:var\(--c1\)" data-id="board">.*?</button>\n',src,re.S).group(0)
    card=card.replace('data-id="board"','data-id="%s"'%typ).replace('السبورات',TYPES[typ]).replace('الهوية والمواطنة',SUBJ[subject]).replace('الصف الثالث','الصف '+GRADE[grade])
    m=re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="(?:explorer|numbers|kahoot|homework)">',t)
    t=t.replace(m.group(0),card+m.group(0),1)
    m=re.search(r"    (?:explorer|numbers|kahoot|homework):\{title:",t)
    t=t.replace(m.group(0),"    %s:{title:'%s',hash:null},\n"%(typ,TYPES[typ])+m.group(0),1)
    write(p,t,dry)

def add_catalogue(grade,subject,typ,dry):
    t=read('p/index.html'); key='"%d/%s/"'%(grade,subject)
    i=t.index(key); j=t.index('"parts": [',i)
    if '["%s",'%typ in t[j:j+600]: return
    k=t.index('["prep", "ملف التحضير", false], ',j)+len('["prep", "ملف التحضير", false], ')
    t=t[:k]+'["%s", "%s", true], '%(typ,TYPES[typ])+t[k:]
    write('p/index.html',t,dry)

def main():
    args=[a for a in sys.argv[1:] if not a.startswith('--')]; dry='--dry-run' in sys.argv
    man=json.load(open(args[0],encoding='utf8')); base=man['base']
    for it in man['items']:
        g,s,ty=int(it['grade']),it['subject'],it['type']
        assert s in SUBJ and ty in TYPES and g in GRADE,(g,s,ty)
        pre=lock_prefix(g,s)
        write('%d/%s/%s/index.html'%(g,s,ty),page(g,s,ty,it['files'],base,pre),dry)
        add_portal(g,s,ty,dry); add_catalogue(g,s,ty,dry)
        print('ok',g,s,ty,len(it['files']),'file(s)')
if __name__=='__main__': main()
