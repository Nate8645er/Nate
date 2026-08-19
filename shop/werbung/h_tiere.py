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
                        linie, speichern, fit_font)

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


def passend(txt, wunsch, breite, boden=None):
    """Groesse, bei der txt in breite passt - hoechstens wunsch.

    WARUM ES DAS GIBT

    Erster Lauf am 19.8.2026: K-berg trug die Unterzeile "Fuer Hund und
    Katze - Gratisversand in der Schweiz" in fester Groesse. Im
    Querformat ist die Textspalte 448 Pixel breit, die Zeile brauchte
    530 - sie lief rechts aus dem Bild und endete als "in der Schw".
    Eine feste Schriftgroesse hoechstens zu pruefen, statt sie rechnen
    zu lassen, ist genau der Fehler, den ich beim Kopf schon vermieden
    hatte.

    boden = Untergrenze. Wird sie erreicht, ist die Zeile zu lang und
    gehoert gekuerzt, nicht weiter geschrumpft - deshalb meldet die
    Funktion das laut, statt still unleserlich klein zu setzen.
    """
    gr = min(wunsch, fit_font(txt, breite, False, track=0.0))
    if boden is not None and gr < boden:
        raise ValueError(
            "Zeile zu lang fuer %d px: %r braucht %d px Schrift, "
            "Untergrenze ist %d. Text kuerzen." % (breite, txt, gr, boden))
    return gr


def quer(W, H, *, bild, anker, kopf, unterzeile, name, fotoanteil=0.52):
    """Querformat: Foto LINKS, Text RECHTS - nicht uebereinander.

    WARUM ES DIESE ZWEITE FUNKTION GIBT

    Die erste Fassung schickte auch 1200x628 durch motiv(). Am 19.8.2026
    nachgesehen, was dabei herauskam: bei 52 Prozent Fotoanteil bleiben
    fuer den Text 301 Pixel Hoehe, die zweizeilige Zeile in 95 px braucht
    aber allein 190 - plus Markenzeile, Unterzeile und Fuss. Die
    Ueberschrift lief unten aus dem Bild, die Trennlinie ging quer durch
    "und Katze." und die Adresse lag darunter. Im Quadrat und im
    Hochformat stimmte alles, deshalb war es beim Durchsehen nicht
    aufgefallen - ich hatte das Querformat schlicht nicht angeschaut.

    Ein Querformat kippt man nicht, man dreht es: die Achse laeuft
    seitlich statt uebereinander. Nebenbei wird auch der Anschnitt
    besser - 624x628 ist fast quadratisch, das Tier behaelt den Kopf,
    waehrend ein 1200x327-Streifen ihn abschneidet.
    """
    fw = round(W * fotoanteil)
    img = Image.new("RGB", (W, H), WEISS)
    img.paste(foto(bild, fw, H, anker), (0, 0))

    x = fw + round(W * 0.053)
    rechts = W - round(W * 0.053)
    breite = rechts - x

    marke_gr = round(W * 0.019)
    text(img, (x, round(H * 0.175)), "Let'sDrink", font(marke_gr, True),
         MUTED, track=0.4)

    # Groesse aus der Spaltenbreite ableiten, nicht raten: die laengste
    # Zeile bestimmt sie, gedeckelt bei 62 px, damit zwei Zeilen plus
    # Fuss sicher in die 628 passen.
    kopf_gr = min(62, min(fit_font(z, breite, True, track=-2.0) for z in kopf))
    y = block(img, (x, round(H * 0.285)), kopf, font(kopf_gr, True),
              lh=round(kopf_gr * 1.10), track=-kopf_gr * 0.025)
    text(img, (x, y + round(H * 0.028)), unterzeile,
         font(passend(unterzeile, round(W * 0.020), breite, boden=17)), MUTED)

    fy = H - round(H * 0.088)
    linie(img, x, fy - round(H * 0.042), rechts)
    text(img, (x, fy), "letsdrink-pet.com", font(round(W * 0.019)), MUTED,
         track=0.6)
    text(img, (rechts, fy - round(H * 0.008)), "CHF 37.91",
         font(round(W * 0.024), True), TEXT, anchor="rs")
    speichern(img, name)


def motiv(W, H, *, bild, anker, kopf, unterzeile, name, fotoanteil=0.60):
    """Gestapelt: Foto oben, Text darunter. Fotohoehe wird GERECHNET.

    WARUM DIE HOEHE GERECHNET WIRD

    Zweiter Fehler desselben Tages, diesmal senkrecht statt waagrecht.
    Die Fotohoehe stand fest bei 58 Prozent, und der Rest des Bildes
    musste eben reichen. Bei zwei Kopfzeilen reichte er. J-spaziergang
    hat drei ("Trinken, / ohne Napf / zu suchen.") - die dritte Zeile
    lag auf der Trennlinie und auf der Adresse.

    Jetzt laeuft es andersherum: erst wird ausgerechnet, wie hoch der
    Textteil wirklich ist, dann bekommt das Foto den Rest, hoechstens
    aber den gewuenschten Anteil. Eine Zeile mehr im Kopf schiebt das
    Foto nach oben, statt den Text aus dem Bild zu schieben. Wird das
    Foto dabei kleiner als ein Drittel, ist der Text zu lang - dann
    bricht es hier ab, statt still etwas Kaputtes zu speichern.
    """
    m = round(W * 0.081)
    kopf_gr = round(W * 0.079)
    marke_gr = round(W * 0.022)
    sub_gr = passend(unterzeile, round(W * 0.027), W - 2 * m, boden=20)
    lh = round(kopf_gr * 1.08)

    luft_oben = round(H * 0.040)        # zwischen Foto und Markenzeile
    nach_marke = round(marke_gr * 2.1)
    nach_kopf = round(H * 0.018)
    fy = H - round(H * 0.055)           # Grundlinie der Fusszeile
    regel_y = fy - round(H * 0.026)
    luft_unten = round(H * 0.030)       # zwischen Unterzeile und Regel

    hoch = nach_marke + lh * len(kopf) + nach_kopf + sub_gr
    platz = regel_y - luft_unten - hoch - luft_oben
    fh = min(round(H * fotoanteil), platz)
    if fh < round(H * 0.33):
        raise ValueError(
            "%s: Text braucht zu viel Hoehe, fuers Foto bleiben nur %d von "
            "%d px. Kopf kuerzen." % (name, fh, H))

    img = Image.new("RGB", (W, H), WEISS)
    img.paste(foto(bild, W, fh, anker), (0, 0))

    # MARKENZEILE UNTER DAS FOTO, NICHT DARAUF.
    # Erste Fassung setzte sie weiss auf das Bild. Nachgemessen auf dem
    # Hund-und-Katze-Motiv: der Grund dort ist helles Fell und heller
    # Karton, Helligkeit 0.600, Kontrast zu Weiss nur 1.62 zu 1 - noetig
    # sind 4.5. Sie war praktisch unsichtbar. Auf hellem Grund unter dem
    # Foto steht sie sicher, und die Leserichtung stimmt trotzdem:
    # Marke, Aussage, Preis.
    y = fh + luft_oben
    text(img, (m, y), "Let'sDrink", font(marke_gr, True), MUTED, track=0.4)
    y += nach_marke

    y = block(img, (m, y), kopf, font(kopf_gr, True), lh=lh,
              track=-kopf_gr * 0.025)
    text(img, (m, y + nach_kopf), unterzeile, font(sub_gr), MUTED)

    linie(img, m, regel_y, W - m)
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


def alle_drei(*, bild, anker, kopf, unterzeile, praefix):
    """Ein Motiv in allen drei Formaten - Hochformate gestapelt, Quer geteilt.

    Hochformat 1080x1920 laeuft mit 0.68 statt 0.56: bei 0.56 klaffte
    zwischen Unterzeile und Fusslinie eine leere Flaeche von 375 Pixeln,
    also fast ein Fuenftel des Bildes. Groesseres Foto schliesst die
    Luecke und zeigt mehr vom Tier - genau darum geht es bei diesen
    Motiven.
    """
    motiv(1080, 1080, bild=bild, anker=anker, kopf=kopf,
          unterzeile=unterzeile, fotoanteil=0.58,
          name="%s_1080x1080.png" % praefix)
    motiv(1080, 1920, bild=bild, anker=anker, kopf=kopf,
          unterzeile=unterzeile, fotoanteil=0.68,
          name="%s_1080x1920.png" % praefix)
    quer(1200, 628, bild=bild, anker=anker, kopf=kopf,
         unterzeile=unterzeile, name="%s_1200x628.png" % praefix)


if __name__ == "__main__":
    alle_drei(bild=H_BILD, anker=0.35, kopf=H_KOPF, unterzeile=H_SUB,
              praefix="H-tiere")
    alle_drei(bild=I_BILD, anker=0.30, kopf=I_KOPF, unterzeile=I_SUB,
              praefix="I-katze")
