# -*- coding: utf-8 -*-
"""Entwurf A - "Eine Hand reicht." Ruhiges Hero, ein Produkt, viel Weissraum.
Story haelt die Story-Sicherheitszone (Inhalt zwischen y=260 und y=1620)."""
from lib_studio import *

FARBE = "tuerkis"
SUB = "550 ml  ·  Sechs Farben"


def quadrat():
    W = H = 1080
    m = 88
    img = studio_bg(W, H, horizon=828)
    stelle(img, flasche(FARBE), hoehe=742, cx=792, boden_y=884)

    text(img, (m, m), "LET'SDRINK", font(20, True), MUTED, track=3.4)
    y = block(img, (m, 372), ["Eine Hand", "reicht."], font(96, True),
              lh=104, track=-2.4)
    text(img, (m, y + 36), SUB, font(29), MUTED)

    linie(img, m, H - m - 64, W - m)
    text(img, (m, H - m - 34), "letsdrink-pet.com", font(24), MUTED, track=0.6)
    text(img, (W - m, H - m - 39), "CHF 37.91", font(30, True), TEXT, anchor="rs")
    speichern(img, "A-hand_1080x1080.png")


def story():
    W, H = 1080, 1920
    m = 96
    img = studio_bg(W, H, horizon=1356)
    stelle(img, flasche(FARBE), hoehe=740, cx=560, boden_y=1414,
           a_blur=46, a_w=1.5)

    text(img, (m, 270), "LET'SDRINK", font(22, True), MUTED, track=3.8)
    block(img, (m, 372), ["Eine Hand", "reicht."], font(104, True),
          lh=112, track=-2.6)

    linie(img, m, 1486, W - m)
    text(img, (m, 1516), SUB, font(30), MUTED)
    text(img, (m, 1560), "Gratisversand in der Schweiz", font(30), MUTED)
    text(img, (W - m, 1508), "CHF 37.91", font(44, True), TEXT, anchor="rs")
    text(img, (W - m, 1562), "letsdrink-pet.com", font(28), MUTED,
         track=0.6, anchor="rs")
    speichern(img, "A-hand_1080x1920.png")


def link():
    W, H = 1200, 628
    m = 72
    img = studio_bg(W, H, horizon=470)
    stelle(img, flasche(FARBE), hoehe=498, cx=958, boden_y=534,
           a_blur=34, a_h=0.085)

    text(img, (m, 56), "LET'SDRINK", font(18, True), MUTED, track=3.2)
    y = block(img, (m, 196), ["Eine Hand", "reicht."], font(78, True),
              lh=84, track=-2.0)
    text(img, (m, y + 26), SUB, font(25), MUTED)

    linie(img, m, H - m - 56, 640)
    text(img, (m, H - m - 32), "letsdrink-pet.com", font(23), MUTED, track=0.6)
    text(img, (640, H - m - 37), "CHF 37.91", font(29, True), TEXT, anchor="rs")
    speichern(img, "A-hand_1200x628.png")


if __name__ == "__main__":
    quadrat(); story(); link()
