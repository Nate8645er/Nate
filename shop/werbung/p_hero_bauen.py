#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motiv P-hero: gleicher Aufbau wie O-hero, aber mit Nano Banana Pro
statt Marketing Studio Image.

Nate: "Benutz das beste model von higgsfield ... professionell
bessere bilder". Laut Higgsfield-Modellkatalog (models_explore) ist
"Nano Banana Pro" (Google) aktuell auf "Ultimate quality, text and
diagrams" eingestuft - hoehere Aufloesung (4K statt 1K), schaerfer.

GEPRUEFT GEGEN DAS ECHTE PRODUKT

Wieder die echte Flasche (frei-sauber/tuerkis.png) als Referenzbild
gegeben, wieder danach gegen den Freisteller verglichen
(crop-knopf-nanobanana.png vs. crop-knopf-echt.png): Napfform,
Pfotenknopf, Henkel, Materialtransparenz stimmen. EIN Unterschied:
die zwei Schloss-Icons rechts vom Knopf zeigen beim echten Produkt
einmal zu, einmal offen - hier zeigen beide "offen". Kosmetisches
Detail, keine Aenderung an Form oder Funktion des Produkts, aber
nicht verschwiegen.

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
    "hero-tuerkis-nanobanana-1600.png"))
ZIEL = os.path.join(TIERE, "letsdrink-hero-ki-nanobanana.jpg")


def vorbereiten():
    im = Image.open(QUELLE).convert("RGB")
    os.makedirs(TIERE, exist_ok=True)
    im.save(ZIEL, quality=95)
    print("vorbereitet:", ZIEL, im.size)


P_KOPF = ["Für Hund", "und Katze."]
P_SUB = "550 ml  ·  Sechs Farben"


if __name__ == "__main__":
    vorbereiten()
    alle_drei_hell(bild="letsdrink-hero-ki-nanobanana.jpg", anker=0.5,
                    kopf=P_KOPF, unterzeile=P_SUB, praefix="P-hero")
