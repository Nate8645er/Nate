#!/usr/bin/env python3
"""Foto-Anzeigen aus dem eigenen Produktfilm.

WARUM ES DIESE DATEI GIBT

Die erste Fassung der Anzeigen stellte den Text in eine deckende Flaeche
am unteren Rand. Auf dem Bank-Motiv verschwand damit der ganze
Flaschenkoerper dahinter - zu sehen war nur noch der Napf. Nate hat das
beanstandet, und er hatte recht: ein Produktbild, auf dem mehr als die
Haelfte des Produkts fehlt, ist kein Produktbild.

Zwei Dinge sind daraufhin anders:

1. DER TEXT SITZT OBEN, in einem weichen dunklen Verlauf statt in einer
   Flaeche mit Kante. Der Verlauf gibt der weissen Schrift Halt, ohne
   eine Linie zu ziehen - und er liegt dort, wo im Hochformat ohnehin
   Himmel, Hemd oder unscharfer Hintergrund steht, nicht auf dem
   Produkt.

2. DIE EINZELBILDER SIND ANDERE. Der Film hat 15 Sekunden, und die
   Stellen, an denen die ganze Flasche im Bild steht, sind nicht die,
   die ich zuerst genommen hatte. Nachgesehen wurde an einem
   Kontaktblatt mit einem Bild je Sekunde, danach jeder Anschnitt
   einzeln geprueft, statt eine Zahl zu raten:

     t4.4  y330   Hand haelt die ganze Flasche, dunkles Hemd dahinter
     t8.2  y190   der Hund trinkt wirklich aus dem Napf
     t13.4 y190   Flasche in der Seitentasche, Hund laeuft hinterher
     t1.2  y150   Bank, Rucksack, Leine, Hundepfoten

KEINE ERZEUGTEN PRODUKTBILDER

Naheliegend waere gewesen, mit einem Bildgenerator eine huebschere
Flasche zu bauen. Das waere dann aber nicht mehr Nates Flasche. Wer
etwas kauft, muss bekommen, was er gesehen hat. Alle Bilder hier sind
Einzelbilder aus dem echten Film; erzeugt ist nichts.

WAS DRAUFSTEHT

Nur Belegtes: 550 ml, sechs Farben, Gratisversand Schweiz. Keine
Bewertung, keine Verkaufszahl, keine Dringlichkeit, keine Aussage zur
Dichtigkeit. "Im Rucksack dabei" statt "Passt in die Seitentasche" -
das Bild zeigt diesen einen Rucksack, es verspricht nicht jeden.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
Q = os.path.join(HIER, "quelle")
RAHMEN = os.path.join(Q, "frames")
ZIEL = os.path.join(HIER, "bilder")

FETT = os.path.join(Q, "a-sans-bold.ttf")
MAGER = os.path.join(Q, "a-sans.ttf")

FORMATE = {"1x1": (1080, 1080), "4x5": (1080, 1350), "9x16": (1080, 1920)}

MOTIVE = [
    ("4-hand", "t4.4.jpg", 330,
     ["Wasser dabei,", "Napf inklusive."],
     "550 ml · sechs Farben · Gratisversand Schweiz"),
    ("5-hund", "t8.2.jpg", 190,
     ["Der Napf ist", "schon dran."],
     "550 ml · sechs Farben"),
    ("6-rucksack", "t13.4.jpg", 190,
     ["Im Rucksack", "dabei."],
     "550 ml · sechs Farben · Gratisversand Schweiz"),
    ("7-bank", "t1.2.jpg", 150,
     ["Wasser dabei,", "Napf inklusive."],
     "550 ml · sechs Farben"),
]


def tropfen(g, farbe):
    """Der Wassertropfen aus dem Kopf des Shops."""
    ue = 8
    n = g * ue
    b = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    r = n * 0.242
    mx, my = n / 2, n * 0.575
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=farbe)
    d.polygon([(mx, n * 0.133),
               (mx - r * 0.995, my + r * 0.10),
               (mx + r * 0.995, my + r * 0.10)], fill=farbe)
    return b.resize((g, g), Image.LANCZOS)


def bau(datei, kopf, zeile, breite, hoehe, oben):
    im = Image.open(os.path.join(RAHMEN, datei)).convert("RGB")

    # Fenster im Zielverhaeltnis, oben verankert an der geprueften
    # Stelle. Bei 9:16 deckt sich das Verhaeltnis mit der Quelle, dann
    # faellt der Anschnitt weg.
    fh = min(int(im.width * hoehe / breite), im.height)
    y = min(max(0, oben), im.height - fh)
    b = im.crop((0, y, im.width, y + fh)).resize((breite, hoehe), Image.LANCZOS)

    d = ImageDraw.Draw(b)
    rand = int(breite * 0.075)
    y = int(hoehe * 0.055)
    hm = int(breite * 0.050)

    # WO DER TEXT ENDET, MUSS DER VERLAUF NOCH TRAGEN.
    #
    # Erste Fassung: ein durchgehend abfallender Verlauf ueber 42 % der
    # Hoehe. Nachgemessen war der Kontrast der Beizeile an hellen Stellen
    # bei 1.0 - weisse Schrift auf hellem Tuerkis, praktisch unlesbar.
    # Der Mittelwert sah mit 4.2 bis 9.4 gut aus und verdeckte genau das:
    # es kommt auf die schlechteste Stelle an, nicht auf den Schnitt.
    #
    # Jetzt haelt der Verlauf volle Deckung bis unter die letzte Zeile
    # und blendet erst danach aus.
    unterkante = (y + int(hm * 1.9) + int(breite * 0.098) * len(kopf)
                  + int(breite * 0.012) + int(breite * 0.055))
    ausblenden = int(hoehe * 0.16)
    tief = unterkante + ausblenden
    v = Image.new("L", (1, tief))
    for i in range(tief):
        if i < unterkante:
            v.putpixel((0, i), 190)
        else:
            v.putpixel((0, i), int(190 * (1 - (i - unterkante) / ausblenden) ** 1.6))
    b.paste(Image.new("RGB", (breite, tief), "#0B0B0B"), (0, 0),
            v.resize((breite, tief)))

    t = tropfen(int(hm * 0.95), "#FFFFFF")
    b.paste(t, (rand, y), t)
    d.text((rand + t.width + int(hm * 0.28), y - int(hm * 0.08)), "Let'sDrink",
           font=ImageFont.truetype(FETT, hm), fill="#FFFFFF")
    y += int(hm * 1.9)

    f = ImageFont.truetype(FETT, int(breite * 0.082))
    for z in kopf:
        d.text((rand, y), z, font=f, fill="#FFFFFF")
        y += int(breite * 0.098)
    y += int(breite * 0.012)
    d.text((rand, y), zeile,
           font=ImageFont.truetype(MAGER, int(breite * 0.037)), fill="#EDEDED")
    return b


def main():
    os.makedirs(ZIEL, exist_ok=True)
    for name, datei, oben, kopf, zeile in MOTIVE:
        for fname, (br, ho) in FORMATE.items():
            p = os.path.join(ZIEL, "%s-%s.jpg" % (name, fname))
            bau(datei, kopf, zeile, br, ho, oben).save(p, quality=90, optimize=True)
            print("%-22s %4dx%-5d %5d KB" % (os.path.basename(p), br, ho,
                                             os.path.getsize(p) // 1024))


if __name__ == "__main__":
    main()
