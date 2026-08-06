# Werkzeuge zum Nachmessen des Shops

Drei kleine Programme. Sie messen, was der Kunde tatsaechlich sieht,
statt sich auf das zu verlassen, was im Quelltext steht. Jede Aussage
ueber Kontrast, Bewegung oder Sichtbarkeit in `../ENTWURF-A.md` stammt
aus diesen drei Dateien.

## Reihenfolge

    python3 spiegel.py    # Seiten samt aller CSS/JS lokal spiegeln
    python3 messen.py     # Kontrast, Bewegung, Sichtbarkeit, Querlauf
    python3 bilder.py     # Bildschirmfotos in 390 und 1280 Pixel Breite

`spiegel.py` muss immer zuerst laufen; die beiden anderen lesen den
Spiegel, den es anlegt.

## Zwei Fallen, die hier schon zugeschnappt sind

**Der Keksbehaelter.** Die Vorschau eines unveroeffentlichten Themes
haengt an einem Keks, nicht am Adressteil `?preview_theme_id=`. Ruft man
die Adresse mit `-L`, aber ohne `-c`/`-b` ab, folgt curl der Umleitung
und misst am Ende die VEROEFFENTLICHTE Fassung. Das hat hier einmal einen
falschen Befund erzeugt: gemeldet wurde ein Rueckschritt, den es nicht
gab. `spiegel.py` fuehrt den Behaelter deshalb immer mit.

**Fremde Anfragen.** Der Spiegel enthaelt nur CSS und JS. Laesst man den
Browser die fehlenden Shopify-Bausteine trotzdem anfordern, wartet der
Seitenaufbau ins Zeitlimit. `messen.py` und `bilder.py` weisen deshalb
jede Anfrage ab, die nicht an 127.0.0.1 geht.

Bilder werden bewusst NICHT gespiegelt. Im Bildschirmfoto steht dann
Ersatztext statt der Flasche. Das ist kein Fehler: auf Textfarbe,
Bewegung und Querlauf hat ein fehlendes Bild keinen Einfluss, und der
Spiegel bleibt klein genug, um in Sekunden zu stehen.

## Was `messen.py` ausgibt

- **Kontrast** jeder sichtbaren Textstelle gegen ihren wirksamen Grund.
  Der Grund wird durch die ganze Elternkette hindurch aufgebaut, halb-
  durchsichtige Schichten werden uebereinandergelegt. Schwelle 4.5 zu 1,
  bei grosser Schrift 3.0 — nach WCAG.
- **Uebergaenge** und **Endlosbewegungen** als Zahl. Eine Bewegung, die
  nie aufhoert, teilt nichts mit und laesst einen Shop billig wirken.
- **Sofort sichtbarer Textanteil.** Vor dem Umbau standen auf der
  Startseite 38 Prozent des Textes beim Laden auf Deckung 0 und warteten
  auf ein Skript. Wer schnell scrollt oder ein Skript blockiert, sah
  einen leeren Shop.
- **Querlauf** bei 320, 360, 390, 768, 1024 und 1440 Pixeln.

Jede Seite wird zweimal gemessen: mit JavaScript und ohne. Ohne muss der
Shop vollstaendig lesbar bleiben.

## Theme-ID

Steht oben in `spiegel.py`. Bei einem neuen Theme dort aendern — an
keiner anderen Stelle.
