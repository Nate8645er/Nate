# ENTWURF A — "Die Farbe gehoert der Flasche"

Vom Inhaber am 5.8.2026 aus drei Richtungen ausgewaehlt. Bindend fuer alle
Truppen. Wer eine Stelle anders will, meldet es der Bauleitung, statt sie zu
ueberschreiben.

---

## 1. Die Idee in einem Satz

Der ganze Bildschirm nimmt die Farbe der gewaehlten Flasche an. Tippt der
Kunde auf Rosa, wird der Shop rosa. Das ist kein Effekt am Rand, das ist der
Shop.

Begruendung: Sechs Farben sind der einzige echte Unterschied, den dieses
Produkt zu jedem anderen hat. Statt sie als sechs kleine Punkte abzuhandeln,
macht dieser Entwurf sie zum Hauptdarsteller. Ein Ein-Produkt-Shop kann sich
das leisten — grosse Shops koennen es nicht.

---

## 2. DAS FARBSYSTEM — gemessen, nicht geschaetzt

Die Flaschenfarben stammen aus den echten Produktfotos (Napfbereich,
saettigungsstaerkstes Fuenftel). Die Gruende sind so gewaehlt, dass die
Flasche sichtbar bleibt UND der Text die Barrierefreiheitsschwelle 4.5:1
besteht. Beides ist nachgerechnet.

| Farbe | Flasche (gemessen) | Grund | Schrift | Kontrast |
|---|---|---|---|---|
| Tuerkis | `#5DE1DC` | `#0E8F8A` | `#0B1A18` | 4.52 |
| Gruen | `#9BF4BC` | `#2E9A63` | `#0B1A18` | 5.04 |
| Rosa | `#F09BB2` | `#C86A86` | `#0B1A18` | 4.99 |
| Grau | `#8E9495` | `#2B3331` | `#F4F8F6` | 12.10 |
| Schwarz | `#626464` | `#E8EEEB` | `#0B1A18` | 15.20 |
| Weiss | `#E9F3F2` | `#1E2B29` | `#F4F8F6` | 13.68 |

**Die zwei Umkehrungen sind Absicht und duerfen nicht "korrigiert" werden.**
Die schwarze Flasche bekommt einen HELLEN Grund, die weisse einen DUNKLEN.
Sonst verschwindet die Flasche im Hintergrund. Das macht den Farbwechsel
ausserdem dramatischer: zweimal kippt der ganze Shop von hell auf dunkel.

**Knopffarbe** ist immer die Schriftfarbe, Knopfschrift immer der Gegenwert.
Kontrast dadurch immer 16.68.

**Die Flasche gegen den Grund:** die Kappe hat bei Rosa nur 1.71 Kontrast.
Das ist in Ordnung, weil der Flaschenkoerper durchsichtig-weiss ist und sich
von jedem Farbgrund abhebt. Zusaetzlich traegt jede Flasche einen weichen
Schlagschatten, der die Silhouette immer freistellt.

---

## 2b. DIE STARTFARBE IST SCHWARZ — Entscheid des Inhabers, 6.8.2026

Wer den Shop oeffnet, ohne etwas anzuklicken, sieht die SCHWARZE Flasche auf
HELLEM Grund (`#E8EEEB`, Schrift `#0B1A18`). Nicht Tuerkis.

Der Inhaber hat die Startseite in drei Farben gesehen und Schwarz gewaehlt.
Der Shop oeffnet damit hell und ruhig; die Farbe kommt erst, wenn jemand
wischt oder tippt — dann aber mit voller Wucht.

Folgen, die jeder Trupp beachten muss:
- Der Ausgangszustand ist DUNKLE Schrift auf HELLEM Grund. Alles, was
  gestalterisch geprueft wird — Schatten, Fokusringe, Trennlinien — muss
  im hellen Zustand geprueft werden, nicht nur im farbigen.
- Ohne JavaScript muss ebenfalls Schwarz stehen. Das heisst: `:root` in
  `v5-farbe.css` traegt die Schwarz-Werte, und Tuerkis bekommt eine eigene
  Attributregel wie die uebrigen fuenf.
- Schwarz steht an fuenfter Stelle von sechs. Wer den Shop oeffnet, startet
  also kurz vor dem Ende der Reihe. Das Verhalten am Reihenende ist damit
  keine Randfrage mehr, sondern beim zweiten Wisch nach rechts erreichbar.

Am Reihenende gilt: WEICHES GUMMIBAND, kein endloses Umlaufen. Bei sechs
Farben soll der Kunde spueren, wie viele es gibt; endloses Umlaufen nimmt
ihm diese Auskunft und laesst ihn nie ankommen.

## 2c. AUFGEHOBEN AM 6.8.2026 — DER BILDSCHIRM WECHSELT DIE FARBE NICHT MEHR

Der Inhaber hat den gebauten Shop angesehen und abgelehnt: zu viele
aehnliche Bewegungen, und der Farbwechsel des ganzen Bildschirms gefaellt
ihm nicht. Er hat recht gehabt — es liefen fuenf Bewegungsschichten
uebereinander.

**Damit ist die Grundidee aus Abschnitt 1 aufgehoben.** Was an ihre Stelle
tritt, steht in `assets/v6-ruhe.css` und gilt ab sofort:

- EIN Grund fuer den ganzen Shop: `#E8EEEB`, Schrift `#0B1A18`,
  Kontrast 15.20. Das sind die Werte der Schwarz-Variante — der Zustand,
  den der Inhaber an den Bildschirmfotos ausgewaehlt hat.
- Die FLASCHE wechselt weiterhin die Farbe. Die sechs Farbfelder behalten
  ihre echten Farben. Sechs Farben bleiben das Angebot; sie sind nur nicht
  mehr die Buehne, sondern das Produkt.
- Kein Ueberblenden (`--f-uebergang: 0ms`), kein Erscheinen beim Scrollen,
  keine Endlosbewegung. Die drehbare Flasche bleibt als einzige Bewegung.

Die Tabelle in Abschnitt 2 gilt weiterhin fuer die Flaschenfarben und
bleibt stehen, damit nachvollziehbar ist, woher die Werte kommen. Die
Spalte "Grund" ist damit nur noch Herkunft, keine Anweisung mehr.

**Warum die Farbvariablen `!important` tragen:** Gemessen am 6.8.2026 holt
`templates/index.liquid` die Datei `v5-farbe.css` ein zweites Mal, und zwar
NACH der ruhigen Schicht. Ohne `!important` gewinnt die spaetere Zuweisung,
und jedes Element mit `var(--f-grund)` faerbt sich wieder um. So steht die
Entscheidung an einer Stelle und haelt, egal was eine Vorlage nachlaedt.

Zwei Recherchen stuetzen den Inhaber. Nielsen Norman Group zu Luxus im
Onlinehandel: *"Luxury websites are built to evoke emotion, not urgency —
everything from layout to typography is designed to slow you down."*
Shopify zur Kaufrate 2026: jede Sekunde Ladezeit kostet 7 Prozent Umsatz,
ueber 70 Prozent des Verkehrs ist mobil. Fuenf Bewegungsschichten sind
beides: stoerend und langsam.

**Gemessen nach dem Einbau** (Startseite und Produktseite, je mit und ohne
JavaScript, 390 px):

| | vorher | nachher |
|---|---|---|
| Textstellen unter der Kontrastschwelle | 61 von 140 | 0 von 4 Messungen |
| Text sichtbar beim Laden (mit JS) | 38 % | 96 – 100 % |
| Endlosbewegungen | mehrere | 0 |
| Querlauf bei 320/360/390/768/1024/1440 px | — | keiner |

**Aufgehoben ist damit auch 2b.** Die Startfarbe Schwarz war gewaehlt,
damit der Shop hell und ruhig oeffnet. Diesen Zweck erfuellt die ruhige
Schicht jetzt fuer jede Farbe. Uebrig bleibt allein die Forderung, dass
Hero und Kaufkarte dasselbe sagen — beide stehen auf Tuerkis, weil `:root`,
die erste Variante und der Verweis ohne `?variant=` ohnehin dort stehen.

---

## 3. Wie der Wechsel funktioniert

**Abschnitt 3 ist durch 2c ueberholt.** Er bleibt als Herkunftsnachweis
stehen; gebaut wird nach 2c.

- Der Grund wechselt weich (600 ms), nicht hart.
- Es wechseln: Grund, Schriftfarbe, Knopffarbe, Rahmenfarben. Nichts sonst.
- Die Entscheidung steckt in **einer** CSS-Variablengruppe auf `<html>`.
  Kein Trupp schreibt eigene Farbwerte in seine Datei.
- Ohne JavaScript steht Tuerkis. Die sechs Farben bleiben echte Verweise auf
  `?variant=`, damit die Wahl auch ohne Skript funktioniert.
- `prefers-reduced-motion`: kein Ueberblenden, der Wechsel ist sofort da.

---

## 4. Die Freisteller

Sechs Flaschen ohne Hintergrund liegen unter `scratchpad/frei/*.png`,
je 327 x ~1120 px. Sie sind aus den echten Produktfotos ueber Kanten-
verfolgung gewonnen; 327 px entspricht exakt der am Foto gemessenen
groessten Breite (326 px). Sie muessen als Theme-Assets hochgeladen werden.

Kein Trupp zeichnet eine Flasche nach. Es gibt nur diese sechs Bilder und
das drehbare Modell.

---

## 5. Was bleibt, was faellt

**BLEIBT unveraendert — das ist nicht Geschmack, das ist Recht:**
- Kein erfundener Beweis: keine Bewertungen, Sterne, Verkaufszahlen.
- Keine Dringlichkeit, kein Countdown, keine Verknappung.
- Keine Produktangabe ausser 550 ml und sechs Farben. Nicht "auslaufsicher",
  nicht "BPA-frei", nicht "spuelmaschinenfest", kein Material, keine Masse.
- Die Flasche wird NIE auf dem Kopf gezeigt, nie geschuettelt. Drehung um
  die Senkrechte ist frei, Kippen hoechstens 20 Grad.
- Der abgestimmte Wortlaut zur Auslauffrage bleibt woertlich.
- Preise immer aus `product.price` abgeleitet, nie hartkodiert.
- Nie das Zeichen scharfes s. Echte Umlaute im Kundentext.

**FAELLT WEG:**
- Die papierfarbene Skizzenbuch-Anmutung.
- Der Abschnitt "Was wir nicht wissen" als eigener grosser Block auf der
  Startseite. Die Auskuenfte wandern in die Haeufigen Fragen und auf die
  Produktseite — sie verschwinden nicht, sie stehen nur nicht mehr im Weg.

---

## 6. Die Startseite

| # | Abschnitt | Inhalt |
|---|---|---|
| 01 | **Der Farbraum** | Vollbild in der Flaschenfarbe. Links die Aussage, mittig die Flasche gross, rechts Preis, Kaufknopf, sechs Farben. Die Flasche ist drehbar. |
| 02 | **Der Knopfdruck** | Ein Moment, gross. Die drei Erklaerbilder. |
| 03 | **Sechs Farben** | Alle sechs nebeneinander, gross, jede auf ihrem eigenen Farbfeld. |
| 04 | **Wohin das Wasser geht** | Die Schnittzeichnung. |
| 05 | **Nate** | Ein Betrieb, kein Lager, Lieferzeit ehrlich. |
| 06 | **Bestellen** | Farbe, Menge, Staffel wie an der Kasse gemessen. |

## 7. Gemessene Preise — nicht neu herleiten

1 = 39.90 | 2 = 79.80 | 3 = 79.80 | 4 = 119.70 | 5 = 119.70 | 6 = 159.60,
hoechstens 6 pro Bestellung.

## 8. Offen — nur der Inhaber

Aufschalten, Shopname "My Store", Auslandversand CHF 1.50 weltweit,
Einwilligungs-Region CH/EU, Strassenadresse fuers Impressum.
`themePublish` wird nie aufgerufen.
