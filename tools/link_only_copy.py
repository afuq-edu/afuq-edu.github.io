#!/usr/bin/env python3
"""«نسخ» copies the link only (owner, 2026-11-11: «الغي نسخ رسالة نور وابقي فقط نسخ وهو ينسخ رابط فقط بدون اي كلام»).
The list pages of the games, harvest and homework sections had two buttons per row — «🔗 نسخ الرابط» and «📋 نسخ رسالة نور» (a message
with the title and a greeting). Now one button, «🔗 نسخ», copies the bare link. Rewrites the pages and the generator tools
(add_games.py, add_units.py); idempotent.  Usage: python3 tools/link_only_copy.py"""
import os, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
MSG = '<button type="button" class="btn cp" data-k="msg">📋 نسخ رسالة نور</button>'
SUB = [(MSG, ''),
       ('اضغط «نسخ رسالة نور» وألصقها في منصة نور (الواجبات أو المحتوى) فتصل للطلاب مع الرابط، أو «نسخ الرابط» وحده.', 'اضغط «نسخ» وألصق الرابط في منصة نور (الواجبات أو المحتوى).'),
       ('اضغط «نسخ رسالة نور» وألصقها في منصة نور، أو «نسخ الرابط» وحده.', 'اضغط «نسخ» وألصق الرابط في منصة نور.'),
       ('اضغط «نسخ الرابط» وضعه', 'اضغط «نسخ» وضعه'),
       ('🔗 نسخ الرابط', '🔗 نسخ'),
       ("c.textContent='نسخ الرابط'", "c.textContent='نسخ'"), ("c.textContent='نسخ الرابط'", "c.textContent='نسخ'")]
def fix(p):
    h = open(p, encoding='utf8').read(); o = h
    for a, b in SUB: h = h.replace(a, b)
    h = h.replace("setTimeout(function(){c.textContent='نسخ الرابط'", "setTimeout(function(){c.textContent='نسخ'")
    if h != o: open(p, 'w', encoding='utf8').write(h); return 1
    return 0
def main():
    n = 0
    for p in glob.glob(R + '[0-9]*/*/*/index.html') + [R + 'tools/add_games.py', R + 'tools/add_units.py']:
        try: n += fix(p)
        except Exception: pass
    print('rewritten:', n)
if __name__ == '__main__': main()
