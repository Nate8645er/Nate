#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motiv L-alpen: erzeugter Hintergrund, echte Flasche.

WARUM ES DIESES SKRIPT GIBT

Higgsfield hat wieder Guthaben (26.8.2026). Die Regel aus
bauen-foto.py gilt unveraendert: "Die Flasche darf nicht erzeugt
sein. Erzeugte Umgebung mit der echten Flasche darin waere erlaubt
gewesen." Genau das baut dieses Skript - zum ersten Mal, seit die
Regel im Zusammenhang mit dem gescheiterten 30-Sekunden-Film
aufgeschrieben wurde.

DER HINTERGRUND

marketing/anzeigen/higgsfield/hintergrund-alpen.png - ein
KI-generierter Wanderweg in den Alpen, geprueft: keine Person, kein
Tier, kein Gegenstand, keine Flasche, kein Groessenvergleich moeglich.
Reine Szenerie.

DIE FLASCHE

Der echte Freisteller aus shop/werbung/frei-sauber/schwarz.png -
derselbe, den auch die Studio-Motive benutzen. Platziert mit
lib_studio.stelle(), also demselben Zwei-Schatten-Aufbau wie ueberall
sonst. Nichts an der Flasche selbst ist erzeugt oder veraendert.

DANACH

Das Ergebnis wird wie ein normales Foto behandelt und durch
lib_foto.alle_drei() geschickt - dieselbe Kontrastsuche, dieselbe
Typografie wie bei H/I/J/K. Kein Sonderfall, keine zweite Bildsprache.
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
    "hintergrund-alpen.png"))
ZIEL = os.path.join(TIERE, "letsdrink-alpen-ki.jpg")

FARBE = "schwarz"


def komponieren():
    """Hintergrund hochskalieren, echte Flasche mit Schatten aufsetzen."""
    bg = Image.open(QUELLE_BG).convert("RGB")

    # Auf Arbeitsgroesse bringen - hoch genug fuer 1080x1920, ohne die
    # Aufnahme staerker zu vergroessern als noetig (928 -> 1600, Faktor
    # 1.72, deutlich weniger als ein Nachschaerfen brauchen wuerde).
    ziel_b = 1600
    ziel_h = round(bg.height * ziel_b / bg.width)
    bg = bg.resize((ziel_b, ziel_h), Image.LANCZOS)

    im = flasche(FARBE)
    hoehe = round(ziel_h * 0.62)
    cx = round(ziel_b * 0.32)          # linkes Bilddrittel, Weg bleibt frei
    boden_y = round(ziel_h * 0.93)
    stelle(bg, im, hoehe=hoehe, cx=cx, boden_y=boden_y,
           a_blur=40, a_w=1.35, kontakt=0.30, ambient=0.10)

    os.makedirs(TIERE, exist_ok=True)
    bg.save(ZIEL, quality=92)
    print("komponiert:", ZIEL, bg.size)


L_KOPF = ["Wasser für", "den ganzen Weg."]
L_SUB = "550 ml  ·  Sechs Farben"


if __name__ == "__main__":
    komponieren()
    alle_drei(bild="letsdrink-alpen-ki.jpg", anker=0.62, kopf=L_KOPF,
              unterzeile=L_SUB, praefix="L-alpen")
