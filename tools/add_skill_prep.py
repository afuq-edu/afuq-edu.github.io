#!/usr/bin/env python3
"""«تحضير حسب المهارة» (owner, 2026-10-29): Arabic grades 1–4, an extra prep beside the period prep (ملف التحضير stays as it is).
For every lesson the periods are gathered by skill — التحدث، القراءة، الأنماط اللغوية، الإملاء، الخط، التعبير — and each skill
has one prep in the 10 Noor fields (same rules as every prep: outcome times, one warm-up time, numbered steps ending with
«غلق الدرس – …», «تفريد التعليم (5 دقائق):», «أسئلة التقويم الختامي (5 دقائق):»). The prep covers the skill's k periods (40 × k min).
Usage: python3 tools/add_skill_prep.py GRADE OUT.json [OUT.json ...]
  OUT = {"grade", "lessons": [{"li", "title", "skills": [{"skill", "periods": [pi], "f": [10 fields]}]}]} (li / pi index the
  grade's period prep, read again here for the unit, week and period titles).
Writes <g>/arabic/skills/index.html, the portal card (opens like ملف التحضير, no gold lock), the catalogue part, the home list
and the «جديد» badge. Not under prep*/: the period-prep tools (stage times, 35-minute view…) leave it alone."""
import re, os, sys, json, html as H
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
import add_apps as A
KEY, TITLE = 'skills', 'تحضير حسب المهارة'
SK = ['التحدث', 'القراءة', 'الأنماط اللغوية', 'الإملاء', 'الخط', 'التعبير']
SKI = {'التحدث': '🗣️', 'القراءة': '📖', 'الأنماط اللغوية': '🧩', 'الإملاء': '✍️', 'الخط': '🖋️', 'التعبير': '💬'}
FIELDS = ['المخرجات التعليمية', 'المستوى المعرفي', 'الاستراتيجيات', 'المصادر التعليمية', 'المفاهيم', 'التهيئة / التمهيد / التعلم القبلي',
          'إجراءات سير الدرس / الأنشطة التدريسية', 'التقويم التكويني', 'التقويم الختامي', 'ملاحظات ضمن خطة الدراسة الأسبوعية']
A.ICON[KEY] = A.SVG % '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M8.5 13.5l2 2 4-4"/>'

def source(g): return __import__('skill_norm').norm(g)

def page(g, data):
    grd = A.GRADES[g - 1].replace('_', ' ')
    js = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return ('''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><script src="/assets/pkgmode.js" data-role="page"></script>
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%(t)s – اللغة العربية – الصف %(g)s</title>
<style>
:root{--bg:#F4F7FB;--card:#fff;--ink:#1D2A3F;--muted:#5E6B84;--line:#DCE4EF;--brand:#2E6F73;--soft:#EAF4F3;--chip:#F1F5FA}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,"Segoe UI",system-ui,sans-serif;line-height:1.75}
main{max-width:900px;margin:0 auto;padding:18px 14px 60px}a.back{color:var(--muted);text-decoration:none;font-size:14px}
h1{margin:8px 0 2px;font-size:clamp(20px,4.6vw,26px)}p.sub{margin:0 0 14px;color:var(--muted);font-size:14.5px}
.pick{display:grid;gap:10px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px 14px;margin-bottom:12px}
select{width:100%%;font:inherit;padding:9px 10px;border:1px solid var(--line);border-radius:12px;background:#fff}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{font:inherit;font-size:14.5px;font-weight:700;padding:7px 13px;border-radius:999px;border:1px solid var(--line);background:var(--chip);cursor:pointer;color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--brand);border-color:var(--brand);color:#fff}
.meta{background:var(--soft);border-radius:14px;padding:10px 14px;margin:0 0 12px;font-size:14px;color:#24414A}.meta b{color:var(--ink)}.meta ol{margin:4px 0 0;padding-inline-start:20px}
.f{background:var(--card);border:1px solid var(--line);border-radius:16px;margin:0 0 12px;overflow:hidden}
.f h2{display:flex;align-items:center;gap:8px;margin:0;padding:10px 14px;font-size:15.5px;background:#F7FAFD;border-bottom:1px solid var(--line)}
.f h2 span{flex:1}.cp{font:inherit;font-size:13.5px;font-weight:700;padding:5px 12px;border-radius:10px;border:1px solid var(--brand);background:#fff;color:var(--brand);cursor:pointer}
.cp.ok{background:var(--brand);color:#fff}.f pre{margin:0;padding:12px 14px;white-space:pre-wrap;font:inherit;font-size:15px}
.all{display:inline-block;margin:0 0 12px;font:inherit;font-weight:700;padding:8px 14px;border-radius:12px;border:0;background:var(--brand);color:#fff;cursor:pointer}
</style></head><body><main>
<a class="back" href="../">→ اللغة العربية – الصف %(g)s</a>
<h1>🧭 %(t)s</h1>
<p class="sub">تحضير إضافي بجانب «ملف التحضير»: حصص كل مهارة في الدرس مجموعة في تحضير واحد بحقول نور العشرة. اختر الدرس ثم المهارة، وانسخ كل بند بضغطة.</p>
<div class="pick"><select id="les" aria-label="الدرس"></select><div class="chips" id="sk" role="group" aria-label="المهارة"></div></div>
<div id="view"></div>
</main>
<script type="application/json" id="data">%(js)s</script>
<script>
(function(){
var D=JSON.parse(document.getElementById('data').textContent), F=%(fields)s, I=%(icons)s;
var les=document.getElementById('les'), sk=document.getElementById('sk'), view=document.getElementById('view');
var st={l:0,s:0}; try{var sv=JSON.parse(localStorage.getItem('afuq-skills-g%(gn)s')||'null'); if(sv&&D[sv.l]) st=sv;}catch(e){}
var u=null, og=null;
D.forEach(function(L,i){ if(L.u!==u){ og=document.createElement('optgroup'); og.label=L.u||''; les.appendChild(og); u=L.u; }
  var o=document.createElement('option'); o.value=i; o.textContent=L.t; og.appendChild(o); });
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML}
function copy(t,b){ var done=function(){ b.classList.add('ok'); var x=b.textContent; b.textContent='✔ نُسخ'; setTimeout(function(){b.classList.remove('ok');b.textContent=x},1400); };
  if(navigator.clipboard&&window.isSecureContext) navigator.clipboard.writeText(t).then(done,function(){fb(t);done()}); else { fb(t); done(); } }
function fb(t){ var a=document.createElement('textarea'); a.value=t; a.style.position='fixed'; a.style.opacity='0'; document.body.appendChild(a); a.select(); try{document.execCommand('copy')}catch(e){} a.remove(); }
function draw(){
  var L=D[st.l]; if(!L.s[st.s]) st.s=0; var S=L.s[st.s];
  try{localStorage.setItem('afuq-skills-g%(gn)s',JSON.stringify(st))}catch(e){}
  les.value=st.l; sk.innerHTML='';
  L.s.forEach(function(x,i){ var b=document.createElement('button'); b.type='button'; b.className='chip'; b.textContent=(I[x.k]||'')+' '+x.k; b.setAttribute('aria-pressed',String(i===st.s)); b.onclick=function(){st.s=i;draw()}; sk.appendChild(b); });
  var h='<div class="meta"><b>مهارة '+esc(S.k)+'</b> · '+S.p.length+(S.p.length===1?' حصة':(S.p.length===2?' حصتان':' حصص'))+' ('+(40*S.p.length)+' دقيقة)'+(S.w?' · '+esc(S.w):'')+'<ol>'+S.p.map(function(a){return '<li>'+esc(a)+'</li>'}).join('')+'</ol></div>';
  S.f.forEach(function(t,i){ h+='<section class="f"><h2><span>'+(i+1)+'. '+esc(F[i])+'</span><button type="button" class="cp" data-i="'+i+'">نسخ</button></h2><pre>'+esc(t)+'</pre></section>'; });
  view.innerHTML=h;
  view.querySelectorAll('.cp').forEach(function(b){ b.onclick=function(){ copy(S.f[+b.dataset.i],b); }; });
}
les.onchange=function(){ st.l=+les.value; st.s=0; draw(); };
draw();
})();
</script>
</body></html>''') % {'t': TITLE, 'g': grd, 'gn': g, 'js': js, 'fields': json.dumps(FIELDS, ensure_ascii=False), 'icons': json.dumps(SKI, ensure_ascii=False)}

def main():
    g = int(sys.argv[1]); d = '%d/arabic/' % g
    src = source(g); out = {}
    for f in sys.argv[2:]:
        for L in json.load(open(f, encoding='utf8'))['lessons']: out[L['li']] = L
    data = []
    for li, S in enumerate(src):
        if li not in out: continue
        sk = []
        for s in sorted(out[li]['skills'], key=lambda x: SK.index(x['skill'])):
            ps = sorted(s['periods']); wk = [src[li]['p'][i].get('wk', '') for i in ps]
            weeks = ' – '.join(dict.fromkeys(re.sub(r'\s*[(（].*$', '', w).strip() for w in wk if w))
            sk.append({'k': s['skill'], 'p': [src[li]['p'][i]['ax'] for i in ps], 'w': weeks, 'f': s['f']})
        data.append({'t': S['t'], 'u': S['u'], 's': sk})
    A.write(d + KEY + '/index.html', page(g, data))
    # portal: the card after ملف التحضير, opening like it (no gold lock)
    u = A.read(d + 'index.html')
    if 'data-id="%s"' % KEY not in u:
        m = re.search(A.CARD % 'prep', u, re.S)
        card = re.sub(r'data-id="[a-z0-9]+"', 'data-id="%s"' % KEY, m.group(0), count=1)
        card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % TITLE, card)
        card = re.sub(r'<p>.*?</p>', '<p>حصص كل مهارة مجموعة في تحضير واحد – اللغة العربية – الصف %s</p>' % A.GRADES[g - 1].replace('_', ' '), card, flags=re.S)
        card = re.sub(r'<span class="ic">.*?</span>', '<span class="ic">%s</span>' % A.ICON[KEY], card, count=1, flags=re.S)
        u = u.replace(m.group(0), m.group(0) + card, 1)
        e = re.search(r"    prep:\{title:'[^']*',hash:null\},?\n", u); line = e.group(0)
        u = u.replace(line, (line if line.rstrip().endswith(',') else line.rstrip('\n') + ',\n') + "    %s:{title:'%s',hash:null},\n" % (KEY, TITLE), 1)
        u = u.replace("if(id==='prep'||isUnlocked(id))", "if(id==='prep'||id==='%s'||isUnlocked(id))" % KEY, 1)
        A.write(d + 'index.html', u)
    # catalogue: like prep (not a gold part)
    v = A.read('p/index.html'); cat = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1)); pre = cat[d]['lock']
    m = re.search(r'var ICON=(\{.*?\});', v); ic = json.loads(m.group(1))
    if KEY not in ic: ic[KEY] = A.ICON[KEY]; v = v[:m.start(1)] + json.dumps(ic, ensure_ascii=False) + v[m.end(1):]
    o = '"lock": "%s", "parts": [' % pre; i = v.index(o); j = v.index(']]', i) + 1; seg = v[i:j]
    if '["%s"' % KEY not in seg:
        seg = seg.replace('["prep", "ملف التحضير", false]', '["prep", "ملف التحضير", false], ["%s", "%s", false]' % (KEY, TITLE), 1)
    A.write('p/index.html', v[:i] + seg + v[j:])
    L = A.read('index.html').split('\n'); k = next(n for n, x in enumerate(L) if x.startswith('    %d:[' % g)); x = L[k]
    a = x.find("['arabic/'")
    if a >= 0:
        b = x.index("']", a); s = x[a:b]
        if TITLE not in s: s = s.replace('ملف التحضير', 'ملف التحضير · ' + TITLE, 1)
        L[k] = x[:a] + s + x[b:]; A.write('index.html', '\n'.join(L))
    __import__('mark_new').mark(d + KEY)
    print('done', d + KEY, len(data), 'lessons,', sum(len(x['s']) for x in data), 'skill preps')

if __name__ == '__main__': main()
