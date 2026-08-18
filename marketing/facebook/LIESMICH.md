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
| Kurzbeschreibung | 🐾 Wasser dabei, Napf inklusive. 550 ml, sechs Farben. 💧 Gratisversand in die Schweiz |
| Website | `https://www.letsdrink-pet.com` |
| E-Mail | `yourcatlove.info@gmail.com` |

Die Website steht dort **ohne** Anhang. Die Seite ist die Visitenkarte,
nicht die Anzeige – die Anhänge gehören nur an die Anzeigen, sonst
verfälschen sie die Messung.

## Die Seite steht

Am 18.8.2026 angelegt und vom Connector gemessen sichtbar:

| | |
|---|---|
| Seite | `Lets'drink`, **page_id 1189244220947958** |
| Konto | dasselbe, das die Werbekonten hält (Nate Murseli) |

Diese ID ist der Absender für alle Anzeigen.

Zwei tote Seiten daneben, die nicht benutzt werden: `let'sdrink`
(1282415524951154, leer, erster Anlauf) und `Let'Drink` auf dem zweiten
Facebook-Konto.

Der Name trägt noch den Apostroph an der falschen Stelle; richtig ist
`Let'sDrink`. Solange die Seite frisch ist, geht eine Umbenennung ohne
Prüfung durch.

Die Seite muss dem Werbekonto **nicht** eigens zugewiesen werden – sie
füllt die Liste des Werbekontos von selbst, sobald die erste Anzeige
läuft. Was fehlt, ist etwas anderes: der **Pixel** hängt an keinem
Werbekonto. Ohne ihn lässt sich nicht auf Käufe optimieren.

## Neu bauen

`bilder.py` erzeugt beide Dateien. Es braucht die Schrift als TTF und das
Flaschenbild; beide holt man vom CDN des Shops, die Pfade stehen oben in
der Datei.

## Die Rückgabefrist

**14 Tage, nicht 30.** Ich hatte in einem Entwurf einmal 30 geschrieben.
Die Produktseite sagt an sechs Stellen 14. Wo in diesen Unterlagen eine
Frist steht, ist es diese.
