# -*- coding: utf-8 -*-
"""Entwurf G - "Ein Gegenstand statt zwei."

WARUM ES DIESES MOTIV GIBT

Aus derselben Recherche vom 18.8.2026. Der echte Gegner ist nicht ein
anderer Haendler, sondern die leere Mineralwasserflasche mit Faltnapf:

  "Ich nehm 0,5 Liter Einwegflaschen die verstau ich entweder in einer
   kleinen Guerteltasche ... dazu einen kleinen faltbaren Trinknapf"

  "Ich benutze am liebsten ne alte Fit-Flasche"

Gegen diese Loesung gewinnt man nicht mit Ausstattung, sondern mit
einem einzigen Satz: es ist ein Ding statt zwei. Das ist der einzige
echte Vorteil, den das Produkt gegenueber der Gratis-Alternative hat -
und er stand bisher in keiner Anzeige.

Farbe Rosa, damit sich das Motiv von allen anderen abhebt. ACHTUNG:
Rosa ist beim Lieferanten leer (Stand 18.8.2026). Das Motiv zeigt eine
Farbe, nicht ein Angebot - der Text nennt keine Farbe. Wird Rosa
dauerhaft gestrichen, hier auf Grau wechseln.
"""
from lib_studio import *

FARBE = "rosa"
SUB = "Für Hund und Katze  ·  550 ml"


def quadrat():
    W = H = 1080
    m = 88
    img = studio_bg(W, H, horizon=828)
    stelle(img, flasche(FARBE), hoehe=742, cx=792, boden_y=884)

    text(img, (m, m), "Let'sDrink", font(24, True), MUTED, track=0.4)
    y = block(img, (m, 348), ["Ein Gegenstand", "statt zwei."], font(76, True),
              lh=84, track=-1.9)
    text(img, (m, y + 34), "Flasche und Napf sind eins.", font(29), MUTED)
    text(img, (m, y + 76), SUB, font(25), MUTED)

    linie(img, m, H - m - 64, W - m)
    text(img, (m, H - m - 34), "letsdrink-pet.com", font(24), MUTED, track=0.6)
    text(img, (W - m, H - m - 39), PREIS, font(30, True), TEXT, anchor="rs")
    speichern(img, "G-einer_1080x1080.png")


def story():
    W, H = 1080, 1920
    m = 96
    img = studio_bg(W, H, horizon=1356)
    stelle(img, flasche(FARBE), hoehe=740, cx=560, boden_y=1414,
           a_blur=46, a_w=1.5)

    text(img, (m, 270), "Let'sDrink", font(26, True), MUTED, track=0.4)
    y = block(img, (m, 356), ["Ein Gegenstand", "statt zwei."], font(82, True),
              lh=90, track=-2.0)
    text(img, (m, y + 32), "Flasche und Napf sind eins.", font(30), MUTED)

    linie(img, m, 1486, W - m)
    text(img, (m, 1516), SUB, font(30), MUTED)
    text(img, (m, 1560), "Gratisversand in der Schweiz", font(30), MUTED)
    text(img, (W - m, 1508), PREIS, font(44, True), TEXT, anchor="rs")
    text(img, (W - m, 1562), "letsdrink-pet.com", font(28), MUTED,
         track=0.6, anchor="rs")
    speichern(img, "G-einer_1080x1920.png")


def link():
    W, H = 1200, 628
    m = 72
    img = studio_bg(W, H, horizon=470)
    stelle(img, flasche(FARBE), hoehe=498, cx=958, boden_y=534,
           a_blur=34, a_h=0.085)

    text(img, (m, 56), "Let'sDrink", font(22, True), MUTED, track=0.4)
    y = block(img, (m, 186), ["Ein Gegenstand", "statt zwei."], font(64, True),
              lh=70, track=-1.6)
    text(img, (m, y + 24), "Flasche und Napf sind eins.", font(25), MUTED)
    text(img, (m, y + 60), SUB, font(22), MUTED)

    linie(img, m, H - m - 56, 640)
    text(img, (m, H - m - 32), "letsdrink-pet.com", font(23), MUTED, track=0.6)
    text(img, (640, H - m - 37), PREIS, font(29, True), TEXT, anchor="rs")
    speichern(img, "G-einer_1200x628.png")


if __name__ == "__main__":
    quadrat(); story(); link()
