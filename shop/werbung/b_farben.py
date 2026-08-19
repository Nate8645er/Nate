# -*- coding: utf-8 -*-
"""Entwurf B - "Sechs Farben." Die ehrliche Reihe: alle sechs, gleich gross,
gleich belichtet, mit den echten Farbnamen. Kein Trick, reine Ware."""
from lib_studio import *

REIHE = [("weiss", "Weiss"), ("rosa", "Rosa"), ("gruen", "Grün"),
         ("tuerkis", "Türkis"), ("grau", "Grau"), ("schwarz", "Schwarz")]


def zeile(img, x0, x1, boden_y, hoehe, label_f=None, label_dy=54):
    n = len(REIHE)
    bw = hoehe * 650 / 2212
    gap = ((x1 - x0) - n * bw) / (n - 1)
    for i, (datei, name) in enumerate(REIHE):
        cx = x0 + bw / 2 + i * (bw + gap)
        stelle(img, flasche(datei), hoehe=hoehe, cx=cx, boden_y=boden_y,
               kontakt=0.34, ambient=0.10, a_w=1.30, a_blur=max(16, hoehe // 14))
        if label_f:
            text(img, (cx, boden_y + label_dy), name.upper(), label_f, MUTED,
                 track=2.0, anchor="ms")


def quadrat():
    W = H = 1080
    m = 76
    img = studio_bg(W, H)
    text(img, (m, 76), "LET'SDRINK", font(20, True), MUTED, track=3.4)
    text(img, (m, 196), "Sechs Farben.", font(92, True), TEXT, track=-2.4)
    text(img, (m, 308), "550 ml", font(28), MUTED)

    zeile(img, m, W - m, boden_y=800, hoehe=430, label_f=font(17, True))

    linie(img, m, H - m - 62, W - m)
    text(img, (m, H - m - 33), "letsdrink-pet.com", font(24), MUTED, track=0.6)
    text(img, (W - m, H - m - 38), "CHF 37.91", font(30, True), TEXT, anchor="rs")
    speichern(img, "B-farben_1080x1080.png")


def story():
    W, H = 1080, 1920
    m = 64
    img = studio_bg(W, H)
    text(img, (m + 20, 280), "LET'SDRINK", font(22, True), MUTED, track=3.8)
    text(img, (m + 20, 380), "Sechs", font(118, True), TEXT, track=-3.0)
    text(img, (m + 20, 508), "Farben.", font(118, True), TEXT, track=-3.0)
    text(img, (m + 20, 690), "550 ml", font(30), MUTED)

    zeile(img, m, W - m, boden_y=1300, hoehe=450, label_f=font(18, True),
          label_dy=58)

    linie(img, m + 20, 1430, W - m - 20)
    text(img, (m + 20, 1462), "Gratisversand in der Schweiz", font(28), MUTED)
    text(img, (m + 20, 1506), "14 Tage Rückgabe", font(28), MUTED)
    text(img, (m + 20, 1550), "letsdrink-pet.com", font(28), MUTED, track=0.6)
    text(img, (W - m - 20, 1456), "CHF 37.91", font(46, True), TEXT, anchor="rs")
    speichern(img, "B-farben_1080x1920.png")


def link():
    W, H = 1200, 628
    m = 64
    img = studio_bg(W, H)
    text(img, (m, 62), "LET'SDRINK", font(18, True), MUTED, track=3.2)
    text(img, (m, 152), "Sechs", font(70, True), TEXT, track=-1.8)
    text(img, (m, 228), "Farben.", font(70, True), TEXT, track=-1.8)
    text(img, (m, 330), "550 ml", font(25), MUTED)

    linie(img, m, 402, 356)
    text_ink(img, m, 428, "CHF 37.91", font(32, True), TEXT, track=-0.7)
    text(img, (m, 484), "Gratisversand in der Schweiz", font(22), MUTED)
    text(img, (m, 518), "letsdrink-pet.com", font(22), MUTED, track=0.6)

    zeile(img, 420, W - m, boden_y=456, hoehe=330, label_f=font(15, True),
          label_dy=40)
    speichern(img, "B-farben_1200x628.png")


if __name__ == "__main__":
    quadrat(); story(); link()
