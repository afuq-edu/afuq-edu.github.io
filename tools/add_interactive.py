#!/usr/bin/env python3
"""Add (or replace) a gold-only 'العرض التفاعلي' section next to the board: one self-contained HTML.
Usage: python3 tools/add_interactive.py GRADE SUBJECT LESSONS.html
Creates <g>/<s>/interactive/index.html (guarded like slides), the portal card + SECTIONS entry before the board,
and the catalogue part before the board in p/index.html. Rerunning replaces the page."""
import re, os, sys, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
T = 'العرض التفاعلي'
ICON = '<span class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M12 16v4M8 20h8M7 9l3 2-3 2"/></svg></span>'
def main():
    g = int(sys.argv[1]); s = sys.argv[2]; f = sys.argv[3]; d = '%d/%s/' % (g, s)
    v = open(R+'p/index.html', encoding='utf8').read()
    c = json.loads(re.search(r'var CAT=(\{.*\});\s*\n', v).group(1))[d]; pre = c['lock']
    lab = re.sub(r'\s*–?\s*الصف.*$', '', c['title']).strip() or s
    guard = ("<script>(function(){var k='%sinteractive';function g(n,x){try{return window[n].getItem(x)==='1'}catch(e){return false}}"
             "if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;"
             "document.documentElement.style.display='none';location.replace('../?lock=interactive')})()</script>"
             "<script src=\"/assets/pkgmode.js\" data-role=\"page\"></script>") % pre
    h = open(f, encoding='utf8').read(); assert '<head>' in h, f
    os.makedirs(R+d+'interactive', exist_ok=True)
    open(R+d+'interactive/index.html', 'w', encoding='utf8').write(h.replace('<head>', '<head>' + guard, 1))
    sys.path.insert(0, R+'tools'); __import__('fit_slides').fix(R+d+'interactive/index.html')  # fit the deck to any screen
    p = R+d+'index.html'; u = open(p, encoding='utf8').read()
    if 'data-id="interactive"' not in u:
        ref = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="board">.*?</button>\n', u, re.S).group(0)
        card = ref.replace('data-id="board"', 'data-id="interactive"', 1)
        card = re.sub(r'<h3>.*?</h3>', '<h3>%s</h3>' % T, card)
        card = re.sub(r'<p>.*?</p>', '<p>%s – %s – الصف %s: شرح الدروس بأسلوب تفاعلي</p>' % (T, lab, GRADE[g]), card, flags=re.S)
        card = re.sub(r'<span class="ic">.*?</span>', ICON, card, count=1, flags=re.S)
        u = u.replace(ref, card + ref, 1)
        u = u.replace("    board:{title:", "    interactive:{title:'%s',hash:null},\n    board:{title:" % T, 1); assert 'interactive:{title' in u
        open(p, 'w', encoding='utf8').write(u)
    o = '"lock": "%s", "parts": [' % pre; i = v.index(o); j = v.index(']]', i)
    if '"interactive"' not in v[i:j]:
        seg = v[i:j].replace('["board", "السبورات", true]', '["interactive", "%s", true], ["board", "السبورات", true]' % T, 1)
        assert '"interactive"' in seg; v = v[:i] + seg + v[j:]
        open(R+'p/index.html', 'w', encoding='utf8').write(v)
    __import__('mark_new').mark(d + 'interactive')  # «جديد» badge
    print('done', d + 'interactive')
main()
sys.path.insert(0, R + 'tools'); _d = __import__('dedupe_fonts')  # fonts once in /assets/f (1 GB Pages limit)
for _r in (R, os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'):
    if os.path.isdir(_r): sys.argv = ['', _r]; _d.main()
sys.argv = ['']; __import__('add_lesson_links').main()  # lesson list in the teacher deck + one student link per lesson
sys.argv = ['']; __import__('extract_imgs').main()  # deck images once in /assets/img (both repos)
