# Kampagnenplan Meta

Stand 18.8.2026. Alle Zahlen unten sind gemessen oder als Annahme
gekennzeichnet – keine Faustregel aus dem Netz.

## Was eine Bestellung tragen kann

| Posten | Betrag | Herkunft |
|---|---|---|
| Verkaufspreis | CHF 37.91 | live an der Produktseite gelesen |
| Einkauf 550 ml | CHF 6.30 – 6.55 | DSers, USD 7.76–8.07 zum Kurs 0.811773 |
| Zahlungsgebühr | rund CHF 1.00 | **Annahme**, Kartensatz nicht geprüft |
| Versand des Lieferanten | **unbekannt** | nicht belegt, fehlt in der Rechnung |
| **Bleibt je Flasche** | **rund CHF 30** | |

Das ist die Obergrenze dessen, was eine Bestellung in der Werbung
kosten darf, bevor Nate draufzahlt. Für Gewinn sollte der Wert bei
höchstens der Hälfte liegen, also **CHF 15 je Bestellung**.

Der Lieferantenversand fehlt in dieser Rechnung. Solange er unbekannt
ist, gilt die CHF 30 als zu hoch angesetzt, nicht als sicher.

## Das Problem, das vor dem Budget kommt

Am 18.8.2026 aus dem Pixel gelesen, letzte sieben Tage:

| Ereignis | Anzahl |
|---|---|
| Seitenaufruf | 542 |
| Produkt angesehen | 7 |
| In den Warenkorb | 2 |
| Kasse begonnen | 2 |
| **Kauf** | **0** |

**Meta kann nicht auf Käufe optimieren, die es nie gesehen hat.** Ein
Anzeigensatz braucht rund 50 Ereignisse seiner Optimierungsart pro
Woche, um aus der Lernphase zu kommen. Bei null Käufen startet die
Kampagne blind.

Deshalb nicht sofort auf Kauf optimieren, sondern in zwei Stufen:

**Stufe 1 – auf „In den Warenkorb"**, bis rund 50 Käufe zusammen sind.
Das Ereignis kommt häufiger und gibt Meta früher etwas zu lernen. Es
ist ein Umweg, aber ein kürzerer als wochenlang blind zu fliegen.

**Stufe 2 – auf „Kauf" umstellen**, sobald der Pixel genug Käufe
gesehen hat. Ab dann sucht Meta Käufer statt Klicker.

## Wohin die Anzeigen zeigen — geändert am 18.8.2026

Auf die **Startseite** `https://www.letsdrink-pet.com/`, nicht mehr auf
die Produktseite. Die ausführliche Begründung samt Gegenüberstellung
steht in `TEXTE.md`. Kurz: die Startseite ist die vollständigere
Verkaufsseite und hat als einzige die Mengenstaffel und die
Sechs-Farben-Galerie; die niedrige Zahl „Produkt angesehen" war eine
Messlücke des Shopify-Pixels, kein Urteil über die Seite.

Folge für die Umsetzung: die vier bereits angelegten Werbemittel
tragen die alte Adresse fest eingebrannt. Es braucht vier neue —
gleiche Bilder von der Shopify-CDN, gleiche Texte, andere Zieladresse.
Sie entstehen zusammen mit dem Anzeigensatz, sobald der Pixel hängt,
damit nicht noch mehr unbenutzte Werbemittel in der Bibliothek liegen.

## Was am Messtag sonst noch in der Schweiz lief

In der Meta-Werbebibliothek gesucht, 18.8.2026:

| Suche | Land | aktive Anzeigen |
|---|---|---|
| „Hundetrinkflasche" | CH | **0** |
| „Trinkflasche Hund Napf unterwegs" | CH | **0** |
| „Hundetrinkflasche" | DE + AT + CH | 10 |

Für dieses Produkt wirbt in der Schweiz gerade niemand. Das heisst
nicht automatisch „freie Bahn" — es kann auch heissen, dass es schon
jemand versucht und wieder abgestellt hat. Wissen tun wir es nicht.

**Der unbequeme Teil:** `tatzio.de` verkauft für EUR 34.95–37.95 eine
Flasche mit 1000 ml, Edelstahl 304, Vakuumisolierung und drei
Futterfächern. Zum selben Geld das deutlich bessere Gerät. Was uns
schützt, ist Geografie, nicht das Produkt: Tatzio bewirbt Deutschland,
rechnet in Euro und verlangt EUR 5.90 Versand. Steht dieser Vergleich
je nebeneinander, verlieren wir ihn. Die Einzelheiten stehen in
`.agents/product-marketing.md`.

## Aufbau

```
Kampagne      Ziel: Umsatz, ein Anzeigensatz, kein Budget je Anzeigensatz
  Anzeigensatz  Schweiz · alle Geschlechter · 25–65 · breit, ohne Interessen
    Anzeige 1     Motiv Bank      + Satz 3
    Anzeige 2     Motiv Napf      + Satz 2
    Anzeige 3     Motiv Farben    + Satz 1
    Anzeige 4     Motiv Bank      + Satz 4   (der ehrliche, gegen Satz 3)
```

**Breit statt Interessen.** Bei einem Tagesbudget in dieser Grösse ist
jede Einengung verschenkte Lernmasse. Meta findet die Zielgruppe
schneller selbst, als Nate sie raten kann.

**Ein Anzeigensatz, vier Anzeigen.** Vier Anzeigensätze mit je einem
Motiv würden das Budget vierteln und jeden einzelnen in der Lernphase
verhungern lassen.

## Budget

Gemessen: das Werbekonto lässt ein Mindest-Tagesbudget von **CHF 0.82**
zu. Das ist die technische Untergrenze, nicht die sinnvolle.

**Vorschlag: CHF 20 pro Tag.** Bei einem Zielwert von CHF 15 je
Bestellung sind das gut eine Bestellung täglich, wenn es funktioniert –
genug Signal, um nach zwei Wochen etwas zu wissen. Weniger als CHF 10
und die Kampagne lernt nie aus.

## Wann abbrechen

- **Nach CHF 200 ohne eine einzige Bestellung:** anhalten. Dann liegt
  es nicht an den Anzeigen, sondern an der Seite oder am Preis. Weiter
  zu zahlen kauft nur teurere Gewissheit.
- **Nach CHF 100 ohne einen einzigen Warenkorb:** Motive tauschen. Wenn
  niemand den Knopf drückt, hat das Bild nicht überzeugt.
- **Erste sieben Tage nichts anfassen.** Jede Änderung wirft den
  Anzeigensatz zurück in die Lernphase.

## Zwei Dinge, die vor dem Start geklärt sein müssen

**Rosa ist beim Lieferanten leer.** Das Motiv „Sechs Farben" zeigt alle
sechs, darunter eine, die niemand bestellen kann. Gelogen ist das
nicht – die Seite weist Rosa als ausverkauft aus –, aber jeder Klick,
der wegen Rosa kommt, ist bezahlt und verloren. Entweder Nachschub
besorgen oder mit den anderen drei Motiven starten.

**Der Pixel hängt an keinem Werbekonto.** Ohne das läuft Stufe 1 gar
nicht. Das ist der einzige harte Blocker.

## Was ich anlege, sobald der Pixel hängt

Kampagne, Anzeigensatz und vier Anzeigen – **alle pausiert**. Nichts
startet von selbst, nichts kostet etwas, bevor Nate es angeschaut und
selbst auf „Aktivieren" gedrückt hat.

---

# Was am 18.8.2026 angelegt wurde

Alles **pausiert**. Nichts liefert aus, nichts kostet.

## Kampagne

| | |
|---|---|
| Name | `Let'sDrink · Verkauf · Start CH` |
| ID | `120250903005380251` |
| Ziel | OUTCOME_SALES |
| Budget | CHF 20 pro Tag, auf Kampagnenebene (CBO) |
| Gebotsstrategie | LOWEST_COST_WITHOUT_CAP |
| Status | PAUSED |

Meta empfiehlt für dieses Ziel selbst `OFFSITE_CONVERSIONS` als
Optimierung – genau das, was ohne Pixel am Werbekonto nicht geht.

## Werbemittel - angelegt, aber ueberholt

| Motiv | Creative-ID |
|---|---|
| A1 Hand · Wasser dabei, Napf inklusive | `1698306971276574` |
| A2 Hund · Der Napf ist schon dran | `2010420012844133` |
| A3 Rucksack · Im Rucksack dabei | `1064921423145405` |
| Farben · Sechs Farben, eine Flasche | `1070643555444117` |

Bilder und Texte dieser vier stimmen weiterhin. Nur die Zieladresse
ist ueberholt - sie zeigen auf die Produktseite. Weil Meta die Adresse
in einem bestehenden Werbemittel einfriert, werden sie durch vier neue
ersetzt, die auf die Startseite zeigen. Angelegt zusammen mit dem
Anzeigensatz.

### Und die toten daneben

Fuenf Werbemittel im Konto sind Ausschuss und werden nicht benutzt:
`1404686871521712`, `1104575722240401`, `1837253994367029`,
`1588790252881607`, `1419096773440701`.

Zwei aus der ersten Runde, in der die Textflaeche das Produkt verdeckte;
drei aus der zweiten, in der der Verlauf zu schwach war. Ein Bild laesst
sich in einem bestehenden Werbemittel nicht austauschen - Meta friert es
beim Anlegen ein -, also musste jede Korrektur ein neues Werbemittel
werden.

`ads_creative_delete` ist fuer dieses Werbekonto nicht freigeschaltet.
Sie stehen also weiter in der Bibliothek, haengen aber an keiner
Anzeige und kosten nichts. Im Werbeanzeigenmanager lassen sie sich von
Hand loeschen.

Alle drei mit Absender Seite `1189244220947958`, Knopf „Jetzt einkaufen",
Ziel die Produktseite, Anzeigename `letsdrink-pet.com`.

## Umweg beim Bild

`ads_creative_upload_image` ist für dieses Werbekonto nicht
freigeschaltet – dieselbe Meldung wie beim Video-Upload. Statt dessen
liegen die drei Bilder jetzt in Nates Shopify-Dateien und die
Werbemittel verweisen direkt auf die CDN-Adresse. Das nimmt die
Schnittstelle an.

Nebenwirkung: die Bilder stehen damit auch im Shopify-Dateibereich.
Sie stören dort nicht, lassen sich aber jederzeit löschen – dann
brechen allerdings die Werbemittel.

## 18.8.2026 abends: Anzeigensatz steht, Anzeigen scheitern

Nate kam nicht mehr in sein Meta-Konto (Bestaetigung haengt an einer
alten Telefonnummer). Mein Connector-Zugang lief aber weiter, also
habe ich versucht zu bauen.

**Angelegt und in Ordnung:**

| Was | ID |
|---|---|
| Anzeigensatz `CH · breit 25-65 · Warenkorb` | `120250908761910251` |
| S1 Farben · Startseite | `1591323022470826` |
| S2 Hund · Startseite | `896321246514385` |
| S3 Hand · Startseite | `930602600113164` |
| S4 Rucksack · Startseite · der ehrliche | `1061440346592747` |
| S5 Hund · Startseite · Restwasser | `1316943306969895` |

Alles PAUSED. Die fuenf Werbemittel zeigen auf die Startseite und
benutzen dieselben Bild-Hashes wie vorher - kein neuer Upload noetig.

**Und der Fehler, den ich gemacht habe:** der Anzeigensatz liess sich
mit dem Pixel im `promoted_object` anlegen, ohne zu murren. Daraus habe
ich geschlossen, die Pixel-Sperre sei gar nicht real, und habe Nate
"es funktioniert" geschrieben. Das war voreilig. Beim naechsten
Schritt, dem Anlegen der Anzeigen, kam:

```
Account does not have access to pixel: Account 1524822076060042
does not have access to pixel 1978393872804216
```

Meta prueft die Pixel-Berechtigung also erst auf Anzeigenebene, nicht
auf Anzeigensatzebene. **Die Sperre ist echt.** Ich haette den Erfolg
erst melden duerfen, nachdem die ganze Kette durch war.

Der Anzeigensatz bleibt stehen - er kostet nichts und ist fertig, sobald
der Pixel haengt. Dann fehlen nur noch fuenf Aufrufe fuer die Anzeigen.

## 19.8.2026: Umzug auf das private Werbekonto

Der Business Manager von KatzenUfos verlangt eine Verifizierung, die an
einer Telefonnummer haengt, die es nicht mehr gibt. Das Pixel-Teilen
laeuft ausschliesslich ueber den Business Manager - also ist dieser Weg
zu. Nate hat entschieden, nicht weiter daran zu arbeiten, sondern
umzuziehen. Richtige Entscheidung: stundenlang eine Mauer verhandeln
lohnt nicht, wenn daneben eine offene Tuer ist.

**Neues Zuhause: Werbekonto `1597012881615534` (Nate Murseli), kein
Unternehmen dahinter.** Genau das ist hier der Vorteil - ein Pixel, den
dieses Konto selbst anlegt, gehoert ihm, und die Berechtigungsfrage
entsteht gar nicht erst.

**Was der Umzug NICHT kostet, nachgeprueft:**

| | |
|---|---|
| Seite `Lets'drink` `1189244220947958` | bleibt - Nate ist als Person Administrator, geprueft ueber `ads_get_user_pages` |
| Bilder | bleiben - liegen auf der Shopify-CDN, ueber `image_url` wiederverwendbar |
| Texte | bleiben |
| Pixel-Historie | weg, war aber ueber vier Websites vermischt und unbrauchbar |
| Zahlungsmittel | muss neu hinterlegt werden |

**Angelegt am 19.8.2026 auf `1597012881615534`, alles PAUSED:**

| Was | ID |
|---|---|
| Kampagne `Let'sDrink · Verkauf · Start CH` | `52618860410982` |
| S1 Farben · Startseite | `2138644983741588` |
| S2 Hund · Startseite | `1248205507404043` |
| S3 Hand · Startseite | `2076890522944384` |
| S4 Rucksack · Startseite · der ehrliche | `1850551252989388` |
| S5 Hund · Startseite · Restwasser | `1091666063808328` |

Kampagne mit CHF 20 Tagesbudget auf Kampagnenebene,
LOWEST_COST_WITHOUT_CAP. Die fuenf Werbemittel zeigen auf die
Startseite, Absender ist dieselbe Seite wie vorher.

### Pixel angelegt, Anzeigensatz steht

Nate hat den Pixel angelegt: **`883186891300328`**, Name `Let'sDrink`,
Eigentuemer das Werbekonto `1597012881615534`. Damit ist die
Berechtigungssperre weg - der Pixel wurde im `promoted_object`
anstandslos angenommen.

| Was | ID |
|---|---|
| Anzeigensatz `CH · breit 25-65 · Warenkorb` | `52618872406182` |

CH, 25-65, breit ohne Interessen, Optimierung auf In-den-Warenkorb.

**Der naechste Fehler ist ein anderer - und ein kleinerer.** Beim
Anlegen der ersten Anzeige:

```
No Payment Method: Update payment method
```

Diesmal habe ich die ganze Kette getestet, bevor ich Erfolg melde -
Lehre aus gestern. Der Pixel geht durch, es fehlt nur das
Zahlungsmittel.

**Offen, und nur Nate kann es:**

1. Zahlungsmittel auf `1597012881615534` hinterlegen -
   Werbeanzeigenmanager-App, Konto-Auswahl, `Abrechnung und Zahlungen`
2. Shopify, Facebook-Kanal, Datenfreigabe auf `883186891300328` stellen

**Dann ich:** die fuenf Anzeigen. Fuenf Aufrufe.

### Was im alten Konto liegen bleibt

Kampagne `120250903005380251`, Anzeigensatz `120250908761910251` und
neun Werbemittel im Konto `1524822076060042`. Alles pausiert, nichts
davon kostet etwas. Falls Nate den Zugang je zurueckbekommt, ist es
weiterhin da.

## Was noch fehlt

1. **Pixel dem Werbekonto zuweisen.** Ohne das kein Anzeigensatz mit
   Kauf- oder Warenkorb-Optimierung.
2. **Anzeigensatz** – ein Aufruf, sobald der Pixel hängt.
3. **Drei Anzeigen** – je einer.
4. **Instagram-Konto.** Die Werbemittel tragen keine
   `instagram_user_id`, weil `ads_get_ig_accounts` fuer dieses Konto
   nicht freigeschaltet ist. So liefern sie nur auf Facebook aus. Im
   Werbeanzeigenmanager laesst sich das Instagram-Konto von Hand
   nachtragen.

Bewusst NICHT gemacht: den Anzeigensatz schon mit einer Ersatz-
Optimierung wie „Landingpage-Aufrufe" anzulegen. Er waere fertig
aussehend und aktivierbar, wuerde aber auf das falsche Ziel
optimieren. Eine Falle zu bauen, die aussieht wie ein fertiger
Aufbau, spart fuenf Minuten und kostet im schlechtesten Fall das
Budget einer Woche.

## 19.8.2026: elf Motive statt neun — und zwei eigene Fehler

Nate: „Wrstell neue bilder und mach draus werbe bilder."

### Erzeugen ging nicht — zwei Gruende, beide gemessen

**1. Die Flasche darf nicht erzeugt sein.** Erzeugte Umgebung mit der
echten Flasche darin waere erlaubt gewesen. Eine erzeugte Flasche nie:
wer bestellt, muss bekommen, was er gesehen hat. Genau daran ist am
selben Tag der 30-Sekunden-Film gescheitert (cremefarbener Koerper,
eingepraegte Pfote — ein anderes Modell).

**2. Das Guthaben reicht nicht.** Nachgesehen statt vermutet:

| | |
|---|---|
| Guthaben Higgsfield | **1.29 Credits** |
| Kosten `marketing_studio_image`, 1k, eine Aufnahme | **2 Credits** |
| Freikontingent `unlim` | nicht verfuegbar |

Es reicht also nicht fuer ein einziges Bild. Nate hat zugleich gesagt,
er koenne momentan kein Guthaben aufladen — eine Aufforderung zum
Nachladen waere daher keine Antwort, sondern eine Ausrede.

### Was stattdessen gemacht wurde

Im Ordner `shop/werbung/tiere` lagen vier Fotos aus Nates eigenem
Shop, zwei davon unbenutzt. Beide gegen den Freisteller geprueft —
klarer Koerper, tuerkiser Napf, Pfotenknopf, zwei Schloss-Zeichen:
dieselbe Flasche.

| Motiv | Bild | Aussage |
|---|---|---|
| **J-spaziergang** | Vizsla trinkt im Park aus dem Napf | „Trinken, ohne Napf zu suchen." |
| **K-berg** | Hund und Wanderer vor den Berner Alpen | „Mit auf die Wanderung." |

K ist das erste und einzige Motiv, auf dem die **Schweiz** zu sehen
ist. Keine der deutschen Vergleichsanzeigen hat so ein Bild.

Damit: **11 Motive in 3 Formaten = 33 Dateien.** Texte dazu als
Satz 6 und Satz 7 in TEXTE.md, Laengen nachgemessen.

### Zwei Fehler in meiner eigenen Arbeit von gestern

**Das Querformat von H-tiere und I-katze war kaputt.** Bei 52 Prozent
Fotoanteil bleiben von 628 Pixeln 301 fuer den Text; die zweizeilige
Ueberschrift in 95 px braucht allein 190. Die Ueberschrift lief unten
aus dem Bild, die Trennlinie ging quer durch „und Katze." und die
Adresse lag darunter. Quadrat und Hochformat stimmten — ich hatte das
Querformat nach dem Rendern schlicht nicht angesehen.

Behoben, nicht ueberklebt: Querformat hat jetzt ein eigenes Layout
(Foto links, Text rechts). Nebenbei wird auch der Anschnitt besser —
624x628 ist fast quadratisch, das Tier behaelt den Kopf, waehrend ein
1200x327-Streifen ihn abschneidet.

**Beim ersten Neubau kam derselbe Fehler zweimal wieder**, einmal
waagrecht (K's Unterzeile lief rechts raus und endete als „in der
Schw"), einmal senkrecht (J hat drei Kopfzeilen, das Layout rechnete
mit zwei). Beides sind Masse, die ich geraten statt gerechnet hatte.
Jetzt rechnet der Bau:

- Schriftgroessen werden aus der verfuegbaren Breite abgeleitet und
  bei einer Untergrenze abgebrochen statt unleserlich klein gesetzt.
- Die Fotohoehe ergibt sich aus dem, was der Text wirklich braucht.
  Eine Zeile mehr im Kopf schiebt das Foto nach oben, statt den Text
  aus dem Bild.
- Wird das Foto dabei kleiner als ein Drittel, bricht der Bau ab,
  statt still etwas Kaputtes zu speichern.

Dazu `bogen.py`: baut pro Format einen Kontaktbogen mit allen elf
Motiven nebeneinander. Beide Fehler waeren darauf sofort aufgefallen.

## 19.8.2026 spaeter: "dise sehen zu amateur aus" — Fotomotive neu gebaut

Nate ueber H, I, J und K: "Neue werbe bilder dise sehen zu amateur
aus." Er hatte recht, und der Beweis lag im eigenen Ordner: neben
A-hand und B-farben sahen die vier Fotomotive wie eine Vorlage aus.

**Was daran billig aussah** — Foto in einem Rechteck oben, Text in
einem weissen Kasten unten, dazwischen eine harte Naht. Rechts neben
der Ueberschrift ein totes weisses Feld. Zwei Haelften ohne
gemeinsamen Grund.

**Warum es so gebaut war** — weil ich beim ersten Versuch gemessen
hatte, dass weisse Schrift auf hellem Fell nur 1.62 zu 1 Kontrast
haelt, und daraus den falschen Schluss gezogen habe. Die Antwort auf
zu wenig Kontrast ist nicht, das Foto in einen Kasten zu sperren,
sondern einen Verlauf darunterzulegen.

### Der neue Aufbau (`lib_foto.py`)

Foto randlos ueber die ganze Flaeche, Text darauf, Verlauf dazwischen.
Die Deckkraft des Verlaufs wird **gesucht statt gewaehlt**: probeweise
ueberlagern, auf dem Ergebnis den hellsten Bereich hinter jeder Zeile
messen (92. Perzentil), kleinste Deckkraft nehmen, die ueberall haelt.
So bleibt das Foto so hell wie moeglich und die Schrift trotzdem
sicher. Gemessene Werte, alle ueber der Grenze:

| Motiv | Deckung | schwaechster Kontrast |
|---|---|---|
| H-tiere (hell) | 0.30 | 3.7 (Balken, Grenze 3.0) |
| I-katze | 0.50–0.65 | 3.3 |
| J-spaziergang | 0.55 | 4.0 |
| K-berg | 0.65–0.70 | 3.2 |

### Drei Dinge, die die Messung erzwungen hat

**Das Markentuerkis kann auf Weiss nicht bestehen.** #45B6B2 hat
Leuchtdichte 0.375; gegen hellen Grund sind das 2.3 zu 1, und fuer
3 zu 1 muesste es unter 0.268 liegen. Das ist keine Einstellung,
sondern eine Obergrenze. Es traegt jetzt einen kurzen Akzentbalken
statt Schrift — als Flaeche gilt 3 zu 1 — und fuer die helle Fassung
wird ein tieferer Ton **abgeleitet**: `dunkler(TUERKIS, 4.0, PAPIER)`
= #338784, gemessen 4.04 zu 1.

**Der Anlauf des Verlaufs gehoert oberhalb des Textes.** Erste Fassung
liess ihn am oberen Rand des Textblocks beginnen: selbst bei voller
Deckkraft noch 1.1 zu 1 an der obersten Zeile, weil der Schleier dort
absichtlich fast durchsichtig ist.

**H-tiere braucht die umgekehrte Behandlung.** Es ist kein
Stimmungsbild, sondern ein Produktfoto: sechs Flaschen auf hellem
Karton. Der dunkle Verlauf lag genau auf den Flaschen — gemessen
richtig, gestalterisch falsch. Dort laeuft es jetzt hell: Schleier von
oben, dunkle Schrift, untere Bildhaelfte unberuehrt. Im Querformat
liegen dieselben Flaschen unter der Textspalte, also gilt es dort
auch — beim ersten Durchgang hatte ich nur das Quadrat umgestellt und
das Querformat wieder nicht angesehen.

## 19.8.2026: Werbevideo aus Nates Film

Nate: „Das können wir als werbe video benutzen." 13.05 s, 888×490,
HEVC, mit Ton. Inhalt: Produktnahaufnahmen auf Schwarz, Hund trinkt
im Wald, Wanderung im Geröll, **Katze trinkt im Auto**, Küstenstrasse.
Professionell gedreht — und die Katze ist genau das, was den
Standbildern fehlte.

### Geprüft, bevor gebaut wurde

Bei voller Auflösung gegen den Freisteller gehalten:

| Merkmal | Film | Nates Flasche |
|---|---|---|
| Flaschenkörper | klar | klar ✓ |
| Kopf, Napfform | türkis, gleich | ✓ |
| Schloss-Zeichen | zwei, oben zu / unten offen | **identisch** ✓ |
| Knopf | **Wirbel mit zwei Punkten** | **Pfotenabdruck** ✗ |

Also **nicht** das andere Modell aus dem 30-Sekunden-Film — das hatte
einen cremefarbenen Körper. Hier stimmt alles bis auf den Knopf.
Dieselbe Bauform, anderes eingeprägtes Zeichen; der Wirbel ist
vermutlich das Markenzeichen des Herstellers.

### Was gebaut wurde — `shop/werbung/video.py`

Drei Fassungen, je 15.1 s (13.1 s Film + 2 s Abspann), **ohne Ton**:

| Format | Film im Rahmen | Bemerkung |
|---|---|---|
| 1080×1080 | 1080×596 | Kopfzeile 49 px, das Band gibt nicht mehr her |
| 1080×1350 | 1080×596 | Kopfzeile 93 px |
| 1080×1920 | 1080×796, seitlich beschnitten | Schutzzone 250 oben / 340 unten |

**Nicht beschnitten, sondern gerahmt.** 888 px Breite auf 1080 sind
Faktor 1.22 — vertretbar. Ein 1:1-Zuschnitt hätte 490 auf 1080
gestreckt, Faktor 2.2. Deshalb liegt der Film in voller Breite, der
Text steht auf dem Band darunter.

**Der Ton kommt weg.** Meta spielt Anzeigen stumm an, und Musik in
einem fremd produzierten Film ist die häufigste Urheberrechtsfalle
bei Videoanzeigen. Ohne Ton fällt das Risiko weg, die Anzeige
verliert nichts.

**Beim Hochformat lag der Preis in der Schutzzone.** Erste Fassung
liess das Band bis zum unteren Bildrand laufen — Preis und Adresse
wären hinter Metas Aktionsknopf verschwunden. Jetzt endet das Band
340 px darüber, und der Film füllt den freigewordenen Platz.

### Offen — nur Nate kann es beantworten

**Woher stammt der Film, und darf er ihn verwenden?** Lieferanten
geben Händlern solche Filme häufig ausdrücklich frei; dann ist alles
in Ordnung. Stammt er von einer fremden Marke, kann Meta die Anzeige
sperren und im schlechten Fall das Werbekonto. Die Dateien liegen
gebaut bereit — veröffentlicht wird nichts, bevor das geklärt ist.

## 19.8.2026 abends: drei Anzeigen sind LIVE

Nate: "habe 12 fr auf werbe anzeiger hinzugefügt erstell mir mit dem
webeanzeiger und stelle sienonline" und "Schau das du die perfekten
bilder benutzt wo man die bilder guht sieht".

Der Blocker ist weg: `has_payment_method: true` auf 1597012881615534.

### Was live ist

| | |
|---|---|
| Kampagne | `52619044014582` — Let'sDrink · Test CH · 12 CHF · Klicks |
| Anzeigensatz | `52619044111982` — CH · breit 25-65 |
| Anzeige 1 | `52619044480582` — Hund und Katze · sechs Farben |
| Anzeige 2 | `52619044611782` — Hund trinkt aus dem Napf |
| Anzeige 3 | `52619044630182` — Katze trinkt aus dem Napf |

Alle drei zurueckgelesen: `effective_status: ACTIVE`. Nicht nur
`status` — `effective_status` waere CAMPAIGN_PAUSED oder ADSET_PAUSED,
wenn oben noch etwas ausgeschaltet waere. Vorschau vorher angesehen,
`ads_get_errors` ueber alle fuenf Ebenen: leer.

### Zwei Entscheidungen, die die Messung erzwungen hat

**Ziel ist KLICKS, nicht Verkaeufe.** Der Pixel `883186891300328`
meldet `last_fired_time` = 1970 — also NIE ein Ereignis. Eine
Optimierung auf Kauf oder Warenkorb braucht Pixeldaten; ohne sie
liefert Meta praktisch nichts aus. Deshalb LINK_CLICKS.

In diesem Dokument stand vorher, eine Ersatz-Optimierung waere eine
Falle. Das galt fuer einen Anzeigensatz, der VERKAUF verspricht und
heimlich auf etwas anderes optimiert. Hier heisst die Kampagne
"Klicks", das Ziel ist Klicks, und der Zweck ist ein Test der Motive -
kein Umsatz. Der Unterschied ist die Beschriftung.

**Laufzeitbudget, kein Tagesbudget.** CHF 12 als lifetime_budget mit
Stopp am 23.8.2026, 23:59. Ein Tagesbudget haette weiterlaufen koennen;
so ist der Betrag hart gedeckelt und die Kampagne endet von selbst.

Nebenbefund: `campaign_spend_cap` liess sich nicht setzen — Meta
verlangt dafuer in CHF mindestens 100. Nicht noetig, das
Laufzeitbudget deckelt bereits.

### Welche Bilder und warum diese

Auswahl nach Nates Vorgabe "wo man die bilder guht sieht":

| genommen | warum |
|---|---|
| H-tiere | sechs Flaschen scharf im Bild, Hund UND Katze dahinter |
| J-spaziergang | Flasche gross in der Hand, Hund trinkt sichtbar daraus |
| I-katze | Napf und Flasche gross, Katze trinkt sichtbar daraus |

| verworfen | warum |
|---|---|
| K-berg | Flasche kleiner, Berge dominieren |
| B-farben | die Flaschen wirken grau statt farbig |
| G-einer | zeigt Rosa - beim Lieferanten leer |
| E-fakten | Textmotiv, Flasche klein |

### Weg der Bilder

Meta braucht eine oeffentliche Adresse. Die Motive liegen im Zweig,
nicht im Netz - also ueber Shopify Files hochgeladen
(`stagedUploadsCreate` -> Upload -> `fileCreate`) und die CDN-Adressen
verwendet. Alle drei mit HTTP 200 nachgeprueft, bevor sie an Meta
gingen.

### Was das Geld realistisch kauft

CHF 12 in der Schweiz sind grob 1000 bis 3000 Einblendungen. Das ist
ein Funktionstest, kein Werbetest: es zeigt, ob die Kette laeuft und
welches Motiv ueberhaupt angeklickt wird. Fuer eine belastbare Aussage
ueber Verkauf fehlen zwei Groessenordnungen Budget.

### Was jetzt trotzdem noch fehlt

1. **Der Pixel bekommt keine Ereignisse.** Shopify -> Facebook-Kanal ->
   Datenfreigabe auf `883186891300328` stellen. Ohne das misst niemand,
   was der Verkehr im Laden tut, und eine spaetere Verkaufskampagne
   kann nicht lernen.
2. **Instagram fehlt.** Die Werbemittel tragen keine
   `instagram_user_id` - `ads_get_ig_accounts` ist fuer dieses Konto
   nicht freigeschaltet. Die Anzeigen laufen damit nur auf Facebook.
   Im Werbeanzeigenmanager laesst sich das Konto von Hand nachtragen.
