/* Shared pieces of the homework games: theme, sound, read-aloud, result screen with a certificate. */
(function(){
  var css='\
:root{--bg:#F3F6FB;--card:#FFFFFF;--ink:#16213A;--muted:#5B6782;--line:#DCE3EE;--brand:#2F6FB3;--brand-ink:#FFFFFF;--ok:#1F9D55;--okbg:#E3F6EA;--bad:#D64545;--badbg:#FBE7E7;--gold:#E8A317}\
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0F1626;--card:#18223A;--ink:#E8EDF7;--muted:#9AA6C2;--line:#2B3756;--brand:#6EA8FF;--brand-ink:#0F1626;--ok:#3DD47F;--okbg:#12301F;--bad:#FF6B6B;--badbg:#3A1A1E;--gold:#F2B035}}\
*{box-sizing:border-box}\
body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,"Segoe UI",Tahoma,"Noto Sans Arabic",Arial,sans-serif;line-height:1.7;min-height:100vh}\
header{background:var(--card);border-bottom:1px solid var(--line)}\
.top{max-width:720px;margin:0 auto;padding:12px 16px;display:flex;align-items:center;gap:12px}\
.logo{width:44px;height:44px;border-radius:12px;background:var(--brand);color:var(--brand-ink);display:grid;place-items:center;font-size:22px;font-weight:800;flex:none}\
.top h1{margin:0;font-size:clamp(17px,4.5vw,22px);line-height:1.35}.top p{margin:0;color:var(--muted);font-size:14px}.top a{color:var(--brand);font-weight:700;text-decoration:none}\
main{max-width:720px;margin:0 auto;padding:16px 16px 48px}\
.card{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:20px 16px}\
.btn{font:inherit;font-weight:800;font-size:20px;border:0;border-radius:16px;padding:14px 26px;background:var(--brand);color:var(--brand-ink);cursor:pointer;margin-top:12px}\
.btn.alt{background:var(--bg);color:var(--ink);border:2px solid var(--line)}\
.end{text-align:center}.stars{font-size:48px;letter-spacing:6px;margin:4px 0}.score{font-size:30px;font-weight:800;margin:0}\
.name{margin:16px 0 4px;text-align:start}.name label{font-weight:700;display:block;margin-bottom:6px}\
.name input{width:100%;font:inherit;font-size:22px;padding:12px 14px;border:3px solid var(--line);border-radius:14px;background:var(--bg);color:var(--ink)}\
.cert{display:none;margin:18px 0 0;padding:20px 16px;border:6px double var(--gold);border-radius:18px;text-align:center;background:var(--card)}\
.cert.on{display:block}.cert .t{font-size:28px;font-weight:800;color:var(--gold);margin:0}.cert .n{font-size:30px;font-weight:800;margin:6px 0;word-break:break-word}.cert p{margin:4px 0;font-size:19px}.cert .s{font-size:44px;margin:0}.cert .f{font-size:14px;color:var(--muted);margin-top:10px}\
.row{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-top:8px}\
.hint{color:var(--muted);font-size:14px;margin:12px 0 0;text-align:center}\
.mute{float:left;border:2px solid var(--line);background:var(--bg);border-radius:14px;padding:6px 12px;font-size:20px;cursor:pointer;color:inherit}\
@media print{header,.row,.hint,.name,.end>.stars,.end>.score,.end>.msg,.end>.btn,#game{display:none!important}body{background:#fff}.cert.on{display:block;border-color:#999;margin:0}}';
  var st=document.createElement('style'); st.textContent=css; document.head.insertBefore(st,document.head.firstChild);

  var HW=window.HW={}, AC=null, muted=false;
  try{ muted=localStorage.getItem('afuq-hw-mute')==='1'; }catch(e){}
  HW.$=function(id){ return document.getElementById(id); };
  HW.shuffle=function(a){ a=a.slice(); for(var k=a.length-1;k>0;k--){ var j=Math.floor(Math.random()*(k+1)),t=a[k]; a[k]=a[j]; a[j]=t; } return a; };
  HW.isMuted=function(){ return muted; };
  HW.setMute=function(m){ muted=!!m; try{ localStorage.setItem('afuq-hw-mute',muted?'1':'0'); }catch(e){} };
  function tone(f,d,t,v){ try{ AC=AC||new (window.AudioContext||window.webkitAudioContext)(); var o=AC.createOscillator(),g=AC.createGain(); o.type=t||'sine'; o.frequency.value=f; g.gain.value=v||.12; o.connect(g); g.connect(AC.destination); var n=AC.currentTime; g.gain.setValueAtTime(v||.12,n); g.gain.exponentialRampToValueAtTime(.0001,n+d); o.start(n); o.stop(n+d); }catch(e){} }
  HW.sound=function(k){ if(muted) return; if(k==='ok'){ tone(660,.12); setTimeout(function(){ tone(880,.18); },110); } else if(k==='no'){ tone(200,.28,'sawtooth',.08); } else if(k==='tick'){ tone(500,.05,'square',.05); } else if(k==='win'){ [523,659,784,1047].forEach(function(f,i){ setTimeout(function(){ tone(f,.2); },i*130); }); } };
  HW.speak=function(text){ try{ speechSynthesis.cancel(); var u=new SpeechSynthesisUtterance(text); u.lang=window.HW_LANG||'ar'; u.rate=.85; speechSynthesis.speak(u); }catch(e){} };
  HW.canSpeak='speechSynthesis' in window;
  HW.stars=function(c,n){ return c>=n*0.9?3:c>=n*0.6?2:1; };

  /* o: {mount, correct, total, points, title, sub, onAgain} */
  HW.end=function(o){
    var m=o.mount, st=HW.stars(o.correct,o.total), star=new Array(st+1).join('⭐');
    var msg=st===3?'ممتاز! أنت رائع':st===2?'جيد جدًا، واصل التقدم':'حاول مرة أخرى لتحصل على نجوم أكثر';
    m.className='card end'; m.hidden=false;
    m.innerHTML='<div class="stars"></div><p class="score"></p><p class="msg" style="font-size:20px;margin:6px 0"></p>'+
      '<div class="name"><label for="nm">اكتب اسمك لتظهر شهادة الإنجاز:</label><input id="nm" maxlength="30" autocomplete="name" placeholder="اسمي"></div>'+
      '<div class="cert" id="cert"><p class="t">🏅 شهادة إنجاز</p><p>تُمنح الطالبة / الطالب</p><p class="n" id="cn"></p><p class="ct"></p><p class="s"></p><p class="cc" style="font-weight:800"></p><p class="cd"></p><p class="f"></p></div>'+
      '<div class="row"><button class="btn" id="show" type="button">عرض الشهادة</button><button class="btn alt" id="prt" type="button" hidden>🖨 طباعة الشهادة</button><button class="btn alt" id="again" type="button">↻ العب من جديد</button></div>'+
      '<p class="hint" id="shot" hidden>للتسليم: صوّر الشهادة (لقطة شاشة) وأرفقها في منصة نور.</p>';
    m.querySelector('.stars').textContent=star;
    m.querySelector('.score').textContent='نتيجتك: '+o.correct+' من '+o.total+(o.points!=null?' · '+o.points+' نقطة':'');
    m.querySelector('.msg').textContent=msg;
    var nm=HW.$('nm'); try{ nm.value=localStorage.getItem('afuq-hw-name')||''; }catch(e){}
    function cert(){
      var n=nm.value.trim(); if(!n){ nm.focus(); nm.style.borderColor='var(--bad)'; return; }
      nm.style.borderColor=''; try{ localStorage.setItem('afuq-hw-name',n); }catch(e){}
      HW.$('cn').textContent=n; m.querySelector('.ct').textContent='على إتمام واجب «\u2068'+o.title+'\u2069»';
      m.querySelector('.s').textContent=star; m.querySelector('.cc').textContent='الدرجة: '+o.correct+' من '+o.total+(o.points!=null?' · النقاط: '+o.points:'');
      var d=''; try{ d=new Date().toLocaleDateString('ar-OM',{year:'numeric',month:'long',day:'numeric'}); }catch(e){ d=new Date().toDateString(); }
      m.querySelector('.cd').textContent=d; m.querySelector('.f').textContent='منصة أفق التعليمية · '+o.sub;
      HW.$('cert').classList.add('on'); HW.$('prt').hidden=false; HW.$('shot').hidden=false; HW.$('show').hidden=true;
      HW.$('cert').scrollIntoView({behavior:'smooth',block:'center'});
    }
    HW.$('show').onclick=cert; HW.$('prt').onclick=function(){ window.print(); }; HW.$('again').onclick=o.onAgain;
    nm.addEventListener('keydown',function(e){ if(e.key==='Enter') cert(); });
    HW.sound('win'); window.scrollTo(0,0);
  };
})();
