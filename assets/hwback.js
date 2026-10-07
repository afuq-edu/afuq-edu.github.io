/* A published activity link (race / catch / activity) opened directly shows no way back to the other methods;
   the back link stays only when the page was reached from its own lesson page. */
(function(){
  var m=/^(\/\d+\/[a-z]+\/homework\/[^\/]+\/)(?:race|catch|activity)\/?(?:index\.html)?$/.exec(location.pathname); if(!m) return;
  var fromLesson=false; try{ var r=new URL(document.referrer); fromLesson=r.origin===location.origin && r.pathname.replace(/index\.html$/,'')===m[1]; }catch(e){}
  if(fromLesson) return;
  function hide(){
    Array.prototype.forEach.call(document.querySelectorAll('header a[href="../"]'),function(a){
      var p=a.parentNode; if(!p) return; a.parentNode.removeChild(a);
      if(p.tagName==='P') p.innerHTML=p.innerHTML.replace(/^\s*·\s*/,'');
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',hide); else hide();
})();
