# Advertoriale Synthagen

Statyczne advertoriale (Synthagen Journal) hostowane na Cloudflare Workers (static assets) pod https://synthagen.co/<slug>/ (route `synthagen.co/*`; reguła przekierowania „do sklepu” w strefie synthagen.co obejmuje tylko `/` i `www`). Każdy push na `main` buduje i wdraża Worker `advertoriale` (`npx wrangler deploy`).

| Ścieżka | Temat | Produkt |
|---|---|---|
| `/jelita/` | wzdęcia, ciężkość po posiłkach | GUT BALANCE™ (+ PURE BUTYRATE™) |
| `/stawy/` | sztywne stawy, witamina D zimą | VITAL OMEGA PRO™ (+ PURE OXILLIGENCE™) |
| `/odpornosc/` | sezon przeziębień, witamina D zimą | VITAL OMEGA PRO™ (+ PURE OXILLIGENCE™) |
| `/serce-mozg/` | mało ryb w diecie, EPA i DHA | VITAL OMEGA PRO™ (+ PURE OXILLIGENCE™) |
| `/wlosy-skora/` | włosy, paznokcie, skóra | NOVA CELLCARE™ (+ PURE OXILLIGENCE™) |
| `/cukier/` | zjazd energii po obiedzie | GLUCO AGEPROTECT™ (+ PURE OXILLIGENCE™) |
| `/po-antybiotyku/` | okres po antybiotykoterapii | GUT BALANCE™ (+ PURE BUTYRATE™) |
| `/trening/` | dieta wysokobiałkowa, mało błonnika | PURE BUTYRATE™ (+ GUT BALANCE™) |
| `/po-40/` | trzy procesy starzenia po 40-tce | zestaw PURE OXILLIGENCE™ + GLUCO AGEPROTECT™ + NOVA CELLCARE™ |
| `/regeneracja/` | wolniejsza regeneracja, zmęczenie, longevity | PURE OXILLIGENCE™ (+ NOVA CELLCARE™) |

Przycisk zakupu otwiera koszyk synthagenlabs.com (cart permalink) z wariantami „1 SZT” i atrybutem zamówienia `advertorial=<slug>`. Rabat Black Month (rabaty automatyczne Shopify, 1–30.11.2026) nalicza się w koszyku; progi są w `window.SGA.tiers` każdej strony.

Strony mają GTM `GTM-NLS27RR` i zdarzenie `advertorial_cta` w dataLayer. `/` przekierowuje na synthagenlabs.com.
