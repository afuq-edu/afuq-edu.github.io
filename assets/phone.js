/* «شاشة الهاتف» (assets/phone.css): a small gold lock on the icons of the sections this device has not opened
   (the subject portal's own unlock keys, read from its script); gold users see no locks. */
(function(){
  function on(k){
    try{if(localStorage.getItem(k)==='1')return true}catch(e){}
    try{if(sessionStorage.getItem(k)==='1')return true}catch(e){}
    try{if(new RegExp('(^|; )'+k+'=1(;|$)').test(document.cookie)||(' '+window.name+' ').indexOf(' '+k+' ')>=0)return true}catch(e){}
    return false;
  }
  function run(){
    var pre=null;
    document.querySelectorAll('script:not([src])').forEach(function(s){ var x=s.textContent.match(/return '(ofuq-[a-z0-9-]*?-)'\s*\+\s*id/); if(x) pre=x[1]; });
    if(!pre) return;
    document.querySelectorAll('.card[data-id]').forEach(function(c){
      if(c.querySelector('.tag') && !(on(pre+c.getAttribute('data-id'))||on('afuq-all'))) c.classList.add('ph-lock');
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',run); else run();
})();
