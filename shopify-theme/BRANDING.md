# Branding-Konzept

Das Theme heisst **Aurum Premium** und ist markenneutral gebaut: Name, Logo, Farben
und Schriften werden vollständig über die Theme-Settings gesteuert. Das folgende
Branding ist der empfohlene Standard – als Beispiel ausgearbeitet für einen
Premium-Shop im deutschsprachigen Raum (Schweiz).

## Markenname

**AURUM** – lateinisch für Gold. Kurz, einprägsam, international aussprechbar,
funktioniert als Domain (`aurum-shop.ch` o. ä.) und lässt sich auf fast jede
Premium-Nische übertragen. Alternativ: den bestehenden Store-Namen beibehalten –
alle Texte im Theme referenzieren automatisch `{{ shop.name }}`.

## Slogan

> **„Qualität, die man jeden Tag spürt."**

Kurz, sensorisch, nutzenorientiert – kein Buzzword. Varianten für Ads:
„Gute Produkte. Ehrlicher Service. Keine Kompromisse."

## Markenstory (Kurzfassung, im Theme hinterlegt)

Gegründet aus Frust über anonyme Onlineshops: lange Lieferzeiten, keine
Antworten, enttäuschende Qualität. Die Antwort: ein Shop, in dem jedes Produkt
persönlich getestet wird, jede Bestellung in 24 h das Lager verlässt und jede
E-Mail von einem Menschen beantwortet wird. Die 30-Tage-Geld-zurück-Garantie ist
kein Marketing-Gag, sondern die logische Folge: Wer seine Produkte kennt, kann
dahinterstehen.

## Logo-Idee

- **Wortmarke** in der Headline-Schrift (Playfair Display), gesperrt gesetzt
  (Letter-Spacing ca. 0.12 em), in Dunkelgrün `#1F3D2B`.
- Optionales Signet: ein minimalistischer Kreis mit Initiale – funktioniert als
  Favicon und Social-Media-Avatar.
- Umsetzung: als SVG/PNG mit transparentem Hintergrund in den Theme-Settings
  hochladen (Empfehlung: 520 px Breite, wird auf 140 px angezeigt → scharf auf
  Retina). Im Footer wird das Logo automatisch weiss eingefärbt.

## Farbkonzept

| Rolle | Farbe | Verwendung |
| --- | --- | --- |
| Primär | `#1F3D2B` Dunkelgrün | Header-Akzente, Buttons, Footer, Vertrauen |
| Akzent | `#E8823A` Warmes Orange | CTAs, Sale-Badges, Sterne – EIN Akzent, konsequent |
| Hintergrund | `#FAF7F2` Warmweiss | Seitenhintergrund (kein reines Weiss) |
| Hintergrund soft | `#F1EBE2` Sand | Abgesetzte Sections, Karten |
| Text | `#20201D` Warmschwarz | Fliesstext (kein reines Schwarz) |

Kontrast: Fliesstext auf Hintergrund ≥ 4.5:1, Weiss auf Dunkelgrün ≥ 7:1.

## Schriftarten

- **Headlines:** Playfair Display (Serifenschrift → Luxus, Editorial-Charakter)
- **Body/UI:** Assistant (klare Sans – im Shopify-Font-CDN enthalten, kein
  externer Google-Fonts-Request). Wer Inter bevorzugt: in den Theme-Settings
  unter Typografie wechseln, falls im Font-Picker verfügbar.

Beide Schriften laufen über Shopifys Font-CDN mit `font-display: swap` –
schnell und DSGVO/DSG-unkritisch (kein Google-Server-Kontakt).

## Tonalität

Deutsch, informell („du"), klar und ehrlich. Keine Superlative ohne Beleg, keine
Buzzwords. Jede Behauptung (Versand in 24 h, Geld-zurück-Garantie) muss
operativ eingelöst werden – sonst aus den Settings entfernen.
