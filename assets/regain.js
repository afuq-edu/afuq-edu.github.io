/* «استعادة الوصول» (owner, 2026-11-16: «أي واحد تظهر له هذه الأقسام اجعل فتحها ممكنًا»). A subscriber with a private link (/p/?pl=…) who sees a gold-lock
   dialog («هذا القسم مخصص للباقة الذهبية») — a new browser or app, cleared site data, a device that was replaced — gets a button in that dialog that
   opens his private link again (it re-registers this device and unlocks his subjects; if the link is full it offers to replace the oldest device)
   and shows his package page (the portal pages are outside a private-link package, so he cannot be sent back to them). The link is remembered on the device (afuq-pl-last); without one he pastes it.
   Usage: <script src="/assets/regain.js" defer></script> in the portal pages (tools/add_regain.py). Adds only a block inside the dialog. */
(function () {
  'use strict';
  var KEY = 'afuq-pl-last', MARK = 'afuqRegain';
  function rd(k) { var v = ''; try { v = localStorage.getItem(k) || ''; } catch (e) {}
    if (!v) { try { var m = new RegExp('(?:^|; )' + k + '=([^;]*)').exec(document.cookie); if (m) v = decodeURIComponent(m[1]); } catch (e) {} } return v; }
  function go(code) { location.href = '/p/?pl=' + code; }
  function codeOf(t) { var m = /(?:[#?&]pl=?|#pl)([0-9a-f]{14})/i.exec(t || '') || /^([0-9a-f]{14})$/i.exec((t || '').trim()); return m ? m[1].toLowerCase() : ''; }
  function addTo(d) {
    if (d.querySelector('.' + MARK) || !/هذا القسم مخصص للباقة الذهبية/.test(d.textContent)) return;
    var code = /^[0-9a-f]{14}$/.test(rd(KEY)) ? rd(KEY) : '';
    var box = document.createElement('div'); box.className = MARK;
    box.setAttribute('style', 'margin:12px 0 4px;padding:12px;border:1px dashed #9DB7D5;border-radius:14px;background:rgba(47,111,179,.07);text-align:center;direction:rtl');
    var st = 'display:block;width:100%;border:0;border-radius:12px;padding:11px 14px;font:inherit;font-weight:700;background:#2F6FB3;color:#fff;cursor:pointer';
    var p = document.createElement('p'); p.setAttribute('style', 'margin:0 0 8px;font-size:14px;line-height:1.7');
    if (code) {
      p.textContent = 'هل أنت مشترك ولديك رابط خاص؟ استعد الوصول لتُفتح لك أقسامك.';
      var b = document.createElement('button'); b.type = 'button'; b.setAttribute('style', st); b.textContent = '🔓 استعادة الوصول برابطي الخاص';
      b.onclick = function () { go(code); }; box.append(p, b);
    } else {
      p.textContent = 'هل أنت مشترك ولديك رابط خاص؟ الصقه هنا لتُفتح لك أقسامك.';
      var i = document.createElement('input'); i.type = 'text'; i.placeholder = 'الصق رابطك الخاص'; i.setAttribute('dir', 'ltr');
      i.setAttribute('style', 'width:100%;font:inherit;font-size:15px;padding:10px;border:2px solid #DCE3EE;border-radius:12px;margin:0 0 8px;text-align:left');
      var b2 = document.createElement('button'); b2.type = 'button'; b2.setAttribute('style', st); b2.textContent = '🔓 استعادة الوصول';
      b2.onclick = function () { var c = codeOf(i.value); if (c) go(c); else { i.style.borderColor = '#D64545'; i.focus(); } };
      box.append(p, i, b2);
    }
    var row = d.querySelector('.row'); if (row && row.parentNode) row.parentNode.insertBefore(box, row); else d.appendChild(box);
  }
  function scan() { [].forEach.call(document.querySelectorAll('dialog[open]'), addTo); }
  new MutationObserver(scan).observe(document.documentElement, { subtree: true, attributes: true, attributeFilter: ['open'] });
  if (document.readyState !== 'loading') scan(); else document.addEventListener('DOMContentLoaded', scan);
})();
