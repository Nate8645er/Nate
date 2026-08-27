#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Katzenauto-Anzeige: echtes Lieferantenfoto (Hund+Katze im Produkt,
mit echten Massangaben), eigener Marken-/Preis-Rahmen darauf.

Kein KI-Bild noetig - das Lieferantenfoto zeigt bereits das echte
Produkt aus dem Import. Nur der fremde Sprechblasen-Text der
Lieferantengrafik wurde weggeschnitten (bilder/katzenauto-clean.png).

Kein Domainname im Bild: der Shop laeuft noch unter der alten
letsdrink-pet.com-Adresse, die zur neuen Marke nicht passt. Erst wenn
Nate einen Shopnamen/eine Domain festlegt, gehoert die hierher.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.abspath(os.path.join(HIER, "..", "..",
                                    "marketing", "anzeigen", "quelle"))
QUELLE = os.path.join(HIER, "bilder", "katzenauto-clean.png")

TUERKIS_ORANGE = (232, 119, 34)   # aus dem Produktfoto selbst
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
    y0 = round(rh * 0.30)
    y0 = min(y0, rh - photo_h)
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
    bauen(1080, 1080, "katzenauto_1080x1080.png")
    bauen(1080, 1920, "katzenauto_1080x1920.png")
    bauen(1200, 628, "katzenauto_1200x628.png")
