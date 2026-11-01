# Synthagen Mailer: panel do wysylki mailingow przez Amazon SES (AWS Lambda + Function URL + S3)
import base64, csv, datetime, html as H, io, json, os, re, time, uuid
import boto3
from botocore.exceptions import ClientError

B = os.environ.get('BUCKET', '')
PW = os.environ.get('PANEL_PASSWORD', '')
REGION = os.environ.get('SES_REGION', 'eu-north-1')
CS = os.environ.get('CONFIG_SET', 'bm-pl')
CL = os.environ.get('CONTACT_LIST', 'synthagen-pl')
TOPIC = os.environ.get('TOPIC', 'promocje')
MAX_BOUNCE, MAX_COMPLAINT = 0.06, 0.003

s3 = boto3.client('s3')
ses = boto3.client('sesv2', region_name=REGION)
ses1 = boto3.client('ses', region_name=REGION)
lam = boto3.client('lambda')
cw = boto3.client('cloudwatch', region_name=REGION)
PANEL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'panel.html'), encoding='utf-8').read()
EMAIL_RE = re.compile(r'^[^@\s,;<>"]+@[^@\s,;<>"]+\.[A-Za-z]{2,}$')
FIELDS = ['email', 'first_name', 'segment', 'added']


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def iso(d=None):
    return (d or now()).isoformat(timespec='seconds')


# ---------- S3 ----------
def s3get(key, default=None):
    try:
        return s3.get_object(Bucket=B, Key=key)['Body'].read().decode('utf-8')
    except ClientError as e:
        if e.response['Error']['Code'] in ('NoSuchKey', '404'):
            return default
        raise


def s3put(key, text, ctype='application/json'):
    s3.put_object(Bucket=B, Key=key, Body=text.encode('utf-8'), ContentType=ctype + '; charset=utf-8')


def jget(key, default=None):
    t = s3get(key)
    return json.loads(t) if t else default


def jput(key, obj):
    s3put(key, json.dumps(obj, ensure_ascii=False))


def load_contacts():
    t = s3get('contacts.csv', '')
    return [{k: (r.get(k) or '').strip() for k in FIELDS} for r in csv.DictReader(io.StringIO(t))] if t else []


def save_contacts(rows):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=FIELDS, extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
    s3put('contacts.csv', out.getvalue(), 'text/csv')


# ---------- SES ----------
def unsubscribed():
    out, token = set(), None
    try:
        while True:
            kw = {'ContactListName': CL, 'PageSize': 1000}
            if token:
                kw['NextToken'] = token
            r = ses.list_contacts(**kw)
            for c in r.get('Contacts', []):
                topic_out = any(t.get('TopicName') == TOPIC and t.get('SubscriptionStatus') == 'OPT_OUT' for t in c.get('TopicPreferences', []))
                if c.get('UnsubscribeAll') or topic_out:
                    out.add(c['EmailAddress'].lower())
            token = r.get('NextToken')
            if not token:
                break
    except ClientError:
        pass
    return out


def verified_identities():
    out = set()
    try:
        for i in ses.list_email_identities(PageSize=100).get('EmailIdentities', []):
            if i.get('SendingEnabled') and i.get('VerificationStatus', 'SUCCESS') == 'SUCCESS':
                out.add(i['IdentityName'].lower())
    except ClientError:
        pass
    return out


def greeting(name, for_html):
    n = (name or '').strip().split(' ')[0]
    if not n or not n.replace('-', '').isalpha():
        return 'Cześć,', ''
    if n.isupper() or n.islower():
        n = n[:1].upper() + n[1:].lower()
    return 'Cześć ' + (H.escape(n) if for_html else n) + ',', (H.escape(n) if for_html else n)


def html_to_text(h):
    h = re.sub(r'(?is)<(script|style|head)[^>]*>.*?</\1>', '', h)
    h = re.sub(r'(?is)<div[^>]*display:\s*none[^>]*>.*?</div>', '', h)
    h = re.sub(r'(?is)<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', lambda m: re.sub('<[^>]+>', '', re.sub(r'(?i)<br\s*/?>', ' ', m.group(2))).strip() + ' (' + m.group(1).replace('&amp;', '&') + ')', h)
    h = re.sub(r'(?i)<br\s*/?>', '\n', h)
    h = re.sub(r'(?i)</(p|tr|h\d|div|li)>', '\n', h)
    h = re.sub(r'<[^>]+>', ' ', h)
    h = H.unescape(h)
    lines = [re.sub(r'[ \t ]+', ' ', l).strip() for l in h.split('\n')]
    out, prev = [], ''
    for l in lines:
        if l or prev:
            out.append(l)
        prev = l
    return '\n'.join(out).strip()


def render(tpl, name):
    pw_h, imie_h = greeting(name, True)
    pw_t, imie_t = greeting(name, False)
    pre = H.escape(tpl.get('preheader', ''))
    hb = tpl['html'].replace('{{powitanie}}', pw_h).replace('{{imie}}', imie_h).replace('{{preheader}}', pre)
    tb = html_to_text(tpl['html']).replace('{{powitanie}}', pw_t).replace('{{imie}}', imie_t).replace('{{preheader}}', '')
    return hb, tb


def send_one(tpl, email, name, tag):
    hb, tb = render(tpl, name)
    sender = '%s <%s>' % (tpl.get('from_name', 'Synthagen Labs'), tpl['from_email'])
    kw = dict(FromEmailAddress=sender, Destination={'ToAddresses': [email]},
              Content={'Simple': {'Subject': {'Data': tpl['subject'], 'Charset': 'UTF-8'},
                                  'Body': {'Html': {'Data': hb, 'Charset': 'UTF-8'}, 'Text': {'Data': tb, 'Charset': 'UTF-8'}}}},
              EmailTags=[{'Name': 'campaign', 'Value': tag}], ConfigurationSetName=CS,
              ListManagementOptions={'ContactListName': CL, 'TopicName': TOPIC})
    if tpl.get('reply_to'):
        kw['ReplyToAddresses'] = [tpl['reply_to']]
    ses.send_email(**kw)


def health(start):
    pts = [p for p in ses1.get_send_statistics()['SendDataPoints'] if p['Timestamp'] >= start - datetime.timedelta(minutes=15)]
    return sum(p['DeliveryAttempts'] for p in pts), sum(p['Bounces'] for p in pts), sum(p['Complaints'] for p in pts)


def stats(tag, since):
    start = max(datetime.datetime.fromisoformat(since) - datetime.timedelta(hours=1), now() - datetime.timedelta(days=14))
    names = ['Send', 'Delivery', 'Bounce', 'Complaint', 'Open', 'Click', 'Reject', 'Subscription']
    q = [{'Id': 'm%d' % i, 'MetricStat': {'Metric': {'Namespace': 'AWS/SES', 'MetricName': n, 'Dimensions': [{'Name': 'campaign', 'Value': tag}]},
                                          'Period': 3600, 'Stat': 'Sum'}} for i, n in enumerate(names)]
    out = {n: 0 for n in names}
    try:
        r = cw.get_metric_data(MetricDataQueries=q, StartTime=start, EndTime=now() + datetime.timedelta(minutes=5))
        for res in r['MetricDataResults']:
            out[names[int(res['Id'][1:])]] = int(sum(res['Values']))
    except ClientError as e:
        out['error'] = str(e)
    return out


# ---------- kampanie ----------
def campaign_summary(c):
    return {k: c.get(k) for k in ('id', 'name', 'tag', 'status', 'total', 'sent', 'errors', 'created', 'started', 'finished', 'segments', 'note', 'subject')}


def list_campaigns():
    r = s3.list_objects_v2(Bucket=B, Prefix='campaigns/')
    out = []
    for o in r.get('Contents', []):
        if o['Key'].endswith('.json'):
            c = jget(o['Key'])
            if c:
                out.append(campaign_summary(c))
    return sorted(out, key=lambda c: c.get('created') or '', reverse=True)


def checkpoint(key, c, i):
    """Zapisuje postep. Zwraca True, jesli w miedzyczasie ktos kliknal Zatrzymaj."""
    cur = jget(key, {})
    c['cursor'], c['beat'] = i, iso()
    if cur.get('status') == 'stopping':
        c['status'], c['finished'] = 'stopped', iso()
        jput(key, c)
        return True
    jput(key, c)
    return False


def run_job(cid, context):
    key = 'campaigns/%s.json' % cid
    c = jget(key)
    if c and c['status'] == 'stopping':
        c['status'], c['finished'] = 'stopped', iso()
        jput(key, c)
        return
    if not c or c['status'] not in ('queued', 'running'):
        return
    rec = list(csv.DictReader(io.StringIO(s3get('campaigns/%s.csv' % cid, ''))))
    tpl = c['template']
    if c['status'] == 'queued':
        c['status'], c['started'] = 'running', iso()
    c['beat'] = iso()
    jput(key, c)
    start = datetime.datetime.fromisoformat(c['started'])
    rate = max(1, min(12, int(c.get('rate', 7))))
    i = c.get('cursor', 0)
    t0, base = time.time(), i
    while i < len(rec):
        if context.get_remaining_time_in_millis() < 45000:
            if checkpoint(key, c, i):
                return
            lam.invoke(FunctionName=context.function_name, InvocationType='Event', Payload=json.dumps({'job': cid}).encode())
            return
        if (i - base) % 25 == 0 and i != base:
            if checkpoint(key, c, i):
                return
        r = rec[i]
        for attempt in range(5):
            try:
                send_one(tpl, r['email'], r.get('first_name', ''), c['tag'])
                c['sent'] += 1
                break
            except ClientError as e:
                code = e.response['Error']['Code']
                if code in ('Throttling', 'TooManyRequestsException', 'ThrottlingException') and attempt < 4:
                    time.sleep(2 * (attempt + 1))
                    continue
                if code in ('AccountSuspendedException', 'SendingPausedException', 'MailFromDomainNotVerifiedException'):
                    c['status'], c['note'], c['finished'], c['cursor'] = 'failed', 'SES zablokował wysyłkę: ' + code, iso(), i
                    jput(key, c)
                    return
                c['errors'] += 1
                c.setdefault('error_list', []).append([r['email'], code])
                c['error_list'] = c['error_list'][-50:]
                break
        i += 1
        time.sleep(max(0, (i - base) / rate - (time.time() - t0)))
        if i % 300 == 0:
            try:
                att, b, cpl = health(start)
            except ClientError:
                att = b = cpl = 0
            if att >= 200 and (b / att > MAX_BOUNCE or cpl / att > MAX_COMPLAINT):
                c['status'], c['finished'], c['cursor'] = 'stopped', iso(), i
                c['note'] = 'Zatrzymano automatycznie: odbicia %d/%d, skargi %d/%d' % (b, att, cpl, att)
                jput(key, c)
                return
    if checkpoint(key, c, i):
        return
    c['status'], c['finished'] = 'done', iso()
    jput(key, c)


# ---------- HTTP ----------
def resp(code, body, ctype='application/json; charset=utf-8'):
    return {'statusCode': code, 'headers': {'content-type': ctype, 'cache-control': 'no-store', 'x-robots-tag': 'noindex'},
            'body': body if isinstance(body, str) else json.dumps(body, ensure_ascii=False, default=str)}


def parse_import(text, segment):
    text = text.lstrip('﻿')
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return []
    sample = lines[0]
    delim = ';' if sample.count(';') > sample.count(',') else ','
    head = [h.strip().lower().strip('"') for h in next(csv.reader([sample], delimiter=delim))]
    def idx(*names):
        for n in names:
            if n in head:
                return head.index(n)
        return None
    ie = idx('email', 'e-mail', 'mail', 'adres', 'adres e-mail', 'email address')
    rows = []
    if ie is not None:
        inm, isg = idx('first_name', 'imie', 'imię', 'first name', 'name', 'firstname'), idx('segment', 'grupa', 'tag')
        for rec in csv.reader(lines[1:], delimiter=delim):
            if len(rec) <= ie:
                continue
            rows.append({'email': rec[ie], 'first_name': rec[inm] if inm is not None and len(rec) > inm else '',
                         'segment': segment or (rec[isg] if isg is not None and len(rec) > isg else '')})
    else:
        for l in lines:
            parts = [p.strip() for p in re.split(r'[,;\t]', l)]
            rows.append({'email': parts[0], 'first_name': parts[1] if len(parts) > 1 else '', 'segment': segment})
    out = []
    for r in rows:
        e = r['email'].strip().strip('"').lower()
        if EMAIL_RE.match(e):
            out.append({'email': e, 'first_name': r['first_name'].strip().strip('"'), 'segment': (r['segment'] or '').strip().strip('"') or 'import', 'added': iso()[:10]})
    return out


def api(method, path, data, qs, context):
    if path == '/api/state':
        rows = load_contacts()
        seg = {}
        for r in rows:
            seg[r['segment'] or '(brak)'] = seg.get(r['segment'] or '(brak)', 0) + 1
        try:
            acc = ses.get_account()['SendQuota']
        except ClientError:
            acc = {}
        uns = unsubscribed()
        return {'total': len(rows), 'segments': seg, 'template': jget('template.json', {}), 'quota': acc,
                'unsubscribed': len(uns), 'unsubscribed_in_list': sum(1 for r in rows if r['email'].lower() in uns),
                'campaigns': list_campaigns()[:20]}
    if path == '/api/contacts' and method == 'GET':
        rows = load_contacts()
        uns = unsubscribed()
        q, sg = (qs.get('q') or '').lower().strip(), qs.get('seg') or ''
        if q:
            rows = [r for r in rows if q in r['email'].lower() or q in r['first_name'].lower()]
        if sg:
            rows = [r for r in rows if (r['segment'] or '(brak)') == sg]
        page, size = int(qs.get('page') or 1), int(qs.get('size') or 100)
        part = rows[(page - 1) * size: page * size]
        for r in part:
            r['unsub'] = r['email'].lower() in uns
        return {'total': len(rows), 'page': page, 'size': size, 'rows': part}
    if path == '/api/contacts/add':
        e = (data.get('email') or '').strip().lower()
        if not EMAIL_RE.match(e):
            return {'error': 'Nieprawidłowy adres e-mail'}
        rows = load_contacts()
        if any(r['email'] == e for r in rows):
            return {'error': 'Ten adres już jest na liście'}
        rows.insert(0, {'email': e, 'first_name': (data.get('first_name') or '').strip(), 'segment': (data.get('segment') or 'ręcznie').strip(), 'added': iso()[:10]})
        save_contacts(rows)
        return {'ok': True, 'total': len(rows)}
    if path == '/api/contacts/update':
        e = (data.get('email') or '').strip().lower()
        rows = load_contacts()
        for r in rows:
            if r['email'] == e:
                if 'first_name' in data:
                    r['first_name'] = (data['first_name'] or '').strip()
                if 'segment' in data:
                    r['segment'] = (data['segment'] or '').strip()
        save_contacts(rows)
        return {'ok': True}
    if path == '/api/contacts/delete':
        drop = set(x.strip().lower() for x in data.get('emails', []))
        if data.get('segment'):
            rows = [r for r in load_contacts() if r['segment'] != data['segment']]
        else:
            rows = [r for r in load_contacts() if r['email'] not in drop]
        save_contacts(rows)
        return {'ok': True, 'total': len(rows)}
    if path == '/api/contacts/import':
        new = parse_import(data.get('csv') or '', (data.get('segment') or '').strip())
        rows = [] if data.get('mode') == 'replace' else load_contacts()
        have = {r['email'] for r in rows}
        added = 0
        for r in new:
            if r['email'] not in have:
                rows.append(r)
                have.add(r['email'])
                added += 1
        save_contacts(rows)
        return {'ok': True, 'added': added, 'skipped': len(new) - added, 'total': len(rows)}
    if path == '/api/contacts/export':
        return {'csv': s3get('contacts.csv', '')}
    if path == '/api/template' and method == 'POST':
        fe = (data.get('from_email') or '').strip().lower()
        if fe:
            if not EMAIL_RE.match(fe):
                return {'error': 'Nieprawidłowy adres nadawcy'}
            ok = verified_identities()
            if ok and fe not in ok and fe.split('@')[1] not in ok:
                return {'error': 'Adres nadawcy musi być w zweryfikowanej domenie: ' + ', '.join(sorted(x for x in ok if '@' not in x))}
            data['from_email'] = fe
        if 'html' in data and '{{amazonSESUnsubscribeUrl}}' not in data['html']:
            return {'error': 'W szablonie musi zostać {{amazonSESUnsubscribeUrl}} (link do wypisania).'}
        tpl = jget('template.json', {})
        for k in ('subject', 'preheader', 'from_name', 'from_email', 'reply_to', 'html'):
            if k in data:
                tpl[k] = data[k]
        tpl['updated'] = iso()
        prev = s3get('template.json')
        if prev:
            s3put('template-history/%s.json' % iso().replace(':', '-'), prev)
        jput('template.json', tpl)
        return {'ok': True, 'template': tpl}
    if path == '/api/test':
        tpl = jget('template.json', {})
        to = (data.get('to') or '').strip()
        if not EMAIL_RE.match(to):
            return {'error': 'Podaj poprawny adres testowy'}
        try:
            send_one(tpl, to, data.get('first_name') or 'Jakub', 'test')
        except ClientError as e:
            return {'error': e.response['Error']['Code'] + ': ' + e.response['Error'].get('Message', '')}
        return {'ok': True}
    if path == '/api/campaigns/start':
        for c in list_campaigns():
            if c['status'] in ('queued', 'running', 'stopping'):
                full = jget('campaigns/%s.json' % c['id'], {})
                beat = full.get('beat') or full.get('created')
                if beat and now() - datetime.datetime.fromisoformat(beat) > datetime.timedelta(minutes=10):
                    full['status'], full['finished'] = 'stopped', iso()
                    full['note'] = 'Przerwana (brak postępu przez 10 min). Resztę wyślesz z opcją „Pomiń osoby, które dostały już poprzednią kampanię”.'
                    jput('campaigns/%s.json' % c['id'], full)
                    continue
                return {'error': 'Trwa już wysyłka „%s”. Poczekaj albo ją zatrzymaj.' % c['name']}
        tpl = jget('template.json', {})
        if '{{amazonSESUnsubscribeUrl}}' not in tpl.get('html', ''):
            return {'error': 'W szablonie brakuje linku do wypisania się ({{amazonSESUnsubscribeUrl}}).'}
        segs = data.get('segments') or []
        uns = unsubscribed()
        rows = [r for r in load_contacts() if (not segs or (r['segment'] or '(brak)') in segs) and r['email'].lower() not in uns]
        if data.get('exclude_sent'):
            sent = set()
            for c in list_campaigns():
                if c['status'] in ('done', 'stopped', 'failed') and c.get('sent'):
                    rec = list(csv.DictReader(io.StringIO(s3get('campaigns/%s.csv' % c['id'], ''))))
                    cur = jget('campaigns/%s.json' % c['id'], {}).get('cursor', 0)
                    sent.update(r['email'] for r in rec[:cur])
            rows = [r for r in rows if r['email'] not in sent]
        if not rows:
            return {'error': 'Brak odbiorców dla wybranych grup.'}
        cid = now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:4]
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=['email', 'first_name'], extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
        s3put('campaigns/%s.csv' % cid, out.getvalue(), 'text/csv')
        name = (data.get('name') or tpl.get('subject') or 'Kampania').strip()[:120]
        c = {'id': cid, 'name': name, 'tag': 'c-' + cid, 'status': 'queued', 'total': len(rows), 'sent': 0, 'errors': 0,
             'cursor': 0, 'created': iso(), 'segments': segs, 'rate': int(data.get('rate') or 7), 'template': tpl, 'subject': tpl.get('subject')}
        jput('campaigns/%s.json' % cid, c)
        lam.invoke(FunctionName=context.function_name, InvocationType='Event', Payload=json.dumps({'job': cid}).encode())
        return {'ok': True, 'campaign': campaign_summary(c)}
    m = re.match(r'^/api/campaigns/([\w-]+)(/stop|/stats)?$', path)
    if m:
        cid, act = m.group(1), m.group(2)
        key = 'campaigns/%s.json' % cid
        c = jget(key)
        if not c:
            return {'error': 'Nie ma takiej kampanii'}
        if act == '/stop':
            if c['status'] in ('queued', 'running'):
                c['status'] = 'stopping'
                jput(key, c)
            return {'ok': True}
        out = campaign_summary(c)
        out['cursor'] = c.get('cursor', 0)
        out['error_list'] = c.get('error_list', [])[-10:]
        if act == '/stats':
            out['stats'] = stats(c['tag'], c.get('started') or c['created'])
        return out
    return {'error': 'Nieznany adres'}


def handler(event, context):
    if isinstance(event, dict) and 'job' in event:
        return run_job(event['job'], context)
    http = (event.get('requestContext') or {}).get('http') or {}
    method, path = http.get('method', 'GET'), event.get('rawPath', '/')
    if method == 'GET' and path in ('/', '/index.html'):
        return resp(200, PANEL, 'text/html; charset=utf-8')
    if method == 'GET' and path == '/favicon.ico':
        return resp(204, '')
    hdr = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
    if not PW or hdr.get('x-key') != PW:
        return resp(401, {'error': 'Złe hasło'})
    body = event.get('body') or ''
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')
    try:
        data = json.loads(body) if body.strip() else {}
    except ValueError:
        data = {}
    try:
        out = api(method, path, data, event.get('queryStringParameters') or {}, context)
    except ClientError as e:
        out = {'error': 'AWS: ' + e.response['Error']['Code'] + ' ' + e.response['Error'].get('Message', '')}
    return resp(400 if isinstance(out, dict) and out.get('error') else 200, out)
