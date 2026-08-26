#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motiv M-see: zweiter erzeugter Hintergrund, echte Flasche.

Gleiches Vorgehen wie l_alpen_bauen.py, siehe dort fuer die
Begruendung. Hintergrund diesmal ein Schweizer Seeufer - passt
inhaltlich zum Produkt (Wasser), nicht nur zur Marke (Schweiz).
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
    "hintergrund-see.png"))
ZIEL = os.path.join(TIERE, "letsdrink-see-ki.jpg")

FARBE = "tuerkis"


def komponieren():
    bg = Image.open(QUELLE_BG).convert("RGB")
    ziel_b = 1600
    ziel_h = round(bg.height * ziel_b / bg.width)
    bg = bg.resize((ziel_b, ziel_h), Image.LANCZOS)

    im = flasche(FARBE)
    hoehe = round(ziel_h * 0.60)
    cx = round(ziel_b * 0.30)
    boden_y = round(ziel_h * 0.92)
    stelle(bg, im, hoehe=hoehe, cx=cx, boden_y=boden_y,
           a_blur=40, a_w=1.35, kontakt=0.30, ambient=0.10)

    os.makedirs(TIERE, exist_ok=True)
    bg.save(ZIEL, quality=92)
    print("komponiert:", ZIEL, bg.size)


M_KOPF = ["Frisches Wasser,", "immer dabei."]
M_SUB = "550 ml  ·  Sechs Farben"


if __name__ == "__main__":
    komponieren()
    alle_drei(bild="letsdrink-see-ki.jpg", anker=0.60, kopf=M_KOPF,
              unterzeile=M_SUB, praefix="M-see")
