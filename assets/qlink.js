/* Prep pages: the lesson-games link appended to «ملاحظات ضمن خطة الدراسة الأسبوعية» (tools/build_quiz.py) becomes clickable.
   Only the rendered text changes; copy buttons still copy the plain text with the full link for Noor.
   Some pages wrap Latin runs in their own spans, so a link may be split over several text nodes: it is stitched into one <a>. */
(function(){
  var RE=/https:\/\/afuq-edu\.github\.io\/afuq\/q\/[^\s<>"'،]+/g, FULL=/https:\/\/afuq-edu\.github\.io\/afuq\/q\/\S+/, busy=false;
  var SKIP={A:1,TEXTAREA:1,SCRIPT:1,STYLE:1,BUTTON:1,INPUT:1,OPTION:1,SELECT:1};
  function texts(el){ /* text nodes under el that are not inside a link or a control */
    var out=[], w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
      for(var p=n.parentNode;p&&p!==el.parentNode;p=p.parentNode){ if(SKIP[p.nodeName]) return NodeFilter.FILTER_REJECT; }
      return NodeFilter.FILTER_ACCEPT; }}), n;
    while((n=w.nextNode())) out.push(n);
    return out;
  }
  function link(url){
    var a=document.createElement('a'); a.href=url; a.target='_blank'; a.rel='noopener'; a.textContent=url;
    a.style.cssText='color:#1F6FB2;text-decoration:underline;font-weight:700;direction:ltr;unicode-bidi:isolate;word-break:break-all';
    return a;
  }
  function fixIn(el){
    var ns=texts(el); if(!ns.length) return;
    var all='', pos=[]; ns.forEach(function(n){ pos.push(all.length); all+=n.nodeValue; });
    var ms=[], m; RE.lastIndex=0; while((m=RE.exec(all))) ms.push([m.index,m.index+m[0].length,m[0]]);
    for(var k=ms.length-1;k>=0;k--){
      var s=ms[k][0], e=ms[k][1], first=-1;
      for(var i=0;i<ns.length;i++){
        var a0=pos[i], v=ns[i].nodeValue, a1=a0+v.length; if(a1<=s||a0>=e) continue;
        var from=Math.max(s-a0,0), to=Math.min(e-a0,v.length);
        if(first<0){ first=i; var rest=document.createTextNode(v.slice(to)); ns[i].nodeValue=v.slice(0,from);
          ns[i].parentNode.insertBefore(rest,ns[i].nextSibling); ns[i].parentNode.insertBefore(link(ms[k][2]),rest); }
        else ns[i].nodeValue=v.slice(0,from)+v.slice(to);
      }
    }
  }
  function run(){
    if(busy) return; busy=true;
    try{
      var cand=[];   /* the smallest elements whose text holds a whole link */
      Array.prototype.forEach.call(document.body.querySelectorAll('*'),function(el){
        if(SKIP[el.nodeName]||el.textContent.indexOf('/afuq/q/')<0) return;
        for(var c=el.firstElementChild;c;c=c.nextElementSibling){ if(!SKIP[c.nodeName]&&FULL.test(c.textContent)) return; }
        cand.push(el);
      });
      cand.forEach(fixIn);
    }finally{ busy=false; }
  }
  var t=0; function soon(){ clearTimeout(t); t=setTimeout(run,60); }
  function start(){ run(); new MutationObserver(soon).observe(document.body,{childList:true,subtree:true,characterData:true}); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
