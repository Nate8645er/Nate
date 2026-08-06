=== GEMESSENE ZAHLEN ===

Gemessen am 6.8.2026 an der Vorschau des unveroeffentlichten Themes, mit
Chromium auf einem lokalen Spiegel, Startseite und Produktseite, jede
zweimal: mit JavaScript und ohne.

Kontrast: jede sichtbare Textstelle gegen ihren wirksamen Grund, durch
die ganze Elternkette hindurch aufgebaut, halbdurchsichtige Schichten
uebereinandergelegt. Schwelle 4.5 zu 1, bei grosser Schrift 3.0 (WCAG).

| Messung | Startseite JS | Startseite ohne JS | Produkt JS | Produkt ohne JS |
|---|---|---|---|---|
| Textstellen | 142 | 139 | 170 | 158 |
| davon unter der Kontrastschwelle | 0 | 0 | 0 | 0 |
| sofort sichtbar beim Laden | 96 % | 96 % | 100 % | 100 % |
| Endlosbewegungen | 0 | – | 0 | – |
| Querlauf bei 320/360/390/768/1024/1440 px | keiner | – | keiner | – |

Die 4 Prozent nicht sichtbarer Textstellen auf der Startseite sind die
Farbnamen der fuenf nicht gewaehlten Bilder im Wischkarussell. Das ist
gewollt: nur der Name der aktuellen Farbe steht da.

Vorher, vor dem Umbau am selben Tag: 61 von 140 Textstellen auf der
Produktseite unter der Schwelle, 38 Prozent des Textes beim Laden
unsichtbar, mehrere Endlosbewegungen, und beim Farbwechsel 210 bis 350
Millisekunden vollstaendig unlesbarer Text auf 4 von 6 Umschaltungen.

=== WAS DER SHOP TECHNISCH TUT ===

- Ein einziger ruhiger Grund fuer den ganzen Shop (#E8EEEB, Schrift
  #0B1A18, Kontrast 15.2). Der Bildschirm faerbt sich NICHT um.
- Die Flasche wechselt die Farbe; die sechs Farbfelder zeigen ihre
  echten Farben, aus den Produktfotos gemessen.
- Eine einzige Bewegung bleibt: die Flasche laesst sich mit dem Finger
  um die Senkrechte drehen (360-Grad-Ansicht).
- Ohne JavaScript bleibt alles lesbar und kaufbar. Die Farbwahl sind
  echte Verweise auf ?variant=, keine Skript-Schalter.
- Schriften vom Shopify-CDN statt von Google (vorher hatte Google die
  IP jeder Besucherin, bevor sie etwas angeklickt hatte).
- Strukturierte Daten fuer Organisation, Website, Breadcrumb, Produkt
  und FAQ. Ausdruecklich OHNE aggregateRating - der Shop hat null
  Bewertungen.
- robots: Warenkorb, Suche, Fehlerseite und Kundenkonto auf noindex.

=== DIE HALTUNG DES BETREIBERS ===

Er nennt auf der Produktseite in einem eigenen Abschnitt "Was wir nicht
wissen" offen fuenf Dinge, die sein Lieferant ihm NICHT schriftlich
bestaetigt hat: das Material, die genauen Masse, das Gewicht, die
Spuelmaschinentauglichkeit und ob die Flasche unter allen Umstaenden
dicht ist. Zur Auslauffrage steht woertlich:

  "Wir haben keine schriftliche Zusicherung des Lieferanten, dass sie
   unter allen Umstaenden dicht ist - deshalb behaupten wir es auch
   nicht. Transportiere sie am besten aufrecht. Laeuft deine Flasche
   trotzdem aus, ist das ein Reklamationsfall: Du bekommst Ersatz oder
   dein Geld zurueck."

Die Lieferzeit erklaert er, statt sich zu entschuldigen: kein Lager,
7 bis 14 Werktage, weil jede Flasche erst nach der Bestellung losgeschickt
wird.

=== PREISE UND VERSAND (an der Kasse gemessen) ===

1 Flasche 39.90 | 2 = 79.80 | 3 = 79.80 | 4 = 119.70 | 5 = 119.70 |
6 = 159.60. Hoechstens 6 pro Bestellung.
Also: bei 3 bezahlst du fuer 2, bei 5 fuer 3, bei 6 fuer 4.
Gratisversand in der Schweiz. 14 Tage Rueckgabe ohne Begruendung.
Lagerbestand ist auf "weiterverkaufen" gestellt (Dropshipping).

=== WAS NOCH OFFEN IST - und nur der Inhaber kann es ===

1. DER SHOP IST NICHT AUFGESCHALTET. Die Domain katzenufos.com liefert
   bis jetzt eine voellig andere Website: eine KI-Agentur-Seite mit dem
   Titel "My Store" und der Ueberschrift "Geben Sie den Auftrag - Ihre
   KI-Abteilung liefert das fertige Ergebnis". Der Trinkflaschen-Shop
   ist fertig gebaut, aber unveroeffentlicht. Im Moment kann niemand
   etwas kaufen.
2. Der Shopname steht in den Einstellungen auf "My Store". Er erscheint
   unter anderem in Apple Pay an der Kasse.
3. Auslandversand ist auf CHF 1.50 weltweit eingestellt - vermutlich
   ein Versehen, das bei jeder Auslandbestellung Geld kostet.
4. Die Einwilligungs-Region fuer Meta- und TikTok-Pixel muss auf CH/EU
   gestellt werden. Ein Einwilligungsbanner ist gebaut und funktioniert,
   kann aber den ERSTEN Seitenaufruf nicht blockieren - das entscheidet
   eine Einstellung im Shopify-Adminbereich, nicht das Theme.
5. Kein einziger Verkauf bisher. Keine Werbung geschaltet. Keine
   Reichweite. Keine E-Mail-Liste.

=== WAS ES AN WERBUNG GIBT ===

Vier Motive in je drei Formaten (4:5, 9:16, 1:1), gebaut aus den echten
Produktfotos mit der Schrift des Shops: "Ein Knopf. Ein Napf.",
"Sechs Farben. Eine Flasche.", "CHF 39.90" mit den Bedingungen, und
"Ich schreibe hin, was ich weiss - und was nicht." Noch nirgends
geschaltet.
