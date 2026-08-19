# -*- coding: utf-8 -*-
"""Entwurf C - "Der Napf ist fest angebaut."
Detailaufnahme mit Annotation: die Haarlinie zeigt auf die sichtbare Fuge
zwischen Napf und Korpus. Nur beschnitten, nichts retuschiert."""
from lib_studio import *

FARBE = "tuerkis"
FUGE_REL = 1062 / 2212        # Lage der Fuge auf der Flaschenhoehe


def voll(hoehe):
    im = flasche(FARBE)
    w = round(hoehe * im.width / im.height)
    return im.resize((w, round(hoehe)), Image.LANCZOS)


def quadrat():
    """Nahaufnahme: Flasche laeuft unten und rechts aus dem Bild."""
    W = H = 1080
    m = 88
    img = studio_bg(W, H)
    hoehe = 1660
    im = voll(hoehe)
    top, cx = -46, 840
    img.paste(im, (round(cx - im.width / 2), top), im)
    fuge = top + FUGE_REL * hoehe                       # = 751

    text(img, (m, m), "Let'sDrink", font(24, True), MUTED, track=0.4)
    block(img, (m, fuge - 214), ["Der Napf ist", "fest angebaut."],
          font(74, True), lh=82, track=-1.8)

    rechts = round(cx - im.width / 2) - 28
    linie(img, m, round(fuge), rechts)
    text(img, (m, fuge + 24), "550 ml  ·  Sechs Farben", font(26), MUTED)

    text_ink(img, m, 916, "CHF 37.91", font(38, True), TEXT, track=-0.8)
    text(img, (m, 986), "letsdrink-pet.com", font(24), MUTED, track=0.6)
    speichern(img, "C-napf_1080x1080.png")


def story():
    """Ganze Flasche, Annotation auf der Fuge. Inhalt in der Sicherheitszone."""
    W, H = 1080, 1920
    m = 88
    img = studio_bg(W, H, horizon=1512)
    hoehe = 990
    stelle(img, flasche(FARBE), hoehe=hoehe, cx=812, boden_y=1570,
           a_blur=48, a_w=1.45)
    top = 1570 - hoehe
    fuge = top + FUGE_REL * hoehe

    text(img, (m, 276), "Let'sDrink", font(26, True), MUTED, track=0.4)
    block(img, (m, 372), ["Der Napf ist", "fest angebaut."],
          font(96, True), lh=104, track=-2.4)

    bw = round(hoehe * 650 / 2212)
    linie(img, m, round(fuge), 812 - bw // 2 - 30)
    text(img, (m, fuge + 26), "550 ml", font(30), MUTED)
    text(img, (m, fuge + 70), "Sechs Farben", font(30), MUTED)

    text_ink(img, m, 1436, "CHF 37.91", font(56, True), TEXT, track=-1.2)
    text(img, (m, 1540), "letsdrink-pet.com", font(28), MUTED, track=0.6)
    speichern(img, "C-napf_1080x1920.png")


def link():
    """Grosser Napf laeuft oben aus dem Bild, Fuge sitzt auf der Textkante."""
    W, H = 1200, 628
    m = 72
    img = studio_bg(W, H)
    hoehe = 1640
    im = voll(hoehe)
    fuge_ziel = 428
    top = round(fuge_ziel - FUGE_REL * hoehe)
    cx = 902
    img.paste(im, (round(cx - im.width / 2), top), im)

    text(img, (m, 54), "Let'sDrink", font(22, True), MUTED, track=0.4)
    block(img, (m, 232), ["Der Napf ist", "fest angebaut."],
          font(62, True), lh=68, track=-1.5)

    linie(img, m, fuge_ziel, round(cx - im.width / 2) - 26)
    text(img, (m, fuge_ziel + 22), "550 ml  ·  Sechs Farben", font(24), MUTED)

    text_ink(img, m, H - m - 44, "CHF 37.91", font(32, True), TEXT, track=-0.7)
    text(img, (m + 230, H - m - 40), "letsdrink-pet.com", font(23), MUTED, track=0.6)
    speichern(img, "C-napf_1200x628.png")


if __name__ == "__main__":
    quadrat(); story(); link()
