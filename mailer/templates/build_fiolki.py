# Generuje szablon "Fiolki -> NL-BPC-157 (kod VIAL)" do panelu Synthagen Mailer.
# Ceny sprawdzone w koszyku synthagenlabs.com (Black Month + kod VIAL), 1.11.2026.
import json, pathlib

D = pathlib.Path(__file__).parent
SHOP = 'https://synthagenlabs.com'
IMG = 'https://synthagen.co/img/mail'
CDN = 'https://cdn.shopify.com/s/files/1/0953/4911/3207/files'


def utm(content):
    return 'utm_source=ses&amp;utm_medium=email&amp;utm_campaign={{kampania}}&amp;utm_content=' + content


def vial(path, content):
    # link, ktory sam dodaje kod VIAL i przenosi na wskazana strone
    return SHOP + '/discount/VIAL?redirect=' + path.replace('/', '%2F') + '&amp;' + utm(content)


def page(path, content):
    return SHOP + path + '?' + utm(content)


BG, CARD, LINE, HI, HIL = '#05060D', '#0E1226', '#1C2350', '#141C4F', '#2A3A99'
TXT, SUB, MUT, ACC, ACC2 = '#F3F5FF', '#C9CEE6', '#7E86A8', '#4D6BFF', '#8FA3FF'
MONO = "font-family:'Courier New',Courier,monospace;"
BLACK = "font-family:'Arial Black',Arial,Helvetica,sans-serif;font-weight:900;"


def kicker(t):
    return f'<p style="margin:0;{MONO}font-size:11px;letter-spacing:3px;text-transform:uppercase;color:{ACC2};">{t}</p>'


def h2(t):
    return f'<h2 style="margin:8px 0 0;{BLACK}font-size:26px;line-height:1.15;color:#FFFFFF;">{t}</h2>'


def p(t, size=15, color=SUB, top=12):
    return f'<p style="margin:{top}px 0 0;font-size:{size}px;line-height:1.6;color:{color};">{t}</p>'


def button(href, label):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" style="background:#1F3BFF;border-radius:14px;">'
            f'<a href="{href}" target="_blank" style="display:block;padding:19px 16px;font-size:16px;font-weight:700;color:#FFFFFF;text-decoration:none;">{label}</a></td></tr></table>')


def row(inner, pad='26px 32px 0'):
    return f'<tr><td style="padding:{pad};">{inner}</td></tr>\n'


def divider():
    return f'<tr><td style="padding:30px 32px 0;"><div style="height:1px;line-height:1px;font-size:0;background:{LINE};">&nbsp;</div></td></tr>\n'


# ---------- ceny (z koszyka) ----------
TIERS = [  # sloikow, rabat BM, za sloik z VIAL, razem z VIAL
    (1, '–', '215,10', '215,10'),
    (3, '−5%', '204,35', '613,04'),
    (5, '−10%', '193,59', '967,95'),
    (10, '−15%', '182,84', '1 828,35'),
    (15, '−30%', '150,57', '2 258,55'),
    (20, '−38%', '133,36', '2 667,24'),
    (25, '−44%', '120,46', '3 011,40'),
    (30, '−50%', '107,55', '3 226,50'),
]


def price_table():
    th = f'style="padding:10px 6px;{MONO}font-size:10px;letter-spacing:1px;text-transform:uppercase;color:{MUT};border-bottom:1px solid {LINE};"'
    out = [f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">',
           f'<tr><td {th}>Słoików</td><td align="center" {th}>Black Month</td><td align="right" {th}>Za słoik z VIAL</td><td align="right" {th}>Razem z VIAL</td></tr>']
    for n, bm, per, tot in TIERS:
        last = n == 30
        bg = f'background:{HI};' if last else ''
        c1 = '#FFFFFF' if last else TXT
        out.append(f'<tr><td style="{bg}padding:11px 6px;border-bottom:1px solid {LINE};font-size:14px;font-weight:bold;color:{c1};">{n}</td>'
                   f'<td align="center" style="{bg}padding:11px 6px;border-bottom:1px solid {LINE};{MONO}font-size:13px;font-weight:bold;color:{ACC2 if bm != "–" else MUT};">{bm}</td>'
                   f'<td align="right" style="{bg}padding:11px 6px;border-bottom:1px solid {LINE};font-size:{17 if last else 15}px;font-weight:bold;color:#FFFFFF;white-space:nowrap;">{per} zł</td>'
                   f'<td align="right" style="{bg}padding:11px 6px;border-bottom:1px solid {LINE};font-size:13px;color:{SUB};white-space:nowrap;">{tot} zł</td></tr>')
    out.append('</table>')
    return '\n'.join(out)


COMPARE = [
    ('Co dostajesz', 'proszek w fiolce do rozpuszczenia', 'gotowa kapsułka'),
    ('Przygo&shy;towanie', 'woda bakteriostatyczna, strzykawka, odmierzanie', 'żadne'),
    ('Podanie', 'wkłucie igłą', '1 kapsułka rano, popijasz wodą'),
    ('Dawka', 'tyle, ile uda się odmierzyć', '200 µg w każdej kapsułce'),
    ('Czą&shy;steczka', 'BPC-157, 15 aminokwasów', 'analog z 16 aminokwasów, oba końce zabezpieczone'),
    ('Kto sprzedaje', 'często anonimowy sklep, etykieta „research only”', 'firma z nazwą, adresem i KRS w stopce maila'),
    ('W podróży', 'fiolki, igły, waciki, lodówka', 'jeden słoik, 30 kapsułek'),
]


def compare_table():
    out = [f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;table-layout:fixed;">',
           f'<tr><td width="26%" style="padding:0 0 10px;"></td>'
           f'<td width="37%" align="center" style="padding:12px 6px;background:{CARD};border:1px solid {LINE};border-radius:12px 0 0 0;{MONO}font-size:10px;letter-spacing:1px;text-transform:uppercase;color:{MUT};">Fiolka „do badań”</td>'
           f'<td width="37%" align="center" style="padding:12px 6px;background:#1F3BFF;border-radius:0 12px 0 0;{MONO}font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#FFFFFF;font-weight:bold;">NL-BPC-157™</td></tr>']
    for lab, a, b in COMPARE:
        out.append(f'<tr><td valign="top" style="padding:11px 8px 11px 0;border-bottom:1px solid {LINE};font-size:12px;font-weight:bold;color:{MUT};word-break:break-word;">{lab}</td>'
                   f'<td valign="top" style="padding:11px 8px;background:{CARD};border-bottom:1px solid {LINE};font-size:13px;line-height:1.45;color:{MUT};"><span style="color:#E25563;">✕</span> {a}</td>'
                   f'<td valign="top" style="padding:11px 8px;background:{HI};border-bottom:1px solid {HIL};font-size:13px;line-height:1.45;color:#FFFFFF;"><span style="color:{ACC2};">✓</span> {b}</td></tr>')
    out.append('</table>')
    return '\n'.join(out)


def tech_point(sym, title, text):
    return (f'<tr><td width="52" valign="top" style="padding:14px 0 0;"><div style="width:40px;height:40px;line-height:40px;text-align:center;border-radius:10px;background:{HI};border:1px solid {HIL};{MONO}font-size:14px;font-weight:bold;color:#FFFFFF;">{sym}</div></td>'
            f'<td valign="top" style="padding:14px 0 0;"><p style="margin:0;font-size:15px;font-weight:bold;color:#FFFFFF;">{title}</p><p style="margin:4px 0 0;font-size:14px;line-height:1.55;color:{SUB};">{text}</p></td></tr>')


def mini(img, name, href):
    return (f'<td width="33%" align="center" valign="top" style="padding:0 4px;"><a href="{href}" target="_blank"><img src="{img}" width="120" alt="{name}" style="display:block;width:100%;max-width:120px;height:auto;border:0;border-radius:10px;margin:0 auto;"></a>'
            f'<p style="margin:6px 0 0;font-size:11px;font-weight:bold;color:#FFFFFF;">{name}</p></td>')


def person(img, name, role, desc):
    return (f'<td class="col" width="50%" valign="top" style="padding:0 6px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CARD};border:1px solid {LINE};border-radius:16px;"><tr><td style="padding:14px;">'
            f'<img src="{img}" width="240" alt="{name}" style="display:block;width:100%;max-width:240px;height:auto;border:0;border-radius:12px;">'
            f'<p style="margin:12px 0 0;font-size:15px;font-weight:bold;color:#FFFFFF;">{name}</p>'
            f'<p style="margin:3px 0 0;{MONO}font-size:10px;letter-spacing:1px;text-transform:uppercase;color:{ACC2};">{role}</p>'
            f'<p style="margin:8px 0 0;font-size:13px;line-height:1.5;color:{SUB};">{desc}</p></td></tr></table></td>')


BPC_IMG = CDN + '/bpc_chat.png?v=1789762734&amp;width=400'
H = []
H.append(f'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark light"><title>Peptyd bez strzykawki</title>
<style>@media screen and (max-width:520px){{.col{{display:block!important;width:100%!important;padding:0 0 12px!important}}.stk{{display:block!important;width:100%!important;box-sizing:border-box;padding:16px 18px!important}}.h1{{font-size:38px!important}}}}</style></head>
<body style="margin:0;padding:0;background:{BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{BG};">{{{{preheader}}}}&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;&#8199;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{BG};"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background:{BG};font-family:Montserrat,Arial,Helvetica,sans-serif;color:{TXT};">
''')
# pasek + logo
H.append(f'<tr><td align="center" style="padding:10px 16px;border-bottom:1px solid {LINE};{MONO}font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#9AA0BE;">Black Month <span style="color:{ACC};">◆</span> Kod VIAL −10% <span style="color:{ACC};">◆</span> Darmowa wysyłka <span style="color:{ACC};">◆</span> Do 30.11</td></tr>\n')
# hero
H.append(row(kicker('Dla tych, którzy znają peptydy z fiolek')
             + f'<h1 class="h1" style="margin:12px 0 0;{BLACK}font-size:46px;line-height:1.02;color:#FFFFFF;">Peptyd bez<br><span style="color:{ACC};">strzykawki.</span></h1>'
             + p('{{powitanie}} jeśli peptydy znasz z fiolek, proszku i insulinówki, mamy dla Ciebie prostszą drogę. <b style="color:#FFFFFF;">NL-BPC-157™</b> to analog BPC-157 zamknięty w kapsułce. Bez rozpuszczania, bez odmierzania, bez wkłucia. Jedna kapsułka rano.', 16, top=18), '32px 32px 0'))
# karta ceny
H.append(row(f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{HI};border:1px solid {HIL};border-radius:18px;"><tr>
<td class="stk" width="44%" align="center" valign="middle" style="padding:18px 6px 18px 18px;"><a href="{vial('/products/nl-bpc-157-heksadekapeptyd', 'hero-img')}" target="_blank"><img src="{BPC_IMG}" width="210" alt="NL-BPC-157™" style="display:block;width:100%;max-width:210px;height:auto;border:0;border-radius:14px;"></a></td>
<td class="stk" valign="middle" style="padding:20px 20px 20px 10px;">
<p style="margin:0;{MONO}font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{ACC2};">NL-BPC-157™ · 30 kapsułek</p>
<p style="margin:10px 0 0;font-size:13px;color:{MUT};">Cena regularna <span style="text-decoration:line-through;">239,00 zł</span></p>
<p style="margin:4px 0 0;font-size:13px;color:{SUB};">Black Month przy 30 słoikach: <b style="color:#FFFFFF;">119,50 zł</b></p>
<p style="margin:4px 0 0;font-size:13px;color:{SUB};">+ Twój kod <b style="color:#FFFFFF;">VIAL</b>: dodatkowe −10%</p>
<p style="margin:12px 0 0;{BLACK}font-size:44px;line-height:1;color:#FFFFFF;">107,55 zł</p>
<p style="margin:4px 0 0;font-size:13px;color:{SUB};">za słoik, czyli <b style="color:#FFFFFF;">−55%</b> od ceny regularnej</p>
</td></tr></table>''', '24px 32px 0'))
# kod
H.append(row(f'''<table role="presentation" align="center" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto;border:2px dashed {ACC};border-radius:14px;"><tr><td align="center" style="padding:14px 30px;">
<p style="margin:0;{MONO}font-size:11px;letter-spacing:2px;color:{MUT};">TWÓJ KOD</p>
<p style="margin:4px 0 0;{MONO}font-size:32px;font-weight:bold;letter-spacing:6px;color:#FFFFFF;">VIAL</p>
<p style="margin:4px 0 0;font-size:12px;color:{SUB};">−10% na całe zamówienie · łączy się z Black Month · do 30.11, 23:59</p></td></tr></table>''', '20px 32px 0'))
H.append(row(button(vial('/products/nl-bpc-157-heksadekapeptyd', 'cta1'), 'Odbierz cenę z kodem VIAL →')
             + f'<p style="margin:10px 0 0;text-align:center;font-size:12px;color:{MUT};">Kliknij przycisk, a kod doda się do koszyka sam.</p>', '18px 32px 0'))

# porownanie
H.append(divider())
H.append(row(kicker('Porównanie') + h2('Fiolka czy kapsułka?')
             + p('Ten sam punkt wyjścia, czyli peptyd BPC-157. Zupełnie inna codzienność.', 15) , '26px 32px 0'))
H.append(row(compare_table(), '18px 32px 0'))

# bezpieczenstwo
H.append(row(f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CARD};border:1px solid {LINE};border-radius:18px;"><tr><td style="padding:22px 22px 20px;">
{kicker('Bez igły')}
<p style="margin:8px 0 0;{BLACK}font-size:21px;line-height:1.2;color:#FFFFFF;">Bez igły znaczy bez ryzyk, które niesie wkłucie.</p>
{p('Przy samodzielnych iniekcjach ryzyko nie kończy się na samym peptydzie. Dochodzi roztwór, którego sterylności nie sprawdzisz, zakażenie w miejscu wkłucia, siniaki i pomyłka przy rozpuszczaniu albo odmierzaniu. Kapsułka usuwa cały ten etap: nie ma igły, nie ma roztworu, nie ma zgadywania dawki.', 14)}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:16px;"><tr>
<td width="33%" align="center" valign="top" style="padding:10px 4px;border:1px solid {HIL};background:{HI};border-radius:12px;"><p style="margin:0;font-size:20px;color:{ACC2};">✓</p><p style="margin:4px 0 0;font-size:12px;font-weight:bold;color:#FFFFFF;">Bez igły<br>i wkłucia</p></td>
<td width="6"></td>
<td width="33%" align="center" valign="top" style="padding:10px 4px;border:1px solid {HIL};background:{HI};border-radius:12px;"><p style="margin:0;font-size:20px;color:{ACC2};">✓</p><p style="margin:4px 0 0;font-size:12px;font-weight:bold;color:#FFFFFF;">Bez rozpuszczania<br>i odmierzania</p></td>
<td width="6"></td>
<td width="33%" align="center" valign="top" style="padding:10px 4px;border:1px solid {HIL};background:{HI};border-radius:12px;"><p style="margin:0;font-size:20px;color:{ACC2};">✓</p><p style="margin:4px 0 0;font-size:12px;font-weight:bold;color:#FFFFFF;">Stała dawka<br>200 µg</p></td>
</tr></table>
<p style="margin:16px 0 0;font-size:12px;line-height:1.55;color:{MUT};">Uczciwie: badania nad BPC-157 prowadzono głównie na zwierzętach i komórkach i nie dotyczą one naszego analogu. Dlatego nie obiecujemy efektów. Dajemy jawny skład, znaną dawkę i formę bez igły.</p>
</td></tr></table>''', '24px 32px 0'))

# technologia
H.append(divider())
H.append(row(kicker('Technologia NL') + h2('Kapsułka w kapsułce.')
             + p('Peptyd to łańcuch aminokwasów, a przewód pokarmowy jest zaprojektowany do rozcinania takich łańcuchów. Dlatego w NL-BPC-157™ są dwa zabezpieczenia.', 15), '26px 32px 0'))
H.append(row(f'<img src="{IMG}/nl-kapsulka.jpg" width="536" alt="Kapsułka w kapsułce NL-DELIVERY™" style="display:block;width:100%;max-width:536px;height:auto;border:0;margin:0 auto;">', '14px 32px 0'))
H.append(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
             + tech_point('Ac', 'Zabezpieczone końce łańcucha (NL-PEPTIDES™)', 'Początek łańcucha jest acetylowany, a koniec amidowany. Takie modyfikacje utrudniają enzymom odcinanie aminokwasów od końców.')
             + tech_point('2×', 'Podwójna kapsułka (NL-DELIVERY™)', 'Wewnętrzna kapsułka z powłoką dojelitową ma przejść przez żołądek i otworzyć się dopiero w jelicie.')
             + tech_point('1', 'Jedna kapsułka rano', 'Na czczo albo ok. 30 minut przed posiłkiem, popijając wodą. Jeden słoik to 30 dni.')
             + '</table>'
             + f'<p style="margin:16px 0 0;font-size:13px;"><a href="https://synthagen.co/bpc-157/?{utm("artykul")}" target="_blank" style="color:{ACC2};font-weight:bold;text-decoration:none;">Co wiadomo o BPC-157, a czego nie wiadomo →</a></p>', '4px 32px 0'))

# ceny z VIAL
H.append(divider())
H.append(row(kicker('Twoja cena') + h2('Ile płacisz z kodem VIAL')
             + p('Rabat Black Month rośnie z liczbą słoików, a VIAL zdejmuje jeszcze 10% z całości. Liczą się wszystkie peptydy NL w koszyku razem, więc możesz łączyć BPC-157 z innymi.', 15), '26px 32px 0'))
H.append(row(price_table()
             + f'<p style="margin:10px 0 0;font-size:11px;line-height:1.5;color:{MUT};">Kwoty z koszyka synthagenlabs.com z rabatem Black Month i kodem VIAL. Cena za słoik zaokrąglona do grosza. Cena regularna: 239,00 zł za słoik.</p>', '16px 32px 0'))
H.append(row(button(vial('/pages/black-month', 'cta-tabela'), 'Zbuduj zestaw z kodem VIAL →'), '20px 32px 0'))

# biohacking
H.append(divider())
H.append(row(kicker('Biohacking') + h2('Jeden peptyd to początek. Plan to stack.')
             + p('Biohacking to nie pojedynczy produkt, tylko plan dnia, który sam układasz i obserwujesz. W Black Month są dwa proste sposoby, żeby go rozbudować i zapłacić mniej.', 15), '26px 32px 0'))
PEPS = [('semax_chat.png?v=1789764305', 'NL-SEMAX™', '/products/nl-semax-met-oktapeptyd'),
        ('selank_chat.png?v=1789764332', 'NL-SELANK™', '/products/nl-selank-oktapeptyd'),
        ('ghk_chat.png?v=1789764388', 'NL-GHK-Cu™', '/products/nl-ghk-cu-tetrapeptyd-cu')]
H.append(row(f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CARD};border:1px solid {LINE};border-radius:18px;"><tr><td style="padding:20px 18px;">
<p style="margin:0;{MONO}font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{ACC2};">1 · Stack peptydów NL</p>
<p style="margin:8px 0 0;font-size:17px;font-weight:bold;line-height:1.35;color:#FFFFFF;">Łącz peptydy, a próg rabatu liczy je razem.</p>
<p style="margin:8px 0 0;font-size:14px;line-height:1.55;color:{SUB};">Na przykład 15× NL-BPC-157™ i 15× NL-SEMAX™ to 30 słoików. To −50% z Black Month, a z kodem VIAL <b style="color:#FFFFFF;">107,55 zł za każdy słoik</b> (3 226,50 zł za całość zamiast 7 170,00 zł).</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;table-layout:fixed;"><tr>
{''.join(mini(CDN + "/" + f + "&amp;width=240", n, page(h, "stack-" + n.split("-")[1].rstrip("™").lower())) for f, n, h in PEPS)}
</tr></table>
<p style="margin:12px 0 0;font-size:12px;line-height:1.5;color:{MUT};">W linii NL są też NL-EPITHALON™ i NL-CORTAGEN™. Wszystkie liczą się do tego samego progu.</p>
</td></tr></table>''', '18px 32px 0'))
TRIO = [('bpc_chat.png?v=1789762734', 'NL-BPC-157™', '/products/nl-bpc-157-heksadekapeptyd'),
        ('gutbalance1_1.png?v=1789745039', 'GUT BALANCE™', '/products/gut-balance'),
        ('butyrate_1.png?v=1789745015', 'PURE BUTYRATE™', '/products/pure-butyrate-sodium-butyrate')]
H.append(row(f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CARD};border:1px solid {LINE};border-radius:18px;"><tr><td style="padding:20px 18px;">
<p style="margin:0;{MONO}font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{ACC2};">2 · Rutyna „Trzy drogi”</p>
<p style="margin:8px 0 0;font-size:17px;font-weight:bold;line-height:1.35;color:#FFFFFF;">Peptyd rano, dwie formuły do posiłku.</p>
<p style="margin:8px 0 0;font-size:14px;line-height:1.55;color:{SUB};">Rano NL-BPC-157™ na czczo, do posiłku GUT BALANCE™ i PURE BUTYRATE™. Trzy różne składniki bez dublowania, każdy słoik na 30 dni, więc wszystkie kończą się tego samego dnia.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;table-layout:fixed;"><tr>
{''.join(mini(CDN + "/" + f + "&amp;width=240", n, page(h, "trio-" + h.split("/")[-1][:12])) for f, n, h in TRIO)}
</tr></table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;border-collapse:collapse;">
<tr><td style="padding:9px 0;border-top:1px solid {LINE};font-size:13px;color:{SUB};">Trio na 30 dni (3 słoiki)</td><td align="right" style="padding:9px 0;border-top:1px solid {LINE};white-space:nowrap;"><span style="font-size:12px;color:{MUT};text-decoration:line-through;">657,00 zł</span> <b style="font-size:15px;color:#FFFFFF;">572,49 zł</b></td></tr>
<tr><td style="padding:9px 0;border-top:1px solid {LINE};font-size:13px;color:{SUB};">Trio na 90 dni (9 słoików)</td><td align="right" style="padding:9px 0;border-top:1px solid {LINE};white-space:nowrap;"><span style="font-size:12px;color:{MUT};text-decoration:line-through;">1 971,00 zł</span> <b style="font-size:15px;color:#FFFFFF;">1 572,35 zł</b></td></tr>
</table>
<p style="margin:8px 0 0;font-size:11px;line-height:1.5;color:{MUT};">Ceny z rabatem Black Month i kodem VIAL. Nutraceuticals mają własne progi, do −30% od 15 słoików.</p>
</td></tr></table>''', '14px 32px 0'))
H.append(row(button(vial('/pages/black-month', 'cta-biohacking'), 'Otwórz konfigurator z kodem VIAL →'), '20px 32px 0'))

# koniec + licznik
H.append(divider())
H.append(f'<tr><td align="center" style="padding:24px 32px 4px;"><a href="{vial("/pages/black-month", "timer")}" target="_blank"><img src="https://gen.sendtric.com/countdown/z9nk41lj4b" width="536" alt="Do końca Black Month" style="display:block;width:100%;max-width:536px;height:auto;border:0;"></a></td></tr>\n')
H.append(f'<tr><td align="center" style="padding:0 32px 4px;{MONO}font-size:11px;letter-spacing:1px;color:{MUT};">Black Month i kod VIAL działają do 30.11, 23:59</td></tr>\n')
H.append(row(button(vial('/products/nl-bpc-157-heksadekapeptyd', 'cta-final'), 'NL-BPC-157™ od 107,55 zł →'), '16px 32px 0'))
H.append(f'''<tr><td style="padding:22px 32px 0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid {LINE};border-bottom:1px solid {LINE};"><tr>
<td align="center" style="padding:12px 4px;font-size:12px;color:#A9B0D0;"><span style="color:#F2B300;">★★★★★</span> <b style="color:#FFFFFF;">4,8</b> · 353 opinie NL-BPC-157™</td>
<td align="center" style="padding:12px 4px;font-size:12px;color:#A9B0D0;">90 dni bez ryzyka</td>
<td align="center" style="padding:12px 4px;font-size:12px;color:#A9B0D0;">Darmowa wysyłka</td>
</tr></table></td></tr>
''')
# stopka
H.append(f'''<tr><td style="padding:24px 32px 32px;font-size:11px;line-height:1.6;color:#6E7598;text-align:center;">
NL-BPC-157™ jest suplementem diety. Suplement diety nie zastępuje zróżnicowanej diety. Nie przekraczaj porcji: 1 kapsułka dziennie. Jeśli przyjmujesz leki, chorujesz przewlekle, jesteś w ciąży albo karmisz piersią, skonsultuj stosowanie z lekarzem. BPC-157 jest na liście substancji zabronionych WADA (kategoria S0): jeśli podlegasz kontroli antydopingowej, nie stosuj produktu.<br><br>
Black Month trwa od 1.11.2026 do 30.11.2026, 23:59. Rabat zależy od liczby słoików z jednej linii w jednym zamówieniu (peptydy NL i Nutraceuticals liczą się osobno) i nalicza się automatycznie w koszyku. Kod VIAL daje dodatkowe 10% na całe zamówienie, łączy się z rabatem Black Month i jest ważny do 30.11.2026, 23:59. Najniższa cena z 30 dni przed obniżką: 239 zł za słoik peptydu NL, 209 zł za słoik GUT BALANCE™ i PURE BUTYRATE™.<br><br>
Otrzymujesz tę wiadomość, bo jesteś klientem Synthagen i wyraziłeś zgodę na otrzymywanie informacji handlowych. Masz pytanie? Odpisz na tego maila albo napisz na info@synthagen.co.<br><br>
Sprzedawca: AXIOM ONE sp. z o.o., os. Na Lotnisku 1/U23, 31-801 Kraków, KRS 0000860410<br><br>
<a href="{{{{amazonSESUnsubscribeUrl}}}}" style="color:{ACC2};">Wypisz się z listy</a>
</td></tr>

</table></td></tr></table>
</body></html>
''')
html = ''.join(H)
assert html.count('{{amazonSESUnsubscribeUrl}}') == 1 and '{{powitanie}}' in html and '{{preheader}}' in html
tpl = {'name': 'Fiolki → NL-BPC-157 (kod VIAL)',
       'subject': 'Peptyd bez strzykawki. NL-BPC-157™ od 107,55 zł z kodem VIAL',
       'preheader': 'Znasz peptydy z fiolek? Kapsułka zamiast igły, a z kodem VIAL dodatkowe −10% do rabatu Black Month.',
       'from_name': 'Synthagen Labs', 'from_email': 'newsletter@synthagen.co', 'reply_to': 'info@synthagen.co', 'html': html}
(D / 'fiolki-nl.html').write_text(html, encoding='utf-8')
(D / 'fiolki-nl.json').write_text(json.dumps(tpl, ensure_ascii=False), encoding='utf-8')
print('ok', len(html))
