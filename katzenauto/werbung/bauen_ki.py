#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Katzenauto-Anzeige, Studio-Variante: freigestelltes KI-Bild (Higgsfield)
statt Lieferantenfoto. Gleicher Marken-/Preis-Rahmen wie bauen.py, aber ohne
Hund/Katze im Bild - reiner Produkt-Look wie bei grossen Marken.

Das KI-Bild wurde per Higgsfield marketing_studio_image direkt (kein
Marketing-Studio-Preset) erzeugt, mit dem echten Lieferantenfoto als
Bildreferenz und expliziten "kein Text/Logo/Wasserzeichen"-Vorgaben. Vor
dem Bau hier per Read visuell mit dem echten Produkt abgeglichen: Form,
Farben (orange/schwarz), Raeder, Kopfstuetzen-Design - alles deckungsgleich,
keine erfundene Beschriftung.

Kein Domainname im Bild, aus demselben Grund wie in bauen.py.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.abspath(os.path.join(HIER, "..", "..",
                                    "marketing", "anzeigen", "quelle"))
QUELLE = os.path.join(HIER, "higgsfield", "hero-roh.png")

TUERKIS_ORANGE = (232, 119, 34)
TINTE = (23, 20, 18)
MUTED = (140, 132, 126)
PREIS = "CHF 139.–"

_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        name = "a-sans-bold.ttf" if bold else "a-sans.ttf"
        _fc[key] = ImageFont.truetype(os.path.join(FDIR, name), size)
    return _fc[key]


def text(img, xy, s, f, fill, anchor="la", track=0.0):
    d = ImageDraw.Draw(img)
    if track == 0:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    x, y = xy
    widths = [d.textlength(ch, font=f) for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    if anchor[0] == "r":
        x -= total
    for ch, w in zip(s, widths):
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += w + track


def bauen(W, H, name):
    src = Image.open(QUELLE).convert("RGB")
    band_h = round(H * 0.34)
    photo_h = H - band_h
    sw, sh = src.size
    scale = max(W / sw, photo_h / sh)
    rw, rh = round(sw * scale), round(sh * scale)
    photo = src.resize((rw, rh), Image.LANCZOS)
    x0 = (rw - W) // 2
    # Produkt sitzt im Studio-Bild etwas unterhalb der Mitte (ca. 53% der
    # Hoehe) - anders als beim Lieferantenfoto, wo die Szene ganz oben
    # beginnt. y0 so gewaehlt, dass das Produkt zentriert im sichtbaren
    # Ausschnitt bleibt statt oben abgeschnitten zu werden.
    mitte = round(rh * 0.53)
    y0 = mitte - photo_h // 2
    y0 = max(0, min(y0, rh - photo_h))
    photo = photo.crop((x0, y0, x0 + W, y0 + photo_h))

    img = Image.new("RGB", (W, H), (250, 249, 247))
    img.paste(photo, (0, 0))

    m = round(W * 0.07)
    y = photo_h + round(H * 0.045)
    bh = max(3, round(W * 0.006))
    ImageDraw.Draw(img).rectangle(
        [m, y, m + round(W * 0.07), y + bh], fill=TUERKIS_ORANGE)
    y += bh + round(H * 0.022)
    marke_gr = round(W * 0.024)
    text(img, (m, y), "Katzenauto", font(marke_gr, True), TINTE, track=0.6)
    y += round(marke_gr * 1.5) + round(H * 0.012)
    kopf_gr = round(W * 0.052)
    text(img, (m, y), "Ade, Karton.", font(kopf_gr, True), TINTE,
         track=-kopf_gr * 0.02)
    y += round(kopf_gr * 1.25)
    sub_gr = round(W * 0.026)
    text(img, (m, y), "Plüsch-Sportwagenbett für Katze & Hund",
         font(sub_gr), MUTED)
    y += round(sub_gr * 1.9)
    ImageDraw.Draw(img).rectangle([m, y, W - m, y], fill=(215, 210, 204))
    y += round(H * 0.026)
    text(img, (m, y), PREIS, font(round(W * 0.038), True), TINTE)

    os.makedirs(HIER, exist_ok=True)
    pfad = os.path.join(HIER, name)
    img.save(pfad, "PNG", optimize=True)
    print("->", name, "%dx%d" % (W, H))
    return pfad


if __name__ == "__main__":
    bauen(1080, 1080, "katzenauto_ki_1080x1080.png")
    bauen(1080, 1920, "katzenauto_ki_1080x1920.png")
    bauen(1200, 628, "katzenauto_ki_1200x628.png")
