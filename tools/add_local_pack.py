#!/usr/bin/env python3
"""Add a gold-only 'pack' (slides HTML, lesson boards + teacher questions PDFs, recap PDF) kept inside the repo.
PDFs are compressed first with tools/compress_pdf.py.
Usage: python3 tools/add_local_pack.py GRADE SUBJECT SLIDES_HTML BOARDS_PDF QUESTIONS_PDF RECAP_PDF   (use - to skip a file)
PDFs go to the files repo ($AFUQ_FILES, default /home/user/afuq): commit and push that repo too, wait for its Pages deploy, then push this one.
Templates are copied from the finished grade 3 social pages, so those must exist."""
import re, os, sys, shutil, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = os.environ.get('AFUQ_FILES', '/home/user/afuq').rstrip('/') + '/'   # PDFs live in the afuq-edu/afuq repo (served at /afuq/)
SUBJ = {'math':'الرياضيات','science':'العلوم','arabic':'أحب لغتي – اللغة العربية','english':'اللغة الإنجليزية','islamic':'التربية الإسلامية','social':'الهوية والمواطنة','physics':'الفيزياء','chemistry':'الكيمياء','biology':'الأحياء'}
GRADE = {1:'الأول',2:'الثاني',3:'الثالث',4:'الرابع',5:'الخامس',6:'السادس',7:'السابع',8:'الثامن',9:'التاسع',10:'العاشر',11:'الحادي عشر',12:'الثاني عشر'}
NAMES = {'slides':'عروض باور بوينت','board':'السبورات','recap':'ملخصات الدروس بالصور'}
def read(p): return open(R+p,encoding='utf8').read()
def pages(f): return int(re.search(r'Pages:\s+(\d+)', subprocess.check_output(['pdfinfo', f]).decode()).group(1))
def mb(f): return round(os.path.getsize(f)/1e6, 1)
def compress(src, dst):
    out = subprocess.check_output([sys.executable, R+'tools/compress_pdf.py', src, dst]).decode().strip(); print(out)
def main():
    g = int(sys.argv[1]); s = sys.argv[2]; slides, boards, questions, recap = [None if a == '-' else a for a in sys.argv[3:7]]
    lab = SUBJ[s]; grd = GRADE[g]; d = '%d/%s/' % (g, s)
    cat = __import__('json').loads(re.search(r'var CAT=(\{.*\});\s*\n', read('p/index.html')).group(1))[d]
    prefix = cat['lock']
    tb, tr, ts = read('3/social/board/index.html'), read('3/social/recap/index.html'), read('3/social/index.html')
    def sub(x):
        return x.replace('/afuq/3/social/', '/afuq/' + d).replace('ofuq-g3o-unlock-', prefix).replace('الهوية والمواطنة', lab).replace('الصف الثالث', 'الصف ' + grd).replace('social-g3', '%s-g%d' % (s, g))
    ids = []
    if slides:
        h = open(slides, encoding='utf8').read(); assert h.count('<head>') >= 1
        guard = "<script>(function(){var k='%sslides';function g(n,x){try{return window[n].getItem(x)==='1'}catch(e){return false}}if(g('localStorage',k)||g('sessionStorage',k)||g('localStorage','afuq-all')||g('sessionStorage','afuq-all'))return;document.documentElement.style.display='none';location.replace('../?lock=slides')})()</script><script src=\"/assets/pkgmode.js\" data-role=\"page\"></script>" % prefix
        os.makedirs(R+d+'slides', exist_ok=True); open(R+d+'slides/index.html', 'w', encoding='utf8').write(h.replace('<head>', '<head>' + guard, 1)); ids.append('slides')
    if boards:
        os.makedirs(R+d+'board', exist_ok=True); os.makedirs(F+d+'board', exist_ok=True)
        compress(boards, F+d+'board/lesson-boards.pdf'); bpath = F+d+'board/lesson-boards.pdf'
        b = sub(tb)
        b = re.sub(r'<p>سبورة لكل حصة.*?</p>', '<p>سبورة جاهزة لكل حصة لدروس %s للصف %s، الفصل الدراسي الأول (%d صفحة).</p>' % (lab, grd, pages(bpath)), b)
        b = re.sub(r'\(نحو [\d.]+ ميغابايت\)(?=\s*</a>)', '(نحو %s ميغابايت)' % mb(bpath), b, count=1)
        if questions:
            compress(questions, F+d+'board/classroom-board-questions.pdf'); qpath = F+d+'board/classroom-board-questions.pdf'
            b = re.sub(r'<p>أسئلة يكتبها المعلم.*?</p>', '<p>أسئلة يكتبها المعلم على السبورة أو يقترحها شفهيًا في كل حصة: في التهيئة وأثناء الشرح وختام الدرس (%d صفحة).</p>' % pages(qpath), b)
            i = b.index('(نحو', b.index('classroom-board-questions.pdf')); j = b.index('ميغابايت)', i)
            b = b[:i] + '(نحو %s ' % mb(qpath) + b[j:]
        else:
            i = b.index('  <div class="card" style="margin-top:14px">'); j = b.index('</main>'); b = b[:i] + b[j:]
            b = b.replace('أتعهد بعدم نشر هذه الملفات أو مشاركتها', 'أتعهد بعدم نشر هذا الملف أو مشاركته')
        open(R+d+'board/index.html', 'w', encoding='utf8').write(b); ids.append('board')
    if recap:
        os.makedirs(R+d+'recap', exist_ok=True); os.makedirs(F+d+'recap', exist_ok=True)
        compress(recap, F+d+'recap/lesson-summaries.pdf'); rpath = F+d+'recap/lesson-summaries.pdf'
        r = sub(tr)
        r = re.sub(r'<p>ملخصات إنفوجرافيك.*?</p>', '<p>ملخصات إنفوجرافيك مصوّرة لدروس %s للصف %s، الفصل الدراسي الأول (%d صفحة)، تصلح للعرض وللطباعة وللمراجعة.</p>' % (lab, grd, pages(rpath)), r)
        r = re.sub(r'\(نحو [\d.]+ ميغابايت\)(?=\s*</a>)', '(نحو %s ميغابايت)' % mb(rpath), r)
        open(R+d+'recap/index.html', 'w', encoding='utf8').write(r); ids.append('recap')
    def card(did): return re.search(r'    <button class="card" style="--c:var\(--c1\)" data-id="%s">.*?</button>\n' % did, ts, re.S).group(0)
    cards = ''.join(card(x if x != 'slides' else 'slides').replace('الهوية والمواطنة', lab).replace('الصف الثالث', 'الصف ' + grd) for x in ids)
    p = R+d+'index.html'; u = open(p, encoding='utf8').read()
    ids_new = [x for x in ids if 'data-id="%s"' % x not in u]
    cards = ''.join(card(x).replace('الهوية والمواطنة', lab).replace('الصف الثالث', 'الصف ' + grd) for x in ids_new)
    if ids_new:
        a = re.search(r'    <button class="card" style="--c:var\(--c\d\)" data-id="(?:explorer|numbers|kahoot|homework)">', u).group(0)
        u = u.replace(a, cards + a, 1)
        first = re.search(r"    (?:explorer|numbers|kahoot|homework):\{title:", u).group(0)
        u = u.replace(first, ''.join("    %s:{title:'%s',hash:null},\n" % (x, NAMES[x]) for x in ids_new) + first, 1)
        open(p, 'w', encoding='utf8').write(u)
        q = R+'p/index.html'; v = open(q, encoding='utf8').read()
        o = '"lock": "%s", "parts": [["prep", "ملف التحضير", false], ' % prefix; assert v.count(o) == 1, prefix
        v = v.replace(o, o + ''.join('["%s", "%s", true], ' % (x, NAMES[x]) for x in ids_new)); open(q, 'w', encoding='utf8').write(v)
    print('done', g, s, ids, 'new cards:', ids_new)
main()
