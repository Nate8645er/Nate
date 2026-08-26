#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motiv O-hero: KI-Studiofoto, Flasche als Referenzbild an Higgsfield.

WARUM DAS ANDERS IST ALS L/M/N

Nate: "richtige werbe bilder für meta ... wie die grossen marken das
machen". Bisher stand die echte Flasche unveraendert als Ausschnitt
in einer erzeugten Szene (lib_studio.stelle - manuelles Einfuegen).
Das sieht man: kein Reflex, kein weicher Kontaktschatten, keine
Lichtstimmung, die zum Hintergrund passt.

Higgsfield kann das besser, wenn man ihm die echte Flasche als
REFERENZBILD gibt (medias-Parameter, role "image") statt nur einen
Text-Prompt. Das Modell baut dann Licht, Schatten und Umgebung um das
Referenzbild herum, statt es stumpf einzufuegen.

GEPRUEFT, NICHT NUR BEHAUPTET

Vor dem Bau wurde das Ergebnis gegen den echten Freisteller
(frei-sauber/tuerkis.png) verglichen: Napfform, Pfotenknopf, die
zwei Schloss-Icons rechts vom Knopf, der Henkel oben - alles stimmt
in Formsprache und Position ueberein. Das ist naeher am Original als
jedes bisherige Verfahren in diesem Ordner, aber es ist trotzdem eine
KI-Neuinterpretation, kein Foto. Das gehoert Nate ehrlich gesagt, nicht
verschwiegen.

Die Datei liegt nur bereit - sie wird nicht automatisch nach Meta
hochgeladen oder aktiviert.
"""
import os
import sys
from PIL import Image

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

from lib_foto import alle_drei_hell, TIERE  # noqa: E402

QUELLE = os.path.abspath(os.path.join(
    HIER, "..", "..", "marketing", "anzeigen", "higgsfield",
    "hero-tuerkis-4x5.png"))
ZIEL = os.path.join(TIERE, "letsdrink-hero-ki.jpg")


def vorbereiten():
    im = Image.open(QUELLE).convert("RGB")
    os.makedirs(TIERE, exist_ok=True)
    im.save(ZIEL, quality=95)
    print("vorbereitet:", ZIEL, im.size)


O_KOPF = ["Für Hund", "und Katze."]
O_SUB = "550 ml  ·  Sechs Farben"


if __name__ == "__main__":
    vorbereiten()
    alle_drei_hell(bild="letsdrink-hero-ki.jpg", anker=0.5, kopf=O_KOPF,
                    unterzeile=O_SUB, praefix="O-hero")
