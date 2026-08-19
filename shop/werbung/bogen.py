# -*- coding: utf-8 -*-
"""Kontaktbogen - alle Motive eines Formats nebeneinander.

WARUM ES DIESE DATEI GIBT

Zwei Fehler an einem Tag, beide gleicher Bauart: ein Motiv war im
Quadrat richtig und im Querformat kaputt, und weil ich nur das Quadrat
angesehen hatte, ging es so in den Zweig. Ein Bogen pro Format zwingt
dazu, jedes Format wirklich anzusehen - und nebeneinander faellt sofort
auf, wenn ein Motiv aus der Reihe tanzt.

Vorher lagen die Boegen ohne Skript herum. Jetzt sind sie jederzeit
neu zu bauen, wenn ein Motiv sich aendert.
"""
import os
from PIL import Image
from lib_studio import HIER

MOTIVE = ["A-hand", "B-farben", "C-napf", "D-volumen", "E-fakten",
          "F-rest", "G-einer", "H-tiere", "I-katze", "J-spaziergang",
          "K-berg"]
FORMATE = ["1080x1080", "1080x1920", "1200x628"]
ZEILE = 620          # Hoehe jedes Motivs auf dem Bogen
LUFT = 12


def bogen(fmt):
    da = [m for m in MOTIVE
          if os.path.exists(os.path.join(HIER, "%s_%s.png" % (m, fmt)))]
    fehlt = [m for m in MOTIVE if m not in da]
    if fehlt:
        print("  fehlt in %s: %s" % (fmt, ", ".join(fehlt)))

    sk = []
    for m in da:
        im = Image.open(os.path.join(HIER, "%s_%s.png" % (m, fmt)))
        sk.append(im.resize((round(im.width * ZEILE / im.height), ZEILE),
                            Image.LANCZOS))
    W = sum(i.width for i in sk) + LUFT * (len(sk) + 1)
    blatt = Image.new("RGB", (W, ZEILE + 2 * LUFT), (255, 255, 255))
    x = LUFT
    for i in sk:
        blatt.paste(i, (x, LUFT))
        x += i.width + LUFT
    p = os.path.join(HIER, "kontaktbogen-%s.png" % fmt)
    blatt.save(p, "PNG", optimize=True)
    print("  ->", os.path.basename(p), blatt.size, "%d Motive" % len(sk))


if __name__ == "__main__":
    for f in FORMATE:
        bogen(f)
