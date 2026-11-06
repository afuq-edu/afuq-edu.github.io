#!/usr/bin/env python3
"""«🎧 Listen» button for the English decks (owner, 2026-11-06: «الدروس تقول استمع لكن لا يوجد زر استماع حتى يسمعوا الطلاب»).
The listening slides of the English decks (steps «Listen. 🎧 (LC1.3)», notes «شغّل المقطع 1.5») had nothing to hear: the CD tracks
are not in the project. A slide with a script gets a big «🎧 Listen» button at the bottom: it reads the script aloud with the browser's
English voice (slowly, tap again to repeat or stop), or plays a real recording when the slide has "audio": "<url>" (an mp3 of the
CD track — preferred over the script when present).
Usage: python3 tools/add_listen.py CONTENT_DIR [GRADE ...]
  CONTENT_DIR/gNN.json = {"<lesson id>": {"<slide index>": "<English script>" | null}}   (slide index = position in the lesson's slides;
  null leaves the slide as it was). Sets "listen" on the slides, patches the deck engine once (marker /*afuq-listen*/), then rebuilds
  the lesson links / student pages (add_lesson_links). Push the files repo first (student pages), wait, then this repo.
To use a real recording for a slide: set its "audio" in the deck data by hand or add {"audio": url} through this file's format
({"<lesson>": {"<i>": {"audio": "/…/1.5.mp3"}}}). Rerunning replaces the scripts."""
import re, os, sys, json, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
sys.path.insert(0, R + 'tools')
DEC = json.JSONDecoder()
MARK = '/*afuq-listen*/'
JS = MARK + r"""
let LST=null;
function listenStop(){try{if(LST&&LST.a){LST.a.pause();LST.a=null}if('speechSynthesis' in window)speechSynthesis.cancel()}catch(e){}if(LST&&LST.b){LST.b.classList.remove('on');LST.b.firstChild.textContent='🎧'}LST=null}
function listenBtn(W,s){
  if(!s||!(s.listen||s.audio))return;
  const b=document.createElement('button');b.className='listenbtn';b.type='button';b.innerHTML='<span>🎧</span> Listen';b.title='استمع';
  const done=()=>{b.classList.remove('on');b.firstChild.textContent='🎧';if(LST&&LST.b===b)LST=null};
  b.onclick=e=>{e.stopPropagation();const was=LST&&LST.b===b;listenStop();if(was)return;LST={b};b.classList.add('on');b.firstChild.textContent='⏹';
    if(s.audio){const a=new Audio(s.audio);LST.a=a;a.onended=done;a.onerror=()=>{done();if(s.listen)speakListen(s.listen,b,done)};a.play().catch(()=>{done();if(s.listen)speakListen(s.listen,b,done)});return}
    speakListen(s.listen,b,done)};
  W.append(b)}
function speakListen(t,b,done){
  if(!('speechSynthesis' in window)){done();alert('جهازك لا يدعم القراءة الصوتية');return}
  LST={b};b.classList.add('on');b.firstChild.textContent='⏹';
  const parts=String(t).split(/(?<=[.?!])\s+/).filter(Boolean);let k=0;
  const vs=speechSynthesis.getVoices(),v=vs.find(x=>/^en[-_]GB/i.test(x.lang))||vs.find(x=>/^en/i.test(x.lang));
  const next=()=>{if(!LST||LST.b!==b)return;if(k>=parts.length){done();return}
    const u=new SpeechSynthesisUtterance(parts[k++]);u.lang='en-GB';u.rate=.8;if(v)u.voice=v;u.onend=()=>setTimeout(next,350);u.onerror=done;speechSynthesis.speak(u)};
  speechSynthesis.cancel();next()}
"""
CSS = MARK + (".listenbtn{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);z-index:6;display:flex;align-items:center;gap:12px;"
              "padding:12px 40px;border-radius:50px;border:4px solid #2b3a55;background:#ffcb3d;color:#2b3a55;font-weight:800;font-size:42px;line-height:1.2;font-family:inherit;"
              "cursor:pointer;box-shadow:0 6px 0 rgba(0,0,0,.2)}.listenbtn span{font-size:46px}.listenbtn.on{background:#7ee0a0}.listenbtn:active{transform:translateX(-50%) translateY(3px)}")

def patch(h):
    if MARK in h: return h
    a = 'function go(i,dir){'; assert h.count(a) == 1, 'go() not found'
    h = h.replace(a, JS + a + 'listenStop();', 1)
    b = "$('#count').textContent=(i+1)+' / '+FLAT.length;"; assert h.count(b) == 1, 'count line not found'
    h = h.replace(b, 'listenBtn(W,s);' + b, 1)
    assert '</style>' in h
    return h.replace('</style>', CSS + '</style>', 1)

def build(g, content):
    p = None
    for sec in ('interactive', 'slides'):
        q = R + '%d/english/%s/index.html' % (g, sec)
        if os.path.exists(q) and 'window.DECK=' in open(q, encoding='utf8').read(): p = q; break
    if not p: print('no deck for grade', g); return None
    h = open(p, encoding='utf8').read(); m = re.search(r'window\.DECK=', h); d, e = DEC.raw_decode(h, m.end())
    n = nn = 0
    for L in d['lessons']:
        for i, v in (content.get(L['id']) or {}).items():
            s = L['slides'][int(i)]
            s.pop('listen', None)
            if v is None: continue
            if isinstance(v, dict): s.update({k: x for k, x in v.items() if k in ('audio', 'listen')}); n += 1
            else: s['listen'] = v; n += 1
    h = h[:m.end()] + json.dumps(d, ensure_ascii=False).replace('</', '<\\/') + h[e:]
    open(p, 'w', encoding='utf8').write(patch(h))
    print('%s: %d listening slides' % (p[len(R):], n)); return p[len(R):-len('/index.html')]

if __name__ == '__main__':
    cdir = sys.argv[1]; gs = [int(x) for x in sys.argv[2:]] or sorted(int(re.search(r'g(\d+)\.json', f).group(1)) for f in glob.glob(os.path.join(cdir, 'g[0-9][0-9].json')))
    done = []
    for g in gs:
        r = build(g, json.load(open(os.path.join(cdir, 'g%02d.json' % g), encoding='utf8')))
        if r: done.append(r.rsplit('/', 1)[0])
    if done:
        sys.argv = [''] + sorted(set(done)); __import__('add_lesson_links').main()
