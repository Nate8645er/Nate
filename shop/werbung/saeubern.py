#!/usr/bin/env python3
"""Den Sockel unter den Freistellern abschneiden.

Unter dem echten Flaschenboden - erkennbar am dunklen Rand - steht in
allen sechs Freistellern ein hellgrauer, gestufter Klotz. Das ist die
Spiegelung aus dem Produktfoto, die die Kantenverfolgung mitgenommen
hat. Auf hellem Grund faellt sie kaum auf, auf dunklem Grund sieht sie
aus wie ein Fehler: die Flasche steht auf einem Podest, das es nicht
gibt.

ERKENNUNG, ohne feste Zeilennummer:
Von unten nach oben zaehlen, wie breit jede Zeile gedeckt ist. Der
Sockel ist schmaler als der Flaschenkoerper. Wo die Breite sprunghaft
zunimmt - mindestens auf das 1.3-fache des bisher von unten gesehenen
Groesstwerts - faengt der Koerper an. Zwei Zeilen darunter wird
geschnitten, damit der dunkle Bodenrand ganz erhalten bleibt.

Das ist bewusst keine feste Zahl: die sechs Bilder sind zwar gleich
gross, aber wer spaeter neue Fotos einpflegt, soll nicht nachrechnen
muessen.
"""
import os
import numpy as np
from PIL import Image

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.path.dirname(HIER) + "/frei"
ZIEL = HIER + "/frei-sauber"
FARBEN = ["tuerkis", "gruen", "rosa", "grau", "schwarz", "weiss"]


def schnittkante(alpha):
    h = alpha.shape[0]
    breiten = (alpha > 128).sum(axis=1)
    groesst = 0
    for y in range(h - 1, int(h * 0.80), -1):
        b = breiten[y]
        if b == 0:
            continue
        if groesst > 0 and b >= 1.3 * groesst:
            # y ist die unterste Zeile, die noch zum Koerper gehoert.
            # Als Hoehe zurueckgeben heisst: y bleibt drin, alles
            # darunter faellt weg.
            return y + 1
        groesst = max(groesst, b)
    return h


def main():
    os.makedirs(ZIEL, exist_ok=True)
    for name in FARBEN:
        im = Image.open(f"{QUELLE}/{name}.png").convert("RGBA")
        a = np.array(im)[:, :, 3]
        y = schnittkante(a)
        neu = im.crop((0, 0, im.width, y))

        # Nach dem Schnitt kann eine Rand-Spalte leer sein; eng
        # zuschneiden, damit alle sechs gleich sitzen.
        bb = neu.getbbox()
        neu = neu.crop(bb)
        neu.save(f"{ZIEL}/{name}.png")
        print(f"{name:8s} {im.size} -> {neu.size}   "
              f"(Sockel {im.height - y} Zeilen entfernt)")


main()
