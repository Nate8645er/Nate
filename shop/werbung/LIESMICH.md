# Werbebilder

Vier Motive in drei Formaten, zwoelf Dateien unter `bilder/`.

    01-knopf      Was das Ding tut
    02-farben     Der einzige echte Unterschied zu jeder anderen Flasche
    03-preis      Preis und Bedingungen
    04-ehrlich    Der Grund, hier zu kaufen statt anderswo

    _beitrag      1080 x 1350  Hochformat 4:5, nimmt im Verlauf am meisten Platz
    _geschichte   1080 x 1920  9:16, oben und unten je 260 px frei gelassen
    _quadrat      1080 x 1080  Katalog, Vorschaubild, Anzeige

Neu bauen:

    python3 saeubern.py    # einmalig: Sockel unter den Freistellern wegschneiden
    python3 werbung.py     # die zwoelf Bilder

## Woraus die Bilder gemacht sind

Aus den echten Produktfotos, ueber Kantenverfolgung freigestellt. **Keine
erzeugten Produktbilder.** Das ist keine Notloesung: wer eine erfundene
Flasche anklickt und eine andere geliefert bekommt, schreibt eine
Rueckgabe statt einer Empfehlung.

Die Schrift ist die des Shops — Fraunces fuer die Titel, IBM Plex Sans
fuer den Satz. Beide werden aus den `woff2`-Dateien des Themes in `ttf`
umgewandelt, statt eine aehnliche Schrift zu nehmen. Wer die Anzeige
sieht und dann den Shop oeffnet, soll dieselbe Marke sehen.

## Warum die Produktmotive dunkel sind, der Shop aber hell

Der Flaschenkoerper ist weiss-durchscheinend. Auf dem hellen Grund des
Shops (`#E8EEEB`) wird er zu einem weissen Klotz ohne Silhouette — erste
Fassung gebaut, angesehen, verworfen.

Dasselbe Problem loest das Farbsystem des Shops seit jeher mit einer
Umkehrung: die *weisse* Flasche bekommt dort einen *dunklen* Grund. Hier
gilt diese Regel fuer alle sechs, weil der Koerper immer weiss ist.
Motiv 04 zeigt keine Flasche gross und bleibt hell — so hat der Verlauf
beide Seiten der Marke.

Welche Farbe auf welchen Grund:

| Grund | geht | geht nicht |
|---|---|---|
| dunkel `#12211F` | tuerkis, gruen, rosa, weiss, grau | **schwarz** — die Kappe verschwindet |
| hell `#E8EEEB` | schwarz, grau | **weiss** — der Koerper verschwindet |

## Der Sockel unter den Freistellern

Unter dem echten Flaschenboden stand in allen sechs Freistellern ein
hellgrauer, gestufter Klotz: die Spiegelung aus dem Produktfoto, die die
Kantenverfolgung mitgenommen hatte. Auf hellem Grund faellt sie kaum auf,
auf dunklem sieht die Flasche aus, als staende sie auf einem Podest.

`saeubern.py` schneidet ihn weg — ohne feste Zeilennummer. Es zaehlt von
unten nach oben, wie breit jede Zeile gedeckt ist; wo die Breite
sprunghaft zunimmt, faengt der Koerper an. Gemessen: 13 Zeilen je Bild.
Wer spaeter neue Fotos einpflegt, muss nichts nachrechnen.

## Rote Linien — gelten fuer Werbung genauso wie fuer den Shop

- Kein erfundener Beweis: keine Bewertungen, Sterne, Verkaufszahlen.
- Keine Dringlichkeit, kein Countdown, keine Verknappung.
- Keine Produktangabe ausser 550 ml und sechs Farben. Nicht
  "auslaufsicher", nicht "BPA-frei", nicht "spuelmaschinenfest", kein
  Material, keine Masse.
- Die Flasche nie auf dem Kopf, Kippen hoechstens 20 Grad.
- Nie das Zeichen scharfes s.

Der Preis steht im Bild als Text und muss von Hand nachgezogen werden,
wenn er sich im Shop aendert. Die Schriftgroesse passt sich selbst an,
damit ein laengerer Preis nicht in die Flasche laeuft.
