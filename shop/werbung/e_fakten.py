# -*- coding: utf-8 -*-
"""Entwurf E - Faktenblatt.
Alles, was wir wirklich wissen, als gesetzte Liste. Fuer den unteren Funnel:
Klarheit statt Stimmung. Keine Zeile ohne Deckung."""
from lib_studio import *

FARBE = "rosa"
FAKTEN = ["550 ml",
          "Sechs Farben",
          "Der Napf ist fest angebaut.",
          "Gratisversand in der Schweiz",
          "14 Tage Rückgabe"]


def liste(img, x, y, breite, f, *, zeile_h, pad):
    for i, z in enumerate(FAKTEN):
        linie(img, x, y + i * zeile_h, x + breite)
        text(img, (x, y + i * zeile_h + pad), z, f, TEXT)
    linie(img, x, y + len(FAKTEN) * zeile_h, x + breite)
    return y + len(FAKTEN) * zeile_h


def quadrat():
    W = H = 1080
    m = 84
    img = studio_bg(W, H, horizon=812)
    stelle(img, flasche(FARBE), hoehe=650, cx=852, boden_y=866,
           a_w=1.32, a_blur=38)

    text(img, (m, m), "LET'SDRINK", font(20, True), MUTED, track=3.4)
    text(img, (m, 190), "Auf einen Blick.", font(60, True), TEXT, track=-1.5)

    ende = liste(img, m, 340, 566, font(27), zeile_h=70, pad=21)
    text_ink(img, m, ende + 54, "CHF 37.91", font(54, True), TEXT, track=-1.1)
    text(img, (m, ende + 132), "letsdrink-pet.com", font(24), MUTED, track=0.6)
    speichern(img, "E-fakten_1080x1080.png")


def story():
    W, H = 1080, 1920
    m = 88
    img = studio_bg(W, H)
    stelle(img, flasche(FARBE), hoehe=740, cx=540, boden_y=1000,
           a_w=1.42, a_blur=46)

    text(img, (m, 288), "LET'SDRINK", font(22, True), MUTED, track=3.8)
    ende = liste(img, m, 1094, W - 2 * m, font(31), zeile_h=80, pad=24)

    text_ink(img, m, ende + 58, "CHF 37.91", font(66, True), TEXT, track=-1.5)
    text(img, (W - m, ende + 74), "letsdrink-pet.com", font(28), MUTED,
         track=0.6, anchor="rs")
    speichern(img, "E-fakten_1080x1920.png")


def link():
    W, H = 1200, 628
    m = 64
    img = studio_bg(W, H, horizon=474)
    stelle(img, flasche(FARBE), hoehe=456, cx=1002, boden_y=528,
           a_w=1.28, a_blur=32)

    text(img, (m, 54), "LET'SDRINK", font(18, True), MUTED, track=3.2)
    text(img, (m, 116), "Auf einen Blick.", font(44, True), TEXT, track=-1.1)

    ende = liste(img, m, 208, 600, font(24), zeile_h=56, pad=16)
    text_ink(img, m, ende + 34, "CHF 37.91", font(38, True), TEXT, track=-0.8)
    text(img, (m + 296, ende + 44), "letsdrink-pet.com", font(23), MUTED, track=0.6)
    speichern(img, "E-fakten_1200x628.png")


if __name__ == "__main__":
    quadrat(); story(); link()
