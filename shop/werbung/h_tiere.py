# -*- coding: utf-8 -*-
"""Entwurf H und I - die Motive, auf denen ein Tier zu sehen ist.

WARUM ES DIESE MOTIVE GIBT

Nate am 19.8.2026: "Man soll sehen das es fuer Hund und Katze ist."
Er hat recht. Auf den sieben Studio-Motiven steht nur die Flasche.
Wer sie nicht kennt, sieht eine Trinkflasche und denkt an sich selbst,
nicht an sein Tier. Die Zeile "Fuer Hund und Katze" steht jetzt auf
allen sieben - aber lesen ist nicht sehen.

WELCHES BILDMATERIAL - UND WARUM NICHT DAS ANDERE

Geprueft wurde die Flasche auf jedem Bild gegen den echten Freisteller:

  BENUTZT     tiere/letsdrink-hero-banner.jpg   Hund und Katze, sechs
              Flaschen. Klarer Koerper, tuerkiser Napf, Pfotenknopf -
              stimmt mit dem Produkt ueberein.
  BENUTZT     tiere/letsdrink-reisen-katze.jpg  Katze trinkt aus dem
              Napf. Bei 100 Prozent nachgesehen: gleiche Flasche.

  NICHT       shop/werbung/video/letsdrink-film-30s-9x16.mp4
              Der Film zeigt eine Flasche mit CREMEFARBENEM Koerper und
              eingepraegter Pfote. Nates sechs Flaschen haben alle einen
              klaren, durchsichtigen Koerper ohne Pfote. Ein anderes
              Modell. Wer das anklickt und Nates Flasche bekommt,
              schreibt eine Rueckgabe statt einer Empfehlung. Dazu
              nennt sein Abspann katzenufos.com.

AUFLOESUNG - EHRLICH GERECHNET

Die Tierbilder sind 955x1120 und 900x672 gross, die Anzeigen brauchen
1080 Breite. Deshalb liegt das Foto NICHT ueber die volle Flaeche,
sondern nimmt den oberen Teil ein; darunter steht der Text auf dem
ruhigen Grund der uebrigen Familie. So bleibt die Vergroesserung unter
1.2fach statt bei 1.7fach, und das Motiv passt trotzdem zu den anderen
sieben.
"""
import os
from PIL import Image
from lib_studio import (WEISS, STUDIO, TEXT, MUTED, HIER, font, text, block,
                        linie, speichern)

TIERE = os.path.join(HIER, "tiere")


def foto(name, breite, hoehe, anker=0.5):
    """Bild auf genau breite x hoehe bringen, ohne zu verzerren.

    anker 0 = oberer Rand, 1 = unterer Rand. Bei Tierbildern liegt der
    Kopf oben; ein zentrierter Anschnitt wuerde ihn abschneiden.
    """
    im = Image.open(os.path.join(TIERE, name)).convert("RGB")
    ziel = breite / hoehe
    ist = im.width / im.height
    if ist > ziel:                       # zu breit -> seitlich beschneiden
        nb = round(im.height * ziel)
        x = round((im.width - nb) / 2)
        im = im.crop((x, 0, x + nb, im.height))
    else:                                # zu hoch -> oben/unten beschneiden
        nh = round(im.width / ziel)
        y = round((im.height - nh) * anker)
        im = im.crop((0, y, im.width, y + nh))
    return im.resize((breite, hoehe), Image.LANCZOS)


def motiv(W, H, *, bild, anker, kopf, unterzeile, name, fotoanteil=0.60):
    fh = round(H * fotoanteil)
    img = Image.new("RGB", (W, H), WEISS)
    img.paste(foto(bild, W, fh, anker), (0, 0))

    m = round(W * 0.081)
    kopf_gr = round(W * 0.079)

    # MARKENZEILE UNTER DAS FOTO, NICHT DARAUF.
    # Erste Fassung setzte sie weiss auf das Bild. Nachgemessen auf dem
    # Hund-und-Katze-Motiv: der Grund dort ist helles Fell und heller
    # Karton, Helligkeit 0.600, Kontrast zu Weiss nur 1.62 zu 1 - noetig
    # sind 4.5. Sie war praktisch unsichtbar. Auf hellem Grund unter dem
    # Foto steht sie sicher, und die Leserichtung stimmt trotzdem:
    # Marke, Aussage, Preis.
    marke_gr = round(W * 0.022)
    y = fh + round(H * 0.040)
    text(img, (m, y), "Let'sDrink", font(marke_gr, True), MUTED, track=0.4)
    y += round(marke_gr * 2.1)

    y = block(img, (m, y), kopf, font(kopf_gr, True),
              lh=round(kopf_gr * 1.08), track=-kopf_gr * 0.025)
    text(img, (m, y + round(H * 0.018)), unterzeile,
         font(round(W * 0.027)), MUTED)

    fy = H - round(H * 0.055)
    linie(img, m, fy - round(H * 0.026), W - m)
    text(img, (m, fy), "letsdrink-pet.com", font(round(W * 0.022)), MUTED,
         track=0.6)
    text(img, (W - m, fy - round(H * 0.004)), "CHF 37.91",
         font(round(W * 0.028), True), TEXT, anchor="rs")
    speichern(img, name)


# --- H: Hund UND Katze in einem Bild -----------------------------------
H_KOPF = ["Für Hund", "und Katze."]
H_SUB = "550 ml  ·  Sechs Farben"
H_BILD = "letsdrink-hero-banner.jpg"

# --- I: die Katze allein, weil sie die Ueberraschung ist ----------------
I_KOPF = ["Auch für", "die Katze."]
I_SUB = "Ein Napf, der schon dran ist."
I_BILD = "letsdrink-reisen-katze.jpg"


if __name__ == "__main__":
    for W, H, anteil, suffix in ((1080, 1080, 0.58, "1080x1080"),
                                 (1080, 1920, 0.56, "1080x1920"),
                                 (1200, 628, 0.52, "1200x628")):
        motiv(W, H, bild=H_BILD, anker=0.35, kopf=H_KOPF, unterzeile=H_SUB,
              fotoanteil=anteil, name="H-tiere_%s.png" % suffix)
        motiv(W, H, bild=I_BILD, anker=0.30, kopf=I_KOPF, unterzeile=I_SUB,
              fotoanteil=anteil, name="I-katze_%s.png" % suffix)
