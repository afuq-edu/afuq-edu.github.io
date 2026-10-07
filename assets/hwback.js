/* Activity pages (race / catch / activity) never show the "back to methods" link, so a student cannot reach the other activities. */
(function(){
  var m=/^(\/\d+\/[a-z]+\/homework\/[^\/]+\/)(?:race|catch|activity)\/?(?:index\.html)?$/.exec(location.pathname); if(!m) return;
  function hide(){
    Array.prototype.forEach.call(document.querySelectorAll('header a[href="../"]'),function(a){
      var p=a.parentNode; if(!p) return; a.parentNode.removeChild(a);
      if(p.tagName==='P') p.innerHTML=p.innerHTML.replace(/^\s*·\s*/,'');
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',hide); else hide();
})();
