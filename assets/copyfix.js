/* منصة أفق — توحيد النص المنسوخ
   Every copy on a prep page goes through clean(): HTML and tables become ordered lines,
   tabs and stray spaces are removed, and blank lines are limited to one between blocks.
   It wraps navigator.clipboard.writeText, the textarea + execCommand('copy') fallback,
   the prompt() fallback, and manual selection copies (Ctrl+C / long-press). */
(function () {
  'use strict';
  if (window.__afuqCopyFix) return;
  window.__afuqCopyFix = true;

  var BLOCK = /^(ADDRESS|ARTICLE|ASIDE|BLOCKQUOTE|DD|DIV|DL|DT|FIELDSET|FIGCAPTION|FIGURE|FOOTER|FORM|H[1-6]|HEADER|HR|LI|MAIN|NAV|OL|P|PRE|SECTION|TABLE|TBODY|THEAD|TFOOT|TR|UL)$/;

  function cellText(td) { return squash(walk(td)).replace(/\n+/g, ' — '); }

  function tableText(tbl) {
    var rows = [].slice.call(tbl.querySelectorAll('tr')).filter(function (r) { return r.closest('table') === tbl; });
    if (!rows.length) return '';
    var head = null, start = 0;
    var first = rows[0].children;
    var allTh = first.length && [].every.call(first, function (c) { return c.tagName === 'TH'; });
    if (allTh && rows.length > 1) { head = [].map.call(first, cellText); start = 1; }
    var out = [];
    for (var i = start; i < rows.length; i++) {
      var cells = [].map.call(rows[i].children, cellText).filter(function (x, k) { return x || (head && head[k]); });
      if (!cells.length) continue;
      if (head && head.length === rows[i].children.length && head.length > 2) {
        // Wide table with headers: one block per row, "header: value" per line.
        var block = [];
        [].forEach.call(rows[i].children, function (c, k) {
          var v = cellText(c); if (!v) return;
          block.push(head[k] ? head[k] + ': ' + v : v);
        });
        out.push(block.join('\n'));
      } else {
        // Narrow table (2 columns or no headers): one line per row.
        out.push(cells.filter(Boolean).join(' — '));
      }
    }
    var wide = head && head.length > 2;
    return '\n' + out.join(wide ? '\n\n' : '\n') + '\n';
  }

  function walk(node) {
    var s = '';
    [].forEach.call(node.childNodes, function (n) {
      if (n.nodeType === 3) {
        var pre = false;
        if (n.parentElement && n.parentElement.isConnected) {
          try { pre = /^pre/.test(getComputedStyle(n.parentElement).whiteSpace); } catch (e) {}
        }
        s += pre ? n.nodeValue.replace(/[ \t]+/g, ' ') : n.nodeValue.replace(/[ \t\r\n]+/g, ' ');
        return;
      }
      if (n.nodeType !== 1) return;
      var t = n.tagName;
      if (n.isConnected) { try { if (getComputedStyle(n).display === 'none') return; } catch (e) {} }
      if (t === 'SCRIPT' || t === 'STYLE' || t === 'BUTTON' || t === 'TEMPLATE') return;
      if (t === 'BR') { s += '\n'; return; }
      if (t === 'TABLE') { s += tableText(n); return; }
      if (t === 'LI') {
        var ol = n.parentElement && n.parentElement.tagName === 'OL';
        var idx = ol ? [].indexOf.call(n.parentElement.children, n) + 1 : 0;
        s += '\n' + (ol ? idx + '. ' : '• ') + walk(n).trim() + '\n';
        return;
      }
      var inner = walk(n);
      s += BLOCK.test(t) ? '\n' + inner + '\n' : inner;
    });
    return s;
  }

  function htmlToText(html) {
    try {
      var doc = new DOMParser().parseFromString('<div>' + html + '</div>', 'text/html');
      return walk(doc.body.firstChild);
    } catch (e) { return html.replace(/<[^>]+>/g, ' '); }
  }

  function squash(t) {
    return String(t)
      .replace(/\r\n?/g, '\n')
      .replace(/[\u00a0\u2007\u202f]/g, ' ')
      .replace(/[\u200b\ufeff\u2066-\u2069]/g, '')
      .replace(/\t+/g, ' — ')
      .split('\n').map(function (l) { return l.replace(/ {2,}/g, ' ').trim(); }).join('\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  var TAG = /<\/?(table|thead|tbody|tr|td|th|br|p|div|span|b|strong|i|em|u|ol|ul|li|h[1-6]|small|sup|sub|section)\b[^>]*>/i;

  /* ---------- field context: which card's copy button was pressed ---------- */
  var COPY_BTN = /^[^\u0621-\u064Aa-zA-Z]*(نسخ|انسخ|تم النسخ|Copy|Copied)/;
  function isCopyBtn(b) { return b && b.tagName === 'BUTTON' && COPY_BTN.test(b.textContent || ''); }
  function cardOf(btn) {
    var c = btn;
    while (c.parentElement) {
      var n = [].filter.call(c.parentElement.querySelectorAll('button'), isCopyBtn).length;
      if (n > 1) break;
      c = c.parentElement;
    }
    return c;
  }
  function titleOf(card) {
    var lines = (card.innerText || '').split('\n');
    for (var i = 0; i < lines.length; i++) {
      var x = lines[i].replace(/^[\s\d٠-٩]*(البند\s*[\d٠-٩]+)?/, '').trim();
      if (x && !COPY_BTN.test(x)) return x;
    }
    return '';
  }
  var ctx = null;
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest && e.target.closest('button');
    if (isCopyBtn(b)) { var c = cardOf(b); ctx = { card: c, title: titleOf(c), at: Date.now() }; }
  }, true);
  function currentCtx() { return ctx && Date.now() - ctx.at < 5000 ? ctx : null; }

  /* ---------- outcome levels ---------- */
  var LV = '(تذكر|فهم|تطبيق|تحليل|تقييم|إبداع|ابتكار|تركيب)';
  var reLv = new RegExp('(?:←\\s*\\(?|:\\s*|\\(\\s*|—\\s*|-\\s*)' + LV + '\\)?\\s*$');
  var reLvHead = new RegExp('^(.*?)[:：]\\s*' + LV + '\\s*(?:[—–-]\\s*(.+)|\\((.+)\\))?$');
  var D = '[\\d٠-٩]+';
  function sections(text) {
    var out = [{ head: null, lines: [] }];
    text.split('\n').forEach(function (l) {
      var t = l.trim(), m = t.match(/^الحصة\s+[\d٠-٩]+/);
      if (m) {
        // "الحصة 1:1. نص المخرج" → heading + first item on its own line
        var rest = t.slice(m[0].length), k = rest.search(/(?:^|[:\s])[\d٠-٩]+[.)]\s/);
        if (k >= 0) {
          var cut = m[0].length + k + (/[:\s]/.test(rest.charAt(k)) ? 1 : 0);
          out.push({ head: t.slice(0, cut).trim(), lines: [t.slice(cut).trim()] });
        } else out.push({ head: t, lines: [] });
      } else out[out.length - 1].lines.push(l);
    });
    if (!out[0].lines.join('').trim() && out.length > 1) out.shift();
    return out;
  }
  function parseOutcomes(lines) {
    var map = {}, seq = 0;
    // Some pages show the whole list on one line: split it at "2." / "٣)" / "مخرج تعليمي آخر:".
    lines = [].concat.apply([], lines.map(function (l) {
      return l.split(new RegExp('\\s+(?=(?:' + D + ')[.)]\\s|(?:ال)?مخرج\\s+(?:تعليمي\\s+)?(?:ال)?آخر\\s*[:：])'));
    }));
    var pending = null; // "المخرج 1" / "مخرج آخر" on its own line, text on the next line
    lines.forEach(function (l) {
      l = l.trim(); if (!l) return;
      var m;
      if (pending) { map[pending] = l; if (pending !== 'other') seq = +pending; pending = null; return; }
      if ((m = l.match(new RegExp('^المخرج\\s*\\(?(' + D + ')\\)?\\s*[:：]?$')))) { pending = toLatin(m[1]); return; }
      if (/^(?:ال)?مخرج\s+(?:تعليمي\s+)?(?:ال)?آخر\s*[:：]?$/.test(l)) { pending = 'other'; return; }
      if ((m = l.match(/^(?:ال)?مخرج\s+(?:تعليمي\s+)?(?:ال)?آخر\s*[:：]\s*(.+)$/))) { map.other = m[1].trim(); return; }
      if ((m = l.match(new RegExp('^(?:المخرج\\s*)?\\(?(' + D + ')\\)?\\s*[.)\\-:]\\s*(.+)$')))) {
        var txt = m[2].trim();
        var oth = /\s*[(\[–—-]?\s*مخرج\s+تعليمي\s+آخر\s*[)\]]?\s*$/;
        if (oth.test(txt)) { map.other = txt.replace(oth, ''); return; }
        map[toLatin(m[1])] = txt; seq = +toLatin(m[1]); return;
      }
      if ((m = l.match(/^[•\-–*]\s*(.+)$/))) { seq++; map[String(seq)] = m[1].trim(); }
    });
    return map;
  }
  function toLatin(s) { return String(s).replace(/[٠-٩]/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.indexOf(d); }); }
  function outcomesFromPage() {
    var btns = [].filter.call(document.querySelectorAll('button'), isCopyBtn);
    for (var i = 0; i < btns.length; i++) {
      var card = cardOf(btns[i]), t = titleOf(card);
      if (/المخرجات|نواتج التعلم/.test(t) && !/مستوى|المستوى/.test(t)) {
        var txt = squash(walk(card)).split('\n');
        var k = txt.findIndex(function (x) { return x.indexOf(t) >= 0; });
        return sections(txt.slice(k + 1).join('\n'));
      }
    }
    return null;
  }
  function fixLevels(text) {
    var secs = sections(text), outs = null, changed = false;
    var res = secs.map(function (sec, si) {
      var seq = 0, lines = sec.lines.map(function (raw) {
        var l = raw.trim(); if (!l) return raw;
        var key = null, lvl = null, inline = '', digits = /[٠-٩]/.test(l) ? 'ar' : 'en', m;
        var body = l;
        if ((m = body.match(new RegExp('^(?:ال)?مخرج\\s+(?:تعليمي\\s+)?(?:ال)?آخر(?=[\\s:：(]|$)\\s*')))) { key = 'other'; body = body.slice(m[0].length); }
        else if ((m = body.match(new RegExp('^المخرج\\s*\\(?(' + D + ')\\)?\\s*')))) { key = toLatin(m[1]); body = body.slice(m[0].length); }
        else if ((m = body.match(new RegExp('^\\(?(' + D + ')\\)?\\s*[.)\\-]\\s*')))) { key = toLatin(m[1]); body = body.slice(m[0].length); }
        else if ((m = body.match(/^[•\-–*]\s*/))) { key = String(++seq); body = body.slice(m[0].length); }
        if (!key) return raw;
        if (key !== 'other') seq = +key;
        // forms: "(text…): LVL", ": LVL — text", ": LVL (text…)", "text ← (LVL)", "text: LVL", ": LVL"
        if ((m = body.match(new RegExp('^\\((.+)\\)\\s*[:：]\\s*' + LV + '\\s*$')))) { inline = m[1]; lvl = m[2]; }
        else if ((m = body.match(reLvHead)) && !m[1].trim()) { lvl = m[2]; inline = (m[3] || m[4] || '').trim(); }
        else if ((m = body.match(reLv))) { lvl = m[1]; inline = body.slice(0, m.index).replace(/^[:：]\s*/, '').trim(); }
        if (!lvl) return raw;
        inline = inline.replace(/^[:：]\s*/, '').replace(/\s*[:：←—–-]\s*$/, '').trim();
        var truncated = !inline || /…$|\.\.\.$/.test(inline);
        if (truncated) {
          if (outs === null) outs = outcomesFromPage() || [];
          var os = outs.length === secs.length ? outs[si] : (outs.length === 1 ? outs[0] : null);
          var full = os && parseOutcomes(os.lines)[key];
          if (full) inline = full;
          else inline = inline.replace(/…$|\.\.\.$/, '').trim();
        }
        var n = key === 'other' ? 'المخرج الآخر' : 'المخرج ' + (digits === 'ar' ? key.replace(/\d/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'[d]; }) : key);
        changed = true;
        return inline ? n + ': ' + inline + ' ← ' + lvl : n + ': ' + lvl;
      });
      return (sec.head ? sec.head + '\n' : '') + lines.join('\n');
    });
    return changed ? res.join('\n\n') : text;
  }

  /* ---------- lesson procedures ---------- */
  var ROLE = '(?:دور\\s+)?(المعلم|المعلمة|الطالب|الطالبة|الطلبة|الطلاب|التلميذ|التلاميذ|المتعلم|المتعلمون)';
  var reRoleLine = new RegExp('^' + ROLE + '\\s*[:：]');
  function fixProcedures(text) {
    var t = text
      .replace(/\s*\|\s*/g, '\n')
      .replace(new RegExp('([:.،؛!؟)\\]])\\s+(' + ROLE + '\\s*[:：])', 'g'), '$1\n$2');
    var lines = t.split('\n').map(function (l) {
      l = l.trim();
      var m = l.match(new RegExp('^' + ROLE + '\\s*[:：]\\s*'));
      return m ? 'دور ' + m[1] + ': ' + l.slice(m[0].length) : l;
    });
    var out = [];
    lines.forEach(function (l) {
      if (!l) { if (out.length && out[out.length - 1] !== '') out.push(''); return; }
      var prev = out.length ? out[out.length - 1] : '';
      if (prev && prev !== '' && !reRoleLine.test(l) && reRoleLine.test(prev)) out.push('');
      out.push(l);
    });
    return out.join('\n');
  }

  function fieldClean(t, c) {
    var title = c ? c.title : '';
    var lines = t.split('\n');
    var roleLines = lines.filter(function (l) { return reRoleLine.test(l.trim()); }).length;
    var roleInline = (t.match(new RegExp(ROLE + '\\s*[:：]', 'g')) || []).length;
    if (/إجراءات|سير الدرس|الأنشطة التدريسية/.test(title) || roleLines >= 2 || roleInline >= 3) t = fixProcedures(t);
    if (/مستوى|المستوى/.test(title) || new RegExp('^\\s*المخرج\\s*\\(?' + D + '\\)?\\s*[:：]\\s*' + LV + '\\s*$', 'm').test(t)) t = fixLevels(t);
    return t;
  }

  function clean(t, c) {
    if (t == null) return t;
    t = String(t);
    if (TAG.test(t)) t = htmlToText(t);
    t = squash(t)
      .replace(/[\u2066-\u2069]/g, '')
      .replace(/^[\-–*]\s+/gm, '• ');
    t = fieldClean(t, c === undefined ? currentCtx() : c);
    return squash(t);
  }
  window.afuqCleanCopy = clean;

  // 1) Async clipboard API
  var cb = navigator.clipboard;
  if (cb && cb.writeText) {
    var orig = cb.writeText.bind(cb);
    try {
      cb.writeText = function (t) { return orig(clean(t)); };
    } catch (e) {}
  }

  // 2) textarea/input + execCommand('copy') fallback
  var origExec = document.execCommand ? document.execCommand.bind(document) : null;
  if (origExec) {
    document.execCommand = function (cmd) {
      if (String(cmd).toLowerCase() === 'copy') {
        var el = document.activeElement;
        if (el && (el.tagName === 'TEXTAREA' || (el.tagName === 'INPUT' && /^(text|search|)$/i.test(el.type || '')))) {
          var c = clean(el.value);
          if (c !== el.value) {
            el.value = c;
            try { el.select(); el.setSelectionRange(0, c.length); } catch (e) {}
          }
        }
      }
      return origExec.apply(document, arguments);
    };
  }

  // 3) prompt('انسخ…', text) fallback
  var origPrompt = window.prompt;
  if (origPrompt) {
    window.prompt = function (msg, def) {
      return def === undefined ? origPrompt.call(window, msg) : origPrompt.call(window, msg, clean(def));
    };
  }

  // 4) Manual selection copy from the page (e.g. selecting a table)
  document.addEventListener('copy', function (ev) {
    var a = document.activeElement;
    if (a && (a.tagName === 'TEXTAREA' || a.tagName === 'INPUT')) return; // handled above / by the field itself
    var sel = window.getSelection && window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount || !ev.clipboardData) return;
    var box = document.createElement('div');
    for (var i = 0; i < sel.rangeCount; i++) {
      var frag = sel.getRangeAt(i).cloneContents();
      // Selecting inside a table gives rows/cells without the <table>: wrap them so they keep their structure.
      if (frag.querySelector && frag.querySelector('tr,td,th') && !frag.querySelector('table')) {
        var tbl = document.createElement('table');
        if (!frag.querySelector('tr')) { var tr = document.createElement('tr'); tr.appendChild(frag); tbl.appendChild(tr); }
        else tbl.appendChild(frag);
        box.appendChild(tbl);
      } else box.appendChild(frag);
    }
    var text = clean(squash(walk(box)));
    if (!text) return;
    ev.clipboardData.setData('text/plain', text);
    ev.preventDefault();
  }, true);
})();
