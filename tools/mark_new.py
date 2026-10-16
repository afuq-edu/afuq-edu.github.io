#!/usr/bin/env python3
"""Mark sections as new: they get a shiny «جديد ✨» badge for 30 days (assets/newbadge.js) on the subject portal,
the custom-link page /p/ and the home page.
Usage: python3 tools/mark_new.py 5/math/harvest [4/english/slides ...]   (the add_* tools call mark() themselves)"""
import os, re, sys, json, datetime
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
F = R + 'assets/newbadge.js'
def mark(*keys, date=None):
    date = date or datetime.date.today().isoformat()
    s = open(F, encoding='utf8').read()
    m = re.search(r'var NEW=(\{.*?\});', s, re.S); new = json.loads(m.group(1))
    for k in keys: new[k.strip('/')] = date
    new = dict(sorted(new.items(), key=lambda kv: (int(kv[0].split('/')[0]), kv[0])))
    s = s[:m.start(1)] + json.dumps(new, ensure_ascii=False, indent=0).replace('\n', '') + s[m.end(1):]
    open(F, 'w', encoding='utf8').write(s)
if __name__ == '__main__':
    mark(*sys.argv[1:]); print('marked', *sys.argv[1:])
