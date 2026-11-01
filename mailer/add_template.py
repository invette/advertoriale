#!/usr/bin/env python3
# Wgrywa szablon z pliku JSON do panelu (tworzy nowy albo aktualizuje ten o tej samej nazwie).
#   python3 add_template.py templates/fiolki-nl.json
import json, sys, urllib.request, os
cfg = dict(l.split(': ', 1) for l in open(os.path.expanduser('~/bm/panel.txt'), encoding='utf-8').read().splitlines() if ': ' in l)
URL, KEY = cfg['Panel'].strip(), cfg['Haslo'].strip()


def call(path, data=None):
    req = urllib.request.Request(URL + path.lstrip('/'), data=json.dumps(data).encode() if data is not None else None,
                                 headers={'x-key': KEY, 'content-type': 'application/json'}, method='POST' if data is not None else 'GET')
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit('Blad: %s' % e.read().decode())


tpl = json.load(open(sys.argv[1], encoding='utf-8'))
have = [t for t in call('/api/templates')['templates'] if t.get('name') == tpl['name']]
tid = have[0]['id'] if have else call('/api/templates/new', {'name': tpl['name']})['template']['id']
r = call('/api/templates/' + tid, {k: tpl[k] for k in ('name', 'subject', 'preheader', 'from_name', 'from_email', 'reply_to', 'html')})
print(('Zaktualizowano' if have else 'Dodano') + ' szablon:', r['template']['name'], '| id:', tid)
