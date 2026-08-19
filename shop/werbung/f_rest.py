# -*- coding: utf-8 -*-
"""Entwurf F - "Der Rest laeuft zurueck."

WARUM ES DIESES MOTIV GIBT

Am 18.8.2026 in einem deutschen Hundeforum nachgelesen. Zweimal
unabhaengig, unaufgefordert, jeweils als DER Grund fuer eine
Kaufempfehlung:

  "Man kann das Wasser, was der Hund nicht trinkt wieder zurueck in die
   Flasche giessen, also keine Verschwendung."

  "nicht getrunken Wasser kann wieder in die Flasche zuruecklaufen.
   Klare Kaufempfehlung."

Das Merkmal steht auf der Startseite und kam in keiner einzigen Anzeige
vor. Die anderen fuenf Motive sind aus dem Produkt heraus geschrieben -
dieses aus dem, was Leute von selbst loben.

BELEGT? Ja. Im eigenen Film sichtbar und woertlich auf der Seite:
"Das uebrige Wasser laeuft zurueck in die Flasche."

Farbe Gruen statt Tuerkis, damit sich das Motiv im Anzeigensatz von
A-hand und C-napf unterscheidet - sonst sieht der Verlauf dreimal
dasselbe.
"""
from lib_studio import *

FARBE = "gruen"
SUB = "550 ml  ·  Sechs Farben"


def quadrat():
    W = H = 1080
    m = 88
    img = studio_bg(W, H, horizon=828)
    stelle(img, flasche(FARBE), hoehe=742, cx=792, boden_y=884)

    text(img, (m, m), "LET'SDRINK", font(20, True), MUTED, track=3.4)
    y = block(img, (m, 348), ["Der Rest", "läuft", "zurück."], font(88, True),
              lh=96, track=-2.2)
    text(img, (m, y + 34), "Kein Wasser, das du wegkippst.", font(29), MUTED)

    linie(img, m, H - m - 64, W - m)
    text(img, (m, H - m - 34), "letsdrink-pet.com", font(24), MUTED, track=0.6)
    text(img, (W - m, H - m - 39), "CHF 37.91", font(30, True), TEXT, anchor="rs")
    speichern(img, "F-rest_1080x1080.png")


def story():
    W, H = 1080, 1920
    m = 96
    img = studio_bg(W, H, horizon=1356)
    stelle(img, flasche(FARBE), hoehe=740, cx=560, boden_y=1414,
           a_blur=46, a_w=1.5)

    text(img, (m, 270), "LET'SDRINK", font(22, True), MUTED, track=3.8)
    block(img, (m, 356), ["Der Rest", "läuft", "zurück."], font(96, True),
          lh=104, track=-2.4)

    linie(img, m, 1486, W - m)
    text(img, (m, 1516), SUB, font(30), MUTED)
    text(img, (m, 1560), "Gratisversand in der Schweiz", font(30), MUTED)
    text(img, (W - m, 1508), "CHF 37.91", font(44, True), TEXT, anchor="rs")
    text(img, (W - m, 1562), "letsdrink-pet.com", font(28), MUTED,
         track=0.6, anchor="rs")
    speichern(img, "F-rest_1080x1920.png")


def link():
    W, H = 1200, 628
    m = 72
    img = studio_bg(W, H, horizon=470)
    stelle(img, flasche(FARBE), hoehe=498, cx=958, boden_y=534,
           a_blur=34, a_h=0.085)

    text(img, (m, 56), "LET'SDRINK", font(18, True), MUTED, track=3.2)
    y = block(img, (m, 176), ["Der Rest läuft", "zurück."], font(72, True),
              lh=78, track=-1.8)
    text(img, (m, y + 24), "Kein Wasser, das du wegkippst.", font(25), MUTED)

    linie(img, m, H - m - 56, 640)
    text(img, (m, H - m - 32), "letsdrink-pet.com", font(23), MUTED, track=0.6)
    text(img, (640, H - m - 37), "CHF 37.91", font(29, True), TEXT, anchor="rs")
    speichern(img, "F-rest_1200x628.png")


if __name__ == "__main__":
    quadrat(); story(); link()
