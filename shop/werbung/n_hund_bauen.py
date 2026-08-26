#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motiv N-hund: erzeugter Hund + erzeugter Hintergrund, echte Flasche.

WARUM DAS ANDERS IST ALS L-alpen UND M-see

Nate: "das zieht keine Kunden an" - zu Recht: eine leere Landschaft mit
Flasche zeigt kein Leben, keinen Grund zu kaufen. Die bewaehrten Motive
(H-tiere, J-spaziergang, K-berg) haben alle ein Tier. Also jetzt ein
erzeugter Hund.

DER GROESSENVERGLEICH - WARUM HIER VORSICHT NOETIG IST

LIESMICH.md, zum A-hand-Motiv: "eine Hand daneben waere ein
Groessenvergleich, den wir nicht belegen koennen." Genau dasselbe
Problem gilt fuer einen Hund neben der Flasche - nur schlimmer, weil
der Hund selbst erzeugt ist und seine Groesse im Bild keine feste
Grosse hat.

Nates eigene Flasche hat keine dokumentierten Masse (siehe TEXTE.md:
"Kein Material, keine Masse, kein Gewicht"). Die Platzierung hier
schaetzt darum bewusst KLEIN und im Vordergrund abseits vom Hund -
eher "die Flasche ist auch dabei" als "so gross ist die Flasche
gegen den Hund". Ein Golden Retriever sitzt real ca. 60 cm hoch, eine
550-ml-Flasche in dieser Produktklasse liegt eher bei 18-22 cm - macht
das Verhaeltnis realistisch klein, nicht bildfuellend gross.
"""
import os
import sys
from PIL import Image

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

from lib_studio import flasche, stelle  # noqa: E402
from lib_foto import alle_drei, TIERE  # noqa: E402

QUELLE_BG = os.path.abspath(os.path.join(
    HIER, "..", "..", "marketing", "anzeigen", "higgsfield",
    "hintergrund-hund-alpen.png"))
ZIEL = os.path.join(TIERE, "letsdrink-hund-ki.jpg")

FARBE = "schwarz"


def komponieren():
    bg = Image.open(QUELLE_BG).convert("RGB")
    ziel_b = 1600
    ziel_h = round(bg.height * ziel_b / bg.width)
    bg = bg.resize((ziel_b, ziel_h), Image.LANCZOS)

    # Konservativ klein: rund 20 % der Bildhoehe, deutlich kleiner als
    # der Hund (der gut 55 % der Bildhoehe einnimmt) - siehe Docstring.
    # Platzierung muss in ALLEN drei Zuschnitten sichtbar bleiben - nicht
    # nur im Quadrat. Story schneidet die Breite auf 1117 px bei x=[203,1320]
    # (anker=0.42), Querformat schneidet die Hoehe auf 837 px bei y=[482,1319].
    # cx und boden_y liegen deshalb bewusst innerhalb beider Fenster.
    im = flasche(FARBE)
    hoehe = round(ziel_h * 0.20)
    cx = round(ziel_b * 0.78)
    boden_y = round(ziel_h * 0.63)
    stelle(bg, im, hoehe=hoehe, cx=cx, boden_y=boden_y,
           a_blur=26, a_w=1.3, kontakt=0.30, ambient=0.10)

    os.makedirs(TIERE, exist_ok=True)
    bg.save(ZIEL, quality=92)
    print("komponiert:", ZIEL, bg.size)


N_KOPF = ["Für jeden", "Spaziergang."]
N_SUB = "550 ml  ·  Sechs Farben"


if __name__ == "__main__":
    komponieren()
    alle_drei(bild="letsdrink-hund-ki.jpg", anker=0.42, kopf=N_KOPF,
              unterzeile=N_SUB, praefix="N-hund")
