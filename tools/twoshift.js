/* Two-shift version of a prep page's data (النشرة التوجيهية 2026/2027): fewer periods per lesson, same lessons and weeks.
   node tools/twoshift.js in.json out.json — in: {pages:[{rel, t1, t2, lits:[data…]}]}, out: {pages:[{rel, lits:[data|null], report}]}.
   For every lesson (an object with a list of periods, each period holding the 10 Noor fields), consecutive periods are merged
   so the page's total goes from t1 (one shift) to t2 (two shifts), shared out in proportion to each lesson's periods (at least
   one each). A merged period: outcomes, levels and questions joined and renumbered; strategies, resources, concepts and notes
   joined without repeats; the first period's warm-up; the procedures of all its periods (the first one's warm-up, every
   period's activities, the last one's closing) with their times rescaled to 40 minutes (assets/shift.js then makes them 35).
   The lesson's merged («مدمج») fields are rebuilt from the new periods. Called by tools/add_twoshift.py. */
'use strict';
const fs = require('fs');
const AR = '٠١٢٣٤٥٦٧٨٩';
const toN = (s) => +String(s).replace(/[٠-٩]/g, (d) => AR.indexOf(d));
const like = (n, orig) => (/[٠-٩]/.test(orig) ? String(n).replace(/\d/g, (d) => AR[d]) : String(n));
const isFields = (v) => (Array.isArray(v) && v.length >= 9 && v.length <= 11 && v.filter((x) => typeof x === 'string').length >= 9) ||
  (v && typeof v === 'object' && !Array.isArray(v) && Object.values(v).length >= 9 && Object.values(v).length <= 11 && Object.values(v).filter((x) => typeof x === 'string').length >= 9);
const COMB = new Set(['c', 'C', 'comb', 'combined', 'merged', 'mer', 'm']);

/* ---------------- lessons */
function findLessons(root) {
  const out = [];
  (function walk(o) {
    if (Array.isArray(o)) { o.forEach(walk); return; }
    if (!o || typeof o !== 'object') return;
    for (const k of Object.keys(o)) {
      const v = o[k];
      if (Array.isArray(v) && v.length && v.every((p) => p && typeof p === 'object' && !Array.isArray(p))) {
        const fk = Object.keys(v[0]).filter((x) => !COMB.has(x) && isFields(v[0][x]));
        if (fk.length && v.every((p) => fk.every((x) => isFields(p[x])))) { out.push({ lesson: o, key: k, fk }); continue; }
      }
      walk(v);
    }
  })(root);
  return out;
}
function allocate(ns, target) {
  const tot = ns.reduce((a, b) => a + b, 0);
  if (target >= tot) return ns.slice();
  const raw = ns.map((n) => (n * target) / tot);
  const r = raw.map((x, i) => Math.min(ns[i], Math.max(1, Math.floor(x))));
  let left = target - r.reduce((a, b) => a + b, 0);
  const ord = raw.map((x, i) => [x - Math.floor(x), i]).sort((a, b) => b[0] - a[0]);
  for (let k = 0; left > 0 && k < ord.length * 3; k++) { const i = ord[k % ord.length][1]; if (r[i] < ns[i]) { r[i]++; left--; } }
  while (left < 0) { let j = -1; r.forEach((x, i) => { if (x > 1 && (j < 0 || x / ns[i] > r[j] / ns[j])) j = i; }); if (j < 0) break; r[j]--; left++; }
  return r;
}
function groupsOf(n1, n2) {
  const base = Math.floor(n1 / n2), extra = n1 % n2, g = []; let s = 0;
  for (let i = 0; i < n2; i++) { const z = base + (i < extra ? 1 : 0); g.push([s, s + z]); s += z; }
  return g;
}

/* ---------------- text helpers */
const lines = (t) => String(t || '').split('\n');
const NUMLINE = /^(\s*[-•]?\s*)([0-9٠-٩]+)(\s*[.)\-–]\s)/;
function renumber(text, re = NUMLINE) {
  let k = 0;
  return lines(text).map((l) => l.replace(re, (m, a, n, b) => a + like(++k, n) + b)).join('\n');
}
const OTHER = /^\s*[-•]?\s*(?:ال)?مخرج(?:ات)?\s+(?:تعليمي(?:ة)?\s+)?(?:ال)?آخر|^\s*(?:another|other)\s+(?:learning\s+)?outcome/i;
function mergeOutcomes(ts) {
  const main = [], other = []; let head = '';
  ts.forEach((t) => {
    let inOther = false;
    lines(t).forEach((l) => {
      if (!l.trim()) return;
      if (OTHER.test(l)) {
        inOther = true; const m = l.match(/^([^:：]*[:：])\s*(.*)$/);
        if (!head) head = m ? m[1] : l.trim();
        if (m && m[2].trim()) other.push(m[2].trim());
        return;
      }
      (inOther ? other : main).push(l);
    });
  });
  const seen = new Set(), oth = other.filter((x) => { const k = x.replace(NUMLINE, '').replace(/^[-•]\s*/, '').trim(); if (seen.has(k)) return false; seen.add(k); return true; });
  let out = renumber(main.join('\n'));
  if (oth.length) {
    const numbered = oth.some((x) => NUMLINE.test(x));
    out += '\n\n' + head + (numbered ? '\n' : (oth.length === 1 ? ' ' : '\n')) + oth.join('\n');
    out = renumber(out);
  }
  return out.trim();
}
const LVLNUM = /^(\s*[-•]?\s*(?:المخرج|Outcome|LO)\s*\(?)([0-9٠-٩]+)/i;
function mergeLevels(ts) {
  const main = [], other = [];
  ts.forEach((t) => lines(t).forEach((l) => { if (!l.trim()) return; (/الآخر|other|another/i.test(l) && !LVLNUM.test(l) ? other : main).push(l); }));
  let k = 0;
  const m = main.map((l) => (LVLNUM.test(l) ? l.replace(LVLNUM, (x, a, n) => a + like(++k, n)) : l));
  const seen = new Set(), o = other.filter((x) => (seen.has(x.trim()) ? false : (seen.add(x.trim()), true)));
  return renumber([...m, ...o].join('\n'));
}
function mergeQuestions(ts) {
  const parts = ts.map((t) => String(t || '').trim()).filter(Boolean);
  let k = 0;
  return parts.join('\n\n').split('\n')
    .map((l) => l.replace(/^(\s*)([0-9٠-٩]+)(\s*[.)]\s)/, (m, a, n, b) => a + like(++k, n) + b))
    .join('\n').replace(/(^|\n)(\s*س\s*)([0-9٠-٩]+)/g, (() => { let j = 0; return (m, a, b, n) => a + b + like(++j, n); })());
}
function mergeUnion(ts) {   /* strategies, resources, concepts: items joined without repeats, numbered lists renumbered */
  const order = [], byKey = new Map();
  const put = (key, item, sep) => { if (!byKey.has(key)) { byKey.set(key, { items: [], sep }); order.push(key); } const e = byKey.get(key); if (!e.items.includes(item)) e.items.push(item); };
  ts.forEach((t) => lines(t).forEach((l) => {
    const s = l.trim(); if (!s) return;
    if (NUMLINE.test(l)) { put('#num', s.replace(NUMLINE, '').trim(), '\n'); return; }
    const m = s.match(/^([^:：]{2,40}[:：])\s*(.+)$/);
    const key = m ? m[1] : '', body = m ? m[2] : s;
    const sep = body.includes('،') ? '، ' : body.includes(',') && !/[؀-ۿ]/.test(body) ? ', ' : null;
    if (sep) body.split(sep === '، ' ? /\s*،\s*/ : /\s*,\s*/).forEach((x) => x && put(key, x, sep)); else put(key + '\u0000' + body, body, null);
  }));
  return order.map((key) => {
    const e = byKey.get(key);
    if (key === '#num') return e.items.map((x, i) => (i + 1) + '. ' + x).join('\n');
    if (key.includes('\u0000')) return (key.split('\u0000')[0] ? key.split('\u0000')[0] + ' ' : '') + e.items[0];
    return (key ? key + ' ' : '') + e.items.join(e.sep);
  }).join('\n');
}
function mergeNotes(ts) {
  const out = [], seen = new Set();
  ts.forEach((t) => lines(t).forEach((l) => { const s = l.trim(); if (!s) { if (out.length && out[out.length - 1] !== '') out.push(''); return; } if (seen.has(s)) return; seen.add(s); out.push(l); }));
  while (out.length && out[out.length - 1] === '') out.pop();
  /* the lesson-games link stays the last line */
  const li = out.findIndex((l) => /\/afuq\/q\//.test(l));
  if (li >= 0 && li !== out.length - 1) { const [x] = out.splice(li, 1); out.push(x); }
  return out.join('\n').replace(/\n{3,}/g, '\n\n');
}

/* ---------------- procedures */
const D = '[0-9٠-٩]+', SP = '(?:\\s|&nbsp;)*';
const UNIT = '(?:دقيقتان|دقيقتين|دقائق|دقيقة|د(?![\\u0600-\\u06FF])|minutes?|mins?\\b)';
const RXS = [
  ['full', new RegExp('\\(' + SP + '(' + D + ')' + SP + '(?:د|دقائق|دقيقة)' + SP + '[:،,]' + SP + '(?:من الدقيقة|الدقيقة)?' + SP + '(' + D + ')' + SP + '(?:إلى|–|-)' + SP + '(' + D + ')' + SP + '\\)')],
  ['range', new RegExp('(?:من الدقيقة|الدقيقة|from minute)' + SP + '⁦?(' + D + ')' + SP + '(?:إلى|حتى|to|–|-)' + SP + '(' + D + ')⁩?')],
  ['range', new RegExp('\\(' + SP + '(' + D + ')' + SP + '[–\\-]' + SP + '(' + D + ')' + SP + UNIT)],
  ['range', new RegExp('(' + D + ')' + SP + '[–\\-]' + SP + '(' + D + ')' + SP + UNIT)],
  ['dur', new RegExp('(' + D + ')' + SP + UNIT)]];
function headTokens(l) {
  const toks = [];
  for (const [k, re] of RXS) {
    const g = new RegExp(re.source, 'g'); let m;
    while ((m = g.exec(l))) {
      if (toks.some((t) => m.index < t.i + t.s.length && t.i < m.index + m[0].length)) continue;
      toks.push(k === 'full' ? { k, i: m.index, s: m[0], d: toN(m[1]), a: toN(m[2]), b: toN(m[3]) }
        : k === 'range' ? { k, i: m.index, s: m[0], a: toN(m[1]), b: toN(m[2]) } : { k, i: m.index, s: m[0], d: toN(m[1]) });
    }
  }
  return toks.sort((x, y) => x.i - y.i);
}
const ROLE = /^\s*(?:[-•–]|(?:دور\s+)?(?:المعلم|المعلمة|الطالب|الطالبة|الطلبة|الطلاب|التلميذ|التلاميذ|المتعلم)|Teacher|Pupils?|Students?|Strategy|الاستراتيجي)/;
const TOTAL = /^\s*[-–•]?\s*(?:المجموع|مجموع الزمن|مجموع زمن الحصة|مجموع زمن الأنشطة|الزمن الكلي|زمن الحصة|Total)/i;
const WARM = /التهيئة|تهيئة|التمهيد|تمهيد|الإحماء|إحماء|warm[- ]?up|lead[- ]?in|starter|opening/i;
const CLOSE = /غلق الدرس|ختام الدرس|Finishing stage|التقويم الختامي|تقويم ختامي|الغلق|الختام|الخاتمة|الإغلاق|مسابقة المجموعات|بطاقة الخروج|خطة الأسبوع|التهدئة|closure|closing|plenary|exit ticket|wrap[- ]?up|cool[- ]?down/i;
const CLOSE_HEAD = /التقويم|بطاقات? (?:ال)?خروج|الخلاصة|التلخيص|ملخص الحصة|assessment|summary|review/i;   /* a step named so (its first line) */
const isClose = (lines0) => CLOSE.test(lines0.join(' ')) || CLOSE_HEAD.test(lines0[0] || '');
function parseProc(t) {
  const L = lines(t), steps = [], pre = []; let cur = null, totals = [];
  L.forEach((l) => {
    if (TOTAL.test(l) && headTokens(l).length) { totals.push(l); return; }
    /* «1. … (5 دقائق)» (tools/proc_style.py): the time closing the line is the step's, not one mentioned inside it */
    const endT = l.match(/\((\s*[0-9٠-٩]+\s*(?:دقيقتان|دقيقتين|دقائق|دقيقة|minutes?))\)\s*$/);
    const tk = ROLE.test(l) ? [] : endT && /^\s*[0-9٠-٩]+\.\s/.test(l) ? headTokens(l).filter((x) => x.i >= l.length - endT[0].length) : headTokens(l);
    const timed = tk.filter((x) => x.k !== 'dur' || true);
    if (timed.length) { cur = { lines: [l], tk: timed }; steps.push(cur); return; }
    if (cur) cur.lines.push(l); else pre.push(l);
  });
  steps.forEach((s) => { while (s.lines.length > 1 && !s.lines[s.lines.length - 1].trim()) s.lines.pop(); });
  return { pre, steps, totals, gap: /\n\s*\n/.test(t) };
}
function durOf(s) {
  const t = s.tk, f = t.find((x) => x.k === 'full'); if (f) return f.d;
  const d = t.find((x) => x.k === 'dur'); if (d) return d.d;
  const r = t.find((x) => x.k === 'range'); if (r) return r.b - r.a + (r.a % 5 === 1 ? 1 : 0);
  return 0;
}
function scaleTo(ds, T) {
  const tot = ds.reduce((a, b) => a + b, 0) || 1;
  const raw = ds.map((x) => (x * T) / tot), r = raw.map((x) => Math.max(1, Math.floor(x)));
  let left = T - r.reduce((a, b) => a + b, 0);
  const ord = raw.map((x, i) => [x - Math.floor(x), i]).sort((a, b) => b[0] - a[0]);
  for (let k = 0; left > 0; k++) { r[ord[k % ord.length][1]]++; left--; }
  while (left < 0) { const j = r.indexOf(Math.max(...r)); r[j]--; left++; }
  return r;
}
function rewriteHead(l, tk, d, c, incl, idx, actIdx) {
  let s = l, shift = 0;
  tk.forEach((t) => {
    let vals;
    if (t.k === 'full') vals = [d, c, c + d];
    else if (t.k === 'range') vals = [c + (incl ? 1 : 0), c + d];
    else vals = [d];
    let k = 0;
    const ns = t.s.replace(/[0-9٠-٩]+/g, (n) => (k < vals.length ? like(vals[k++], n) : n))
      .replace(/([0-9٠-٩]+)(\s*)(دقائق|دقيقة)(?![؀-ۿ])/g, (m, n, sp, u) => { const v = toN(n); return n + sp + (v === 1 ? 'دقيقة' : v === 2 ? 'دقيقتان' : v <= 10 ? 'دقائق' : 'دقيقة'); })
      .replace(/([0-9٠-٩]+)(\s*)(minutes?)\b/g, (m, n, sp) => n + sp + (toN(n) === 1 ? 'minute' : 'minutes'));
    s = s.slice(0, t.i + shift) + ns + s.slice(t.i + shift + t.s.length); shift += ns.length - t.s.length;
  });
  s = s.replace(/^(\s*[◄►•]?\s*)([0-9٠-٩]+)(\s*[.)]\s*)/, (m, a, n, b) => a + like(idx, n) + b);
  s = s.replace(/^(\s*[◄►•]?\s*(?:النشاط|Activity)\s*)([0-9٠-٩]+)/, (m, a, n) => a + like(actIdx(), n));
  return s;
}
function mergeProc(ts, T = 40) {
  const P = ts.map(parseProc);
  if (P.some((p) => !p.steps.length)) return ts.map((t) => String(t || '').trim()).filter(Boolean).join('\n\n');
  /* one warm-up (the first period's) and one closing (the last period's): a later period's opening warm-up steps and an
     earlier period's closing steps (final assessment, group contest, closure / plenary…) are left out */
  let picked = [];
  P.forEach((p, i) => {
    let st = p.steps.slice();
    if (i > 0) while (st.length > 1 && WARM.test(st[0].lines[0])) st.shift();
    if (i < P.length - 1) while (st.length > 1 && isClose(st[st.length - 1].lines)) st.pop();
    picked = picked.concat(st);
  });
  const ds = picked.map(durOf);
  if (ds.some((x) => !(x > 0))) return ts.map((t) => String(t || '').trim()).filter(Boolean).join('\n\n');
  const nd = scaleTo(ds, T);
  const firstRange = picked[0].tk.find((x) => x.k === 'range');
  const incl = !!(firstRange && firstRange.a === 1);
  let c = 0, act = 0;
  const actIdx = () => ++act;
  const outSteps = picked.map((s, i) => {
    const head = rewriteHead(s.lines[0], s.tk, nd[i], c, incl, i + 1, actIdx);
    c += nd[i];
    return [head, ...s.lines.slice(1)].join('\n');
  });
  const sep = P[0].gap ? '\n\n' : '\n';
  let out = (P[0].pre.join('\n').trim() ? P[0].pre.join('\n').trim() + '\n' : '') + outSteps.join(sep);
  const tl = P.map((p) => p.totals[0]).find(Boolean);
  if (tl) out += (P[0].gap ? '\n\n' : '\n') + tl.replace(/[0-9٠-٩]+/, (n) => like(T, n));
  return out.trim();
}

/* procedures drawn as numbered steps (tools/proc_list.py, owner 2026-10-25: no tables): «1. 5 دقائق — التهيئة:» + teacher,
   «• الطالب: …» under it — the same html proc_list.py writes for one shift */
const STEP_ROW = 'margin:0;padding:10px 2px;border-bottom:1px dashed #d8d0bf;line-height:1.9';
const escT = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const PROW = 'margin:0;padding:8px 2px;border-bottom:1px dashed #d8d0bf;line-height:1.9';
function renderNew(t) {   /* the procedures style of tools/proc_style.py (render_html there draws the same) */
  const ps = [];
  String(t).split('\n\n').filter((b) => b.trim()).forEach((b) => {
    let ls = b.split('\n');
    if (/^(?:الحصة|Period)\s/.test(ls[0]) && !/^[0-9٠-٩]+\.\s/.test(ls[0])) {
      ps.push('<p class="phead" style="margin:10px 0 2px;color:#c0392b;font-weight:700">' + escT(ls[0]) + '</p>'); ls = ls.slice(1);
      if (!ls.length) return;
    }
    const m = ls[0].match(/^([0-9٠-٩]+\.)\s*(.*)$/);
    ps.push('<p class="pstep" style="' + PROW + '">' + (m ? '<b>' + escT(m[1]) + '</b> ' + escT(m[2]) : escT(ls[0])) +
      ls.slice(1).map((x) => '<br><span style="opacity:.8">' + escT(x) + '</span>').join('') + '</p>');
  });
  return '<div class="plist">' + ps.join('') + '</div>';
}
function renderSteps(t) {   /* numbered items «1. label: text» with «• …» lines under them; other lines stay paragraphs */
  if (/^[0-9٠-٩]+\.\s.*\([0-9٠-٩]+ (?:دقيقة|دقيقتان|دقائق|minutes?)\)\s*$/m.test(t)) return renderNew(t);
  const out = []; let cur = null;
  lines(t).forEach((l) => {
    const s = l.trim(); if (!s) return;
    if (/^[0-9٠-٩]+[.)]\s/.test(s)) {
      const m = s.match(/^([0-9٠-٩]+[.)](?:\s*[^:：]{0,70}?[:：])?)\s*(.*)$/);
      cur = { lab: m[1], te: m[2], st: [] }; out.push(cur); return;
    }
    if (cur && /^•/.test(s)) { cur.st.push(s); return; }
    if (cur) { cur.te += ' ' + s; return; }
    out.push({ p: s });
  });
  if (!out.some((x) => x.lab)) return null;
  return '<div class="plist">' + out.map((x) => (x.p ? '<p>' + escT(x.p) + '</p>' : '<p class="pstep" style="' + STEP_ROW + '"><b>' + escT(x.lab) + '</b> ' + escT(x.te) +
    x.st.map((y) => '<br><span style="opacity:.85">' + escT(y) + '</span>').join('') + '</p>')).join('') + '</div>';
}

/* ---------------- one period from a group */
const HASNUM = (v, n) => (typeof v === 'number' && v === n) || (typeof v === 'string' && /^[0-9٠-٩]+$/.test(v.trim()) && toN(v) === n);
/* how each of the 10 fields is merged, in the standard Noor order (a page with another order passes its own) */
const KINDS = ['out', 'lvl', 'union', 'union', 'union', 'first', 'proc', 'q', 'q', 'notes'];
/* outcome times «… (10 دقائق)» (tools/outcome_times.py): a merged period's outcomes share its 40 minutes again, part by part */
const OTIME = /\(([0-9٠-٩]+) (دقيقة|دقيقتان|دقائق|minutes?)\)(?=[ \t]*(?:\n|$|<))/g;
const OSEG = /^\s*(?:<div class="psub">)?(?:Period|Lesson|الحصة|حصة)\s*[0-9٠-٩]+\b(?![.)])/i;
function retime(t, T = 40) {
  if (typeof t !== 'string' || !/\((?:[0-9٠-٩]+) (?:دقيقة|دقيقتان|دقائق|minutes?)\)/.test(t)) return t;
  const parts = t.split(/(?=^\s*(?:Period|Lesson|الحصة|حصة)\s*[0-9٠-٩]+\b(?![.)]))|(?=<div class="psub">)/im);
  return parts.map((p) => {
    const ms = []; p.replace(OTIME, (m, n) => { ms.push(toN(n)); return m; });
    if (ms.length < 1 || ms.reduce((a, b) => a + b, 0) === T) return p;
    const nd = ms.length * 5 <= T && ms.length > 1 ? (() => { const r = scaleTo(ms, T / 5 | 0).map((x) => x * 5); r[r.length - 1] += T - r.reduce((a, b) => a + b, 0); return r; })() : scaleTo(ms, T);
    let k = 0;
    return p.replace(OTIME, (m, n, u) => { const d = nd[k++]; return '(' + d + ' ' + (/minute/.test(u) ? (d === 1 ? 'minute' : 'minutes') : (d === 1 || d > 10 ? 'دقيقة' : d === 2 ? 'دقيقتان' : 'دقائق')) + ')'; });
  }).join('');
}
function mergeText(kind, ts) {
  if (kind === 'out') return retime(mergeOutcomes(ts));
  if (kind === 'lvl') return mergeLevels(ts);
  if (kind === 'union') return mergeUnion(ts);
  if (kind === 'first') return ts.find((x) => x.trim()) || ts[0];
  if (kind === 'last') return ts.slice().reverse().find((x) => x.trim()) || ts[ts.length - 1];
  if (kind === 'q') return mergeQuestions(ts);
  if (typeof kind === 'number') return mergeProc(ts, kind);
  if (kind === 'proc') return mergeProc(ts);
  return mergeNotes(ts);
}
function mergeFields(list, kinds = KINDS) {   /* list: field arrays (or objects) of the group's periods */
  const arr = Array.isArray(list[0]);
  const keys = arr ? list[0].map((_, i) => i) : Object.keys(list[0]);
  const get = (f, i) => (arr ? f[i] : f[keys[i]]);
  const n = keys.length, out = arr ? [] : {};
  for (let i = 0; i < n; i++) {
    const ts = list.map((f) => get(f, i)).filter((x) => typeof x === 'string');
    let v;
    if (ts.length !== list.length) v = get(list[0], i);
    else if (/<(?:div|p|br|span|ul|li|b)\b/i.test(ts.join(''))) v = kinds[i] === 'out' ? retime(ts.join('')) : ts.join('');
    else v = mergeText(kinds[i] || 'notes', ts);
    if (arr) out.push(v); else out[keys[i]] = v;
  }
  return out;
}
const LABEL = /(الحصة\s*)([0-9٠-٩]+)(\s*من\s*)([0-9٠-٩]+)/g;
const TOPIC = /^(axis|axisT|ax|focus|topic|title|h|head|label|t|name)$/;
function mergePeriods(ps, fk, gi, n2, n1) {
  const p0 = ps[0], out = {};
  for (const k of Object.keys(p0)) {
    if (k === '__i') continue;
    if (fk.includes(k)) { out[k] = mergeFields(ps.map((p) => p[k])); continue; }
    const v = p0[k];
    if (/^(n|np|of|count|total|nPer)$/.test(k) && HASNUM(v, n1) && !HASNUM(v, ps[0].__i + 1)) { out[k] = typeof v === 'number' ? n2 : like(n2, v); continue; }
    if (HASNUM(v, ps[0].__i + 1)) { out[k] = typeof v === 'number' ? gi + 1 : like(gi + 1, v); continue; }
    if (typeof v === 'string') {
      if (LABEL.test(v)) { LABEL.lastIndex = 0; out[k] = v.replace(LABEL, (m, a, x, b, y) => a + like(gi + 1, x) + b + like(n2, y)); continue; }
      LABEL.lastIndex = 0;
      if (TOPIC.test(k)) { const u = []; ps.forEach((p) => { const s = typeof p[k] === 'string' ? p[k].trim() : ''; if (s && !u.includes(s)) u.push(s); }); out[k] = u.join(' + '); continue; }
    }
    out[k] = v;
  }
  for (const [a, b] of [['html', 'plain'], ['h', 't']]) {
    if (!Array.isArray(out[a]) || !Array.isArray(out[b])) continue;
    out[a].forEach((v, i) => { if (typeof v === 'string' && v.includes('class="plist"') && typeof out[b][i] === 'string') { const r = renderSteps(out[b][i]); if (r) out[a][i] = r; } });
  }
  return out;
}
/* the lesson's merged («مدمج») fields: one «الحصة N» section per period → rebuilt from the new periods */
const SEC = /^(\s*(?:الحصة|Period)\s*)([0-9٠-٩]+)(.*)$/;
function rebuildCombined(text, n1, groups, newFields, i) {
  if (typeof text !== 'string') return text;
  const L = lines(text), heads = [];
  L.forEach((l, j) => { const m = l.match(SEC); if (m && toN(m[2]) === heads.length + 1) heads.push({ j, m }); });
  if (heads.length !== n1) return text;
  return groups.map(([s], g) => {
    const m = heads[s].m;   /* «الحصة 1: عنوان» / «الحصة 1 (عنوان):» / «Period 1:» — the group's first period's heading, renumbered */
    return m[1] + like(g + 1, m[2]) + m[3] + '\n' + newFields[g];
  }).join('\n\n');
}
function fixLessonMeta(lesson, key, n1, n2) {
  for (const k of Object.keys(lesson)) {
    if (k === key || COMB.has(k)) continue;
    const v = lesson[k];
    if ((k === 'n' || k === 'np' || k === 'count' || k === 'num' || k === 'periodsCount') && HASNUM(v, n1)) lesson[k] = typeof v === 'number' ? n2 : like(n2, v);
    else if (typeof v === 'string') lesson[k] = v.replace(/(عدد الحصص\D{0,4})([0-9٠-٩]+)/, (m, a, x) => (toN(x) === n1 ? a + like(n2, x) : m))
      .replace(/([0-9٠-٩]+)(\s*حصص)/, (m, x, b) => (toN(x) === n1 ? like(n2, x) + (n2 <= 2 ? (n2 === 1 ? ' حصة' : ' حصتان') : n2 <= 10 ? b : ' حصة') : m));
    else if (Array.isArray(v) && v.every((x) => Array.isArray(x) && x.length === 2 && typeof x[1] === 'string'))
      lesson[k] = v.map(([a, b]) => [a, b.replace(LABEL, (m, p, x, q, y) => (toN(y) === n1 ? p + x + q + like(n2, y) : m)).replace(/(الحصة\s*[0-9٠-٩]+\s*من\s*)([0-9٠-٩]+)/, (m, p, y) => (toN(y) === n1 ? p + like(n2, y) : m))]);
  }
}

/* ---------------- pages with their own data shapes */
const countAr = (n) => (n === 1 ? 'حصة واحدة' : n === 2 ? 'حصتان' : n <= 10 ? n + ' حصص' : n + ' حصة');
const escH = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\(\+\)/g, '<bdi>(+)</bdi>');
const nonEmpty = (t) => lines(t).map((l) => l.trim()).filter(Boolean);
function procSteps(ps, T) {   /* [{min, text}] lists (grades 2–4 math): one warm-up, one closing, times rescaled to T */
  let picked = [];
  ps.forEach((st, i) => {
    st = st.slice();
    if (i > 0) while (st.length > 1 && WARM.test(st[0].text.slice(0, 40))) st.shift();
    if (i < ps.length - 1) while (st.length > 1 && isClose([st[st.length - 1].text.slice(0, 40)])) st.pop();
    picked = picked.concat(st);
  });
  if (picked.some((x) => !(x.min > 0))) return picked;
  const nd = scaleTo(picked.map((x) => x.min), T);
  return picked.map((x, i) => Object.assign({}, x, { min: nd[i] }));
}
/* grades 2–4 math: lessons [{…, sessions:[{n, focus, outcomes:[{text,level}], extra_outcome, strategies[], resources[], concepts[],
   warmup, procedures:[{min,text}], formative:[{level,q,a}], summative:[…], notes}]}] */
function isSessions(o) { return Array.isArray(o) && o.length && o.every((l) => l && Array.isArray(l.sessions) && l.sessions.every((s) => Array.isArray(s.outcomes) && Array.isArray(s.procedures))); }
function mergeSessions(ss, gi) {
  const uni = (k) => { const u = []; ss.forEach((s) => (s[k] || []).forEach((x) => { if (!u.includes(x)) u.push(x); })); return u; };
  const out = Object.assign({}, ss[0]);
  out.n = gi + 1;
  out.focus = uni2(ss.map((s) => s.focus)).join(' + ');
  const seen = new Set(); out.outcomes = [];
  ss.forEach((s, i) => [...s.outcomes, ...(i && s.extra_outcome ? [s.extra_outcome] : [])].forEach((x) => { if (x && !seen.has(x.text)) { seen.add(x.text); out.outcomes.push(x); } }));
  for (const k of ['strategies', 'resources', 'concepts']) if (Array.isArray(ss[0][k])) out[k] = uni(k);
  if (ss.some((s) => Array.isArray(s.omins))) {   /* outcome times (tools/outcome_times.py): the merged outcomes share 40 minutes */
    const tm = new Map();
    ss.forEach((s) => [...s.outcomes, s.extra_outcome].forEach((x, i) => { if (x && s.omins && s.omins[i] && !tm.has(x.text)) tm.set(x.text, s.omins[i].min); }));
    const ms = [...out.outcomes, out.extra_outcome].map((x) => (x && tm.get(x.text)) || 5);
    const r = ms.length * 5 <= 40 ? scaleTo(ms, 8).map((x) => x * 5) : scaleTo(ms, 40);
    out.omins = r.map((m) => ({ min: m }));
  }
  out.procedures = procSteps(ss.map((s) => s.procedures), 40);
  for (const k of ['formative', 'summative']) if (Array.isArray(ss[0][k])) out[k] = [].concat(...ss.map((s) => s[k] || []));
  if (typeof ss[0].notes === 'string') out.notes = mergeNotes(ss.map((s) => s.notes || ''));
  return out;
}
const uni2 = (a) => a.filter((x, i) => x && a.indexOf(x) === i);
function twoShiftSessions(o, t1, t2) {
  const ns = o.map((l) => l.sessions.length), T1 = ns.reduce((a, b) => a + b, 0), target = Math.round((T1 * t2) / t1);
  const n2s = allocate(ns, target);
  o.forEach((l, li) => { if (n2s[li] < ns[li]) l.sessions = groupsOf(ns[li], n2s[li]).map(([a, b], gi) => mergeSessions(l.sessions.slice(a, b), gi)); });
  return `lessons ${o.length}, periods ${T1} → ${n2s.reduce((a, b) => a + b, 0)} (target ${target})`;
}
/* grade 6 Islamic: one flat list of periods {no, w, wl, date, unit, title, k, n, wi, wn, pages, f:[[label, text]×10]} in week
   order, k of n within a lesson; fields: title, outcomes, strategies, resources, warm-up, procedures (its minutes in the label),
   formative, final assessment, closing, homework. Merged periods are laid out again week by week (fewer in each week). */
function isFlat(o) { return Array.isArray(o) && o.length > 5 && o.every((e) => e && Array.isArray(e.f) && e.f.length === 10 && 'k' in e && 'n' in e && 'w' in e); }
function twoShiftFlat(o, t1, t2) {
  const les = new Map();
  o.forEach((e, i) => { const key = e.unit + '\u0000' + e.title + '\u0000' + e.n; if (!les.has(key)) les.set(key, []); les.get(key).push(i); });
  const L = [...les.values()], ns = L.map((x) => x.length), T1 = o.length, target = Math.round((T1 * t2) / t1);
  const n2s = allocate(ns, target), out = [];
  L.forEach((idx, li) => {
    const n1 = idx.length, n2 = n2s[li];
    groupsOf(n1, n2).forEach(([a, b], gi) => {
      const es = idx.slice(a, b).map((i) => o[i]), e0 = es[0];
      const pm = (e0.f[5][0].match(/[0-9٠-٩]+/) || [])[0];
      const kinds = ['first', 'out', 'union', 'union', 'first', pm ? toN(pm) : 'proc', 'q', 'q', 'last', 'notes'];
      const texts = mergeFields(es.map((e) => e.f.map((x) => x[1])), kinds);
      const pages = uni2(es.map((e) => e.pages));
      out.push({ at: idx[a], e: Object.assign({}, e0, { k: gi + 1, n: n2, pages: pages.length > 1 ? pages.join('، ') : e0.pages, f: e0.f.map((x, i) => [x[0], texts[i]]) }) });
    });
  });
  out.sort((x, y) => x.at - y.at);
  const weeks = []; o.forEach((e) => { const w = weeks.find((x) => x.w === e.w); if (w) w.c++; else weeks.push({ w: e.w, wl: e.wl, date: e.date, c: 1 }); });
  const q = allocate(weeks.map((w) => w.c), out.length);
  let j = 0;
  weeks.forEach((w, wi) => { for (let i = 0; i < q[wi] && j < out.length; i++, j++) Object.assign(out[j].e, { w: w.w, wl: w.wl, date: w.date, wi: i + 1, wn: q[wi] }); });
  out.forEach((x, i) => { x.e.no = i + 1; });
  o.splice(0, o.length, ...out.map((x) => x.e));
  return `lessons ${L.length}, periods ${T1} → ${o.length} (target ${target})`;
}
/* grade 10 sciences: {ft, lessons:[{label, unit, periods:[{n, focus, info(html), fields:[{h, t}]×10}], comb:{info, fields:[{h, t}]}}]}
   — t is the copied text, h its html; merged periods are built from t and h is drawn again from it */
function isHT(o) { return o && !Array.isArray(o) && Array.isArray(o.lessons) && o.lessons.length && o.lessons.every((l) => Array.isArray(l.periods) && l.periods.every((p) => Array.isArray(p.fields) && p.fields.every((f) => f && typeof f.h === 'string' && typeof f.t === 'string'))); }
function htmlOf(i, t, like0) {
  const L = nonEmpty(t), th = (like0.match(/<table.*?<\/thead>/) || [''])[0];
  const pills = (xs) => '<div class="pills">' + xs.map((x) => '<span>' + escH(x) + '</span>').join('') + '</div>';
  if (i === 0) {
    const li = [], ex = []; let head = '';
    L.forEach((l) => { const m = l.match(/^(مخرج(?:ات)? تعليمي(?:ة)? (?:آخر|أخرى)[:：])\s*(.*)$/); if (m) { head = m[1]; if (m[2]) ex.push(escH(m[2])); } else if (head) ex.push(escH(l)); else li.push('<li>' + escH(l.replace(/^[0-9٠-٩]+\s*[.)]\s*/, '')) + '</li>'); });
    return '<ol class="ol">' + li.join('') + '</ol>' + (head ? '<div class="extra"><b>' + head + '</b> ' + ex.join('<br>') + '</div>' : '');
  }
  if (i === 1) return th + '<tbody>' + L.map((l) => { const m = l.replace(/^[•\-]\s*/, '').match(/^(.*)\s←\s(.*)$/) || [0, l, '']; return '<tr><td>' + escH(m[1]) + '</td><td class="lv">' + escH(m[2]) + '</td></tr>'; }).join('') + '</tbody></table>';
  if (i === 2 || i === 3) return pills(L.map((l) => l.replace(/^[•\-]\s*/, '')));
  if (i === 4) return pills(L.join('، ').split(/\s*،\s*/).filter(Boolean));
  if (/class="plist"/.test(like0)) { const r = renderSteps(t); if (r) return r; }   /* no tables (tools/proc_list.py) */
  if (i === 6) {
    const rows = [], tot = (like0.match(/<div class="tot">.*?<\/div>/) || [''])[0];
    String(t).split(/\n\s*\n/).forEach((b) => {
      const bl = nonEmpty(b); if (!bl.length) return;
      const m = bl[0].match(/^\(([0-9٠-٩]+)\s*(?:دقائق|دقيقتان|دقيقة|د)\)\s*(.*)$/);
      if (!m) return;
      const role = (re) => escH((bl.find((x) => re.test(x)) || '').replace(re, '').trim());
      rows.push('<tr><td class="tm">' + m[1] + ' د</td><td class="st">' + escH(m[2]) + '</td><td>' + role(/^دور المعلم[:：]/) + '</td><td>' + role(/^دور الطالب[:：]/) + '</td></tr>');
    });
    return tot.replace(/[0-9٠-٩]+/, (n) => like(40, n)) + th + '<tbody>' + rows.join('') + '</tbody></table>';
  }
  if (i === 7 || i === 8) {
    return th + '<tbody>' + String(t).split(/\n\s*\n/).map((b) => {
      const bl = nonEmpty(b); if (!bl.length) return '';
      const m = bl[0].match(/^[0-9٠-٩]+\)\s*\[([^\]]*)\]\s*(.*)$/) || [0, '', bl[0]];
      const a = bl.slice(1).join(' ').replace(/^الإجابة النموذجية[:：]\s*/, '');
      return '<tr><td class="ev">' + escH(m[1]) + '</td><td>' + escH(m[2]) + '</td><td>' + escH(a) + '</td></tr>';
    }).join('') + '</tbody></table>';
  }
  return L.map((l) => '<p>' + escH(l) + '</p>').join('');
}
/* the page's own markup (e.g. <bdi> around formulas) for every list item / table row / pill / paragraph drawn again from t */
const UNIT_RE = /<(li|tr|span|p)\b[^>]*>.*?<\/\1>/g, TM_RE = /<td class="tm">[^<]*<\/td>/;
const unitKey = (u) => u.replace(/<\/?bdi>/g, '').replace(TM_RE, '');
function ownMarkup(html, units) {
  return html.replace(UNIT_RE, (u) => { const o = units.get(unitKey(u)); if (!o) return u; const tm = u.match(TM_RE); return tm ? o.replace(TM_RE, tm[0]) : o; });
}
function twoShiftHT(o, t1, t2) {
  const units = new Map();
  o.lessons.forEach((l) => l.periods.forEach((p) => p.fields.forEach((f) => (f.h.match(UNIT_RE) || []).forEach((u) => units.set(unitKey(u), u)))));
  const before = o.lessons.map((l) => l.periods.length);
  const g = { lessons: o.lessons.map((l) => ({ periods: l.periods.map((p) => Object.assign({}, p, { fields: p.fields.map((f) => f.t) })) })) };
  const r = twoShiftGeneric(g, t1, t2);
  o.lessons.forEach((l, li) => {
    const np = g.lessons[li].periods; if (np.length === before[li]) return;
    const like0 = l.periods[0].fields.map((f) => f.h);
    l.periods = np.map((p) => Object.assign(p, {
      info: String(p.info).replace(/(محور الحصة:<\/b>\s*)[^<]*/, (m, a) => a + escH(p.focus)),
      fields: p.fields.map((t, i) => ({ h: ownMarkup(i === 5 ? nonEmpty(t).map((x) => '<p>' + escH(x) + '</p>').join('') : htmlOf(i, t, like0[i]), units), t })),
    }));
    if (l.comb) {
      l.comb.info = String(l.comb.info).replace(/(عدد الحصص:<\/b>\s*)[^<]*/, (m, a) => a + countAr(np.length));
      l.comb.fields = l.comb.fields.map((f, i) => ({
        h: l.periods.map((p, k) => '<div class="psub">الحصة ' + (k + 1) + ': ' + escH(p.focus) + '</div>' + p.fields[i].h).join(''),
        t: l.periods.map((p, k) => 'الحصة ' + (k + 1) + ': ' + p.focus + '\n' + p.fields[i].t).join('\n\n'),
      }));
    }
  });
  return r.report;
}
/* grade 11 English: [{label, periods:[{focus, week, num, fields:[[n, label, text]×10]}], merged:[[n, label, text]×10]}] */
function isNLT(o) { return Array.isArray(o) && o.length && o.every((u) => Array.isArray(u.periods) && u.periods.every((p) => Array.isArray(p.fields) && p.fields.every((f) => Array.isArray(f) && f.length === 3 && typeof f[2] === 'string'))); }
function twoShiftNLT(o, t1, t2) {
  const labs = o.map((u) => u.periods[0].fields.map((f) => [f[0], f[1]]));
  o.forEach((u) => { u.periods.forEach((p) => { p.fields = p.fields.map((f) => f[2]); }); if (Array.isArray(u.merged)) u.merged = u.merged.map((f) => f[2]); });
  const r = twoShiftGeneric({ lessons: o }, t1, t2);
  o.forEach((u, ui) => { u.periods.forEach((p) => { p.fields = p.fields.map((t, i) => [...labs[ui][i], t]); }); if (Array.isArray(u.merged)) u.merged = u.merged.map((t, i) => [...labs[ui][i], t]); });
  return r.report;
}
function twoShift(data, t1, t2) {
  const o = JSON.parse(JSON.stringify(data));
  if (isSessions(o)) return { data: o, report: twoShiftSessions(o, t1, t2) };
  if (isFlat(o)) return { data: o, report: twoShiftFlat(o, t1, t2) };
  if (isHT(o)) return { data: o, report: twoShiftHT(o, t1, t2) };
  if (isNLT(o)) return { data: o, report: twoShiftNLT(o, t1, t2) };
  return twoShiftGeneric(o, t1, t2);
}
function twoShiftGeneric(o, t1, t2) {
  const found = findLessons(o);
  if (!found.length) return { data: null, report: 'no period lists' };
  const ns = found.map((f) => f.lesson[f.key].length), T1 = ns.reduce((a, b) => a + b, 0);
  const target = Math.round((T1 * t2) / t1);
  const n2s = allocate(ns, target);
  let merged = 0;
  found.forEach((f, li) => {
    const n1 = ns[li], n2 = n2s[li]; if (n2 >= n1) return;
    const ps = f.lesson[f.key].map((p, i) => Object.assign(p, { __i: i }));
    const groups = groupsOf(n1, n2);
    const np = groups.map(([a, b], gi) => mergePeriods(ps.slice(a, b), f.fk, gi, n2, n1));
    ps.forEach((p) => delete p.__i);
    f.lesson[f.key] = np; merged++;
    for (const ck of Object.keys(f.lesson)) {
      const cv = f.lesson[ck];
      if (!COMB.has(ck) || !isFields(cv)) continue;
      const fk = f.fk[0], arr = Array.isArray(cv);
      const keys = arr ? cv.map((_, i) => i) : Object.keys(cv);
      keys.forEach((kk, i) => {
        const nf = np.map((p) => (Array.isArray(p[fk]) ? p[fk][i] : Object.values(p[fk])[i]));
        cv[kk] = rebuildCombined(cv[kk], n1, groups, nf, i);
      });
    }
    fixLessonMeta(f.lesson, f.key, n1, n2);
  });
  return { data: o, report: `lessons ${found.length}, periods ${T1} → ${n2s.reduce((a, b) => a + b, 0)} (target ${target}), lessons merged ${merged}` };
}
if (require.main === module) {
  const inp = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const out = { pages: inp.pages.map((pg) => {
    const reps = [], lits = pg.lits.map((d) => { const r = twoShift(d, pg.t1, pg.t2); reps.push(r.report); return r.data; });
    return { rel: pg.rel, lits, report: reps.join(' | ') };
  }) };
  fs.writeFileSync(process.argv[3], JSON.stringify(out));
}
module.exports = { twoShift, retime, mergeProc, mergeOutcomes, mergeLevels, mergeUnion, mergeQuestions, mergeNotes, allocate, groupsOf };
