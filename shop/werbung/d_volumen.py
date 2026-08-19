# -*- coding: utf-8 -*-
"""Entwurf D - "550 ml" als Plakat.
Umgekehrte Grundflaeche (durchgehend #F1EFEB), Typografie traegt das Bild.
Einzige Aussage: das Volumen. Schwarze Ausfuehrung fuer maximale Trennung."""
from lib_studio import *

FARBE = "schwarz"


def hochformat(W, H, m, *, hoehe, boden_y, regel_y, giant_h, giant_w,
               brand_s, foot_s, price_s, foot_y, name):
    img = Image.new("RGB", (W, H), STUDIO)
    stelle(img, flasche(FARBE), hoehe=hoehe, cx=W / 2, boden_y=boden_y,
           kontakt=0.30, ambient=0.11, a_blur=max(20, hoehe // 16))

    # Markenschreibweise wie im Shop: "Let'sDrink", nicht gesperrte
    # Versalien. In "LET'SDRINK" mit 0.17 em Sperrung stand der
    # Apostroph als eigenes Zeichen und die Zeile las sich als
    # "LET' SDRINK".
    text(img, (m, m if H < 1500 else 280), "Let'sDrink",
         font(brand_s + 4, True), MUTED, track=0.4)

    linie(img, m, regel_y, W - m, (216, 213, 207))
    gs = fit_ink_height("550 ml", giant_h, True, track=-2.0, max_breite=giant_w)
    text_ink(img, m, regel_y + round(giant_h * 0.24), "550 ml", font(gs, True),
             TEXT, track=-gs * 0.02)

    text(img, (m, foot_y), "Für Hund und Katze", font(foot_s), MUTED)
    text(img, (m, foot_y + round(foot_s * 1.55)), "letsdrink-pet.com",
         font(foot_s), MUTED, track=0.6)
    text(img, (W - m, foot_y - round(price_s * 0.14)), "CHF 37.91",
         font(price_s, True), TEXT, anchor="rs")
    speichern(img, name)


def link():
    """Querformat: Produkt links, Zahl rechts - Landschaft braucht eine Achse."""
    W, H = 1200, 628
    m = 64
    img = Image.new("RGB", (W, H), STUDIO)
    stelle(img, flasche(FARBE), hoehe=452, cx=286, boden_y=534,
           kontakt=0.30, ambient=0.11, a_blur=30)

    sx, ex = 540, W - m
    text(img, (sx, 92), "Let'sDrink", font(22, True), MUTED, track=0.4)
    linie(img, sx, 236, ex, (216, 213, 207))
    gs = fit_ink_height("550 ml", 104, True, track=-2.0, max_breite=ex - sx)
    text_ink(img, sx, 268, "550 ml", font(gs, True), TEXT, track=-gs * 0.02)

    text(img, (sx, 424), "Für Hund und Katze", font(24), MUTED)
    text_ink(img, sx, 476, "CHF 37.91", font(34, True), TEXT, track=-0.7)
    text(img, (sx, 534), "letsdrink-pet.com", font(23), MUTED, track=0.6)
    speichern(img, "D-volumen_1200x628.png")


if __name__ == "__main__":
    hochformat(1080, 1080, 80, hoehe=560, boden_y=606, regel_y=676,
               giant_h=132, giant_w=780, brand_s=20, foot_s=24, price_s=30,
               foot_y=920, name="D-volumen_1080x1080.png")
    hochformat(1080, 1920, 88, hoehe=780, boden_y=1046, regel_y=1146,
               giant_h=176, giant_w=880, brand_s=22, foot_s=28, price_s=46,
               foot_y=1436, name="D-volumen_1080x1920.png")
    link()
