# Jednorazowo: zamienia lista.csv + mail.html (z ~/bm) na dane panelu (contacts.csv + template.json)
import csv, datetime, json, os, re, sys

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
SEG = {'Repeat': 'Powracający (2+ zamówienia)', 'Single order': '1 zamówienie', 'Zero orders': 'Bez zamówień', 'Lost': 'Utraceni', 'Lost (180+ dni)': 'Utraceni (180+ dni bez zakupu)'}
today = datetime.date.today().isoformat()

rows, seen = [], set()
for r in csv.DictReader(open(os.path.join(src, 'lista.csv'), encoding='utf-8')):
    e = (r.get('email') or '').strip().lower()
    if e and e not in seen:
        seen.add(e)
        rows.append({'email': e, 'first_name': (r.get('first_name') or '').strip(), 'segment': SEG.get(r.get('segment', ''), r.get('segment') or 'import'), 'added': today})
with open(os.path.join(dst, 'contacts.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['email', 'first_name', 'segment', 'added'])
    w.writeheader()
    w.writerows(rows)

h = open(os.path.join(src, 'mail.html'), encoding='utf-8').read()
h = h.replace('%%HI%%', '{{powitanie}}')
m = re.search(r'(<div style="display:none;[^"]*">)(.*?)((?:&#8199;&#847;)+)</div>', h, re.S)
pre = ''
if m:
    pre = m.group(2).strip()
    h = h[:m.start(2)] + '{{preheader}}' + h[m.end(2):]
assert '{{powitanie}}' in h and '{{amazonSESUnsubscribeUrl}}' in h
tpl = {'subject': 'Black Month: im więcej słoików, tym niższa cena', 'preheader': pre or 'Rabat do −50% na peptydy NL i do −30% na Nutraceuticals. Nalicza się sam w koszyku, bez kodu.',
       'from_name': 'Synthagen Labs', 'from_email': 'newsletter@synthagen.co', 'reply_to': 'kontakt@synthagenlabs.com', 'html': h,
       'updated': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}
json.dump(tpl, open(os.path.join(dst, 'template.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('kontakty:', len(rows), '| preheader:', pre[:60])
