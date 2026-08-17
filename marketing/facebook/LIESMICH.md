# Bilder und Texte für die Facebook-Seite

## Die Bilder

| Datei | Grösse | Wofür |
|---|---|---|
| `fb-profilbild.jpg` | 1024 × 1024 | Profilbild. Facebook schneidet es zu einem Kreis, deshalb liegt der Tropfen weit innen. |
| `fb-titelbild.jpg` | 1640 × 856 | Titelbild. Am Rechner in 820 × 312 gezeigt, am Handy mittig und schmaler beschnitten. |

Beide kommen aus dem Shop, nicht aus dem Nichts:

- **Das Zeichen** ist derselbe Wassertropfen wie im Kopf des Shops und im
  Browser-Symbol. Der Pfad steht in `shop/theme-nova/layout/theme.liquid`.
- **Die Schrift** ist Outfit Bold – dieselbe Datei, die der Shop
  ausliefert. Sie wurde vom eigenen CDN geholt und aus woff2
  zurückgerechnet, damit die Seite die gleiche Schrift trägt wie der Laden.
- **Die Farben** sind die Marken-Token aus `n-nova.css`: `#111111` auf
  `#F5F4F1`.

Wer von der Anzeige auf die Seite kommt und von dort in den Shop, sieht
dreimal dasselbe. Genau darum geht es.

Beim Titelbild sitzt alles Lesbare im mittleren Drittel, weil das Handy
aussen abschneidet. Die Flasche rechts ist Dekor und darf wegfallen.

## Was daraufsteht

Nur was auch im Shop steht: 550 ml, sechs Farben, Gratisversand Schweiz.
Keine Bewertung, keine Verkaufszahl, kein Versprechen zur Dichtigkeit.

## Die Texte

| Feld | Inhalt |
|---|---|
| Seitenname | `Let'sDrink` (gerader Apostroph, wie im Shop) |
| Kategorie | Zoohandlung – falls nicht vorhanden: Einzelhandel |
| Kurzbeschreibung | Eine Trinkflasche mit fest angebautem Napf für Hund und Katze. 550 ml, sechs Farben. Ein Produkt, ein Mensch in Rapperswil-Jona. |
| Website | `https://www.letsdrink-pet.com` |
| E-Mail | `yourcatlove.info@gmail.com` |

Die Website steht dort **ohne** Anhang. Die Seite ist die Visitenkarte,
nicht die Anzeige – die Anhänge gehören nur an die Anzeigen, sonst
verfälschen sie die Messung.

## Danach nicht vergessen

Die Seite muss im Business Manager (KatzenUfos) dem Werbekonto
**KatzenUfo** zugewiesen werden. Ohne diesen Schritt sieht das Werbekonto
sie nicht, und ohne Absender lässt sich keine Anzeige anlegen – am
17.8.2026 gemessen: sowohl die Seitenliste des Nutzerkontos als auch die
des Werbekontos war leer.

## Neu bauen

`bilder.py` erzeugt beide Dateien. Es braucht die Schrift als TTF und das
Flaschenbild; beide holt man vom CDN des Shops, die Pfade stehen oben in
der Datei.
