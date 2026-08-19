# -*- coding: utf-8 -*-
"""Randlose Fotomotive - Bild ueber die ganze Flaeche, Text darauf.

WARUM ES DIESE DATEI GIBT

Nate am 19.8.2026: "Neue werbe bilder dise sehen zu amateur aus."

Er hat recht, und der Vergleich im eigenen Ordner beweist es. A-hand
und B-farben sehen aus wie eine Marke. H, I, J und K sahen aus wie
eine Vorlage: ein hartes Rechteck Foto oben, ein weisser Kasten
unten, dazwischen eine Naht - und rechts neben der Ueberschrift ein
totes weisses Feld. Zwei Haelften, die nichts miteinander zu tun
haben, weil sie nicht einmal denselben Grund teilen.

Randlos war meine erste Idee gewesen. Ich hatte sie verworfen, weil
weisse Schrift auf hellem Fell nur 1.62 zu 1 Kontrast hatte - noetig
sind 4.5. Der Schluss war falsch: die Antwort auf zu wenig Kontrast
ist nicht, das Foto in einen Kasten zu sperren, sondern einen Verlauf
darunterzulegen. Das macht jede Marke so, die Text auf Bilder setzt.

WAS HIER ANDERS IST ALS EIN GERATENER VERLAUF

Die Deckkraft wird nicht gewaehlt, sondern gesucht. Der Bau legt den
Verlauf probeweise an, misst auf dem fertig ueberlagerten Bild den
HELLSTEN Bereich hinter jeder Textzeile (92. Perzentil, nicht den
Mittelwert - ein Mittelwert verschweigt genau die helle Stelle, an der
die Schrift verschwindet) und nimmt die kleinste Deckkraft, die
ueberall 4.5 zu 1 haelt. So bleibt das Foto so hell wie moeglich und
die Schrift trotzdem sicher lesbar - auf JEDEM Bild, auch auf einem,
das erst spaeter dazukommt.

FARBE

Das Tuerkis stammt aus dem echten Freisteller, nicht aus dem Kopf:
oberer Napfbereich von tuerkis.png, hellere Haelfte, haeufigster Wert
= #45B6B2. Es traegt die Markenzeile und bindet den Rahmen an das
Produkt.
"""
import os
from PIL import Image, ImageDraw
from lib_studio import (HIER, PREIS, font, text, block, fit_font,
                        speichern)

TIERE = os.path.join(HIER, "tiere")

WEISS = (255, 255, 255)
TUERKIS = (69, 182, 178)      # gemessen aus frei-sauber/tuerkis.png
SCHLEIER = (9, 11, 13)        # fast schwarz, leicht kuehl - nicht reines
                              # Schwarz: das wirkt auf Fotos wie ein Loch
ZIEL = 4.5                    # WCAG AA fuer Fliesstext


# --- Messen ------------------------------------------------------------
def _lin(k):
    k = k / 255.0
    return k / 12.92 if k <= 0.04045 else ((k + 0.055) / 1.055) ** 2.4


def leuchtdichte(rgb):
    r, g, b = (_lin(k) for k in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontrast(a, b):
    la, lb = leuchtdichte(a), leuchtdichte(b)
    hell, dunkel = max(la, lb), min(la, lb)
    return (hell + 0.05) / (dunkel + 0.05)


def schlimmster_grund(img, kasten, perzentil=0.92):
    """Hellster nennenswerter Grundton in einem Kasten.

    Nicht der Mittelwert: der verschweigt die eine helle Stelle, an der
    weisse Schrift verschwindet. Nicht das Maximum: ein einzelnes
    Glanzlicht wuerde den ganzen Verlauf unnoetig dunkel machen. Das
    92. Perzentil trifft die Stelle, die wirklich stoert.
    """
    x0, y0, x1, y1 = (max(0, round(k)) for k in kasten)
    x1 = min(img.width, max(x1, x0 + 1))
    y1 = min(img.height, max(y1, y0 + 1))
    aus = img.crop((x0, y0, x1, y1)).convert("RGB")
    if aus.width * aus.height > 40000:        # schneller, gleiches Ergebnis
        aus = aus.resize((200, 200), Image.BILINEAR)
    px = list(aus.getdata())
    px.sort(key=leuchtdichte)
    return px[min(len(px) - 1, int(len(px) * perzentil))]


# --- Verlauf -----------------------------------------------------------
def deckung(img, weich_ab, voll_ab, alpha, farbe=SCHLEIER):
    """Verlauf: durchsichtig bei weich_ab, volle Deckung ab voll_ab.

    WARUM DER ANLAUF OBERHALB DES TEXTES LIEGT

    Erste Fassung liess den Verlauf am oberen Rand des Textblocks
    beginnen und erst am unteren Bildrand voll werden. Ergebnis auf dem
    Bergmotiv: selbst bei voller Deckkraft nur 1.1 zu 1 an der obersten
    Zeile - dort war der Schleier eben noch fast durchsichtig. Der
    Anlauf gehoert oberhalb des Textes, nicht hinein: ueber dem Block
    klingt er weich aus, unter seiner Oberkante deckt er durchgehend.
    So sitzt jede Zeile auf demselben Grund und die weiche Kante bleibt
    trotzdem unsichtbar.
    """
    W, H = img.size
    weich_ab = max(0, round(weich_ab))
    voll_ab = max(weich_ab + 1, round(voll_ab))
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    spanne = voll_ab - weich_ab
    for y in range(weich_ab, H):
        t = min(1.0, (y - weich_ab) / spanne)
        s = t * t * (3 - 2 * t)
        d.line([(0, y), (W, y)], fill=int(255 * alpha * s))
    img.paste(Image.new("RGB", (W, H), farbe), (0, 0), lay)
    return img


def deckung_seite(img, voll_bis, weich_bis, alpha, farbe=SCHLEIER):
    """Waagrecht: volle Deckung bis voll_bis, danach weich bis weich_bis.

    Fuer 1200x628. Ein Querformat ist nur 628 hoch; ein Verlauf von
    unten fraesse das halbe Bild. Seitlich bleibt das Motiv ganz. Wie
    beim senkrechten liegt der Anlauf ausserhalb der Textspalte.
    """
    W, H = img.size
    voll_bis = max(0, round(voll_bis))
    weich_bis = max(voll_bis + 1, round(weich_bis))
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    for x in range(0, min(W, weich_bis)):
        t = 1.0 if x <= voll_bis else 1 - (x - voll_bis) / (weich_bis - voll_bis)
        s = t * t * (3 - 2 * t)
        d.line([(x, 0), (x, H)], fill=int(255 * alpha * s))
    img.paste(Image.new("RGB", (W, H), farbe), (0, 0), lay)
    return img


# --- Foto --------------------------------------------------------------
def randlos(name, W, H, anker=0.5):
    """Foto auf genau W x H bringen, ohne zu verzerren - Motiv fuellt alles."""
    im = Image.open(os.path.join(TIERE, name)).convert("RGB")
    ziel, ist = W / H, im.width / im.height
    if ist > ziel:
        nb = round(im.height * ziel)
        im = im.crop((round((im.width - nb) * anker), 0,
                      round((im.width - nb) * anker) + nb, im.height))
    else:
        nh = round(im.width / ziel)
        im = im.crop((0, round((im.height - nh) * anker),
                      im.width, round((im.height - nh) * anker) + nh))
    return im.resize((W, H), Image.LANCZOS)


# --- Motive ------------------------------------------------------------
def _regle(img, bau, kaesten, farben, ziele):
    """Kleinste Deckkraft finden, die JEDE Zeile ihr eigenes Ziel halten laesst.

    bau(img, alpha) legt den Verlauf an. Statt eine Zahl zu waehlen und
    zu hoffen, wird sie gesucht: probeweise ueberlagern, auf dem
    Ergebnis messen, erst dann entscheiden. Die Ziele sind
    unterschiedlich, weil die Regel es ist - Schrift braucht 4.5 zu 1,
    eine Flaeche 3 zu 1.
    """
    letzte = None
    for i in range(0, 15):
        a = 0.30 + i * 0.05
        probe = bau(img.copy(), a)
        werte = [kontrast(f, schlimmster_grund(probe, k))
                 for k, f in zip(kaesten, farben)]
        letzte = (a, werte, probe)
        if all(v >= z for v, z in zip(werte, ziele)):
            return a, werte, probe
    return letzte


def _pruefe(name, a, werte, ziele):
    print("     Deckung %.2f  Kontrast %s" %
          (a, "  ".join("%.1f" % v for v in werte)))
    schlecht = [(v, z) for v, z in zip(werte, ziele) if v < z]
    if schlecht:
        raise ValueError("%s: Kontrast %.1f unter %.1f" %
                         (name, schlecht[0][0], schlecht[0][1]))


def hoch(W, H, *, bild, kopf, unterzeile, name, anker=0.5):
    """Quadrat und Hochformat: Foto randlos, Text unten auf dem Verlauf."""
    img = randlos(bild, W, H, anker)
    m = round(W * 0.083)
    story = H / W >= 1.5
    # Bei 1080x1920 liegen unten rund 250 px Bedienelemente der App ueber
    # dem Bild. Was dort steht, ist verdeckt - also bleibt es frei.
    unten = round(H * 0.155) if story else round(H * 0.078)

    marke_gr = round(W * 0.022)
    fuss_gr = round(W * 0.023)
    preis_gr = round(W * 0.031)
    sub_gr = round(W * 0.026)
    kopf_gr = min(round(W * 0.090),
                  min(fit_font(z, W - 2 * m, True, track=-2.0) for z in kopf))
    lh = round(kopf_gr * 1.04)
    bh = max(3, round(W * 0.0037))            # Hoehe des Akzentbalkens

    fuss_y = H - unten - fuss_gr
    regel_y = fuss_y - round(H * 0.030)
    sub_y = regel_y - round(H * 0.026) - sub_gr
    kopf_y = sub_y - round(H * 0.022) - lh * len(kopf)
    marke_y = kopf_y - round(H * 0.028) - marke_gr
    balken_y = marke_y - round(H * 0.026) - bh

    # WARUM DAS TUERKIS EIN BALKEN IST UND KEINE SCHRIFTFARBE
    # Erste Fassung setzte "Let'sDrink" in #45B6B2 auf das Foto. Gemessen
    # auf dem Bergmotiv: 1.2 zu 1. Das ist kein Einstellfehler, sondern
    # unmoeglich - die Farbe hat Leuchtdichte 0.375, fuer 4.5 zu 1
    # muesste der Grund unter 0.044 liegen, und genau dort oben ist der
    # Verlauf absichtlich noch fast durchsichtig. Als Flaeche gilt 3 zu 1
    # statt 4.5, und ein kurzer Balken ueber der Marke ist ohnehin das
    # bessere Zeichen: er wirkt gesetzt, nicht eingefaerbt.
    kaesten = [(m, balken_y, m + round(W * 0.068), balken_y + bh),
               (m, marke_y, W - m, marke_y + marke_gr * 1.35),
               (m, kopf_y, W - m, kopf_y + lh * len(kopf)),
               (m, sub_y, W - m, sub_y + sub_gr * 1.4),
               (m, fuss_y, W - m, fuss_y + preis_gr * 1.4)]
    farben = [TUERKIS, WEISS, WEISS, WEISS, WEISS]
    ziele = [3.0, ZIEL, ZIEL, ZIEL, ZIEL]

    a, werte, img = _regle(
        img, lambda b, al: deckung(b, balken_y - round(H * 0.34),
                                   balken_y, al),
        kaesten, farben, ziele)

    ImageDraw.Draw(img).rectangle(
        [m, balken_y, m + round(W * 0.068), balken_y + bh - 1], fill=TUERKIS)
    text(img, (m, marke_y), "Let'sDrink", font(marke_gr, True),
         (236, 236, 238), track=0.6)
    block(img, (m, kopf_y), kopf, font(kopf_gr, True), lh=lh,
          fill=WEISS, track=-kopf_gr * 0.028)
    text(img, (m, sub_y), unterzeile, font(sub_gr), (232, 232, 234))
    ImageDraw.Draw(img).rectangle([m, regel_y, W - m, regel_y],
                                  fill=(120, 122, 126))
    text(img, (m, fuss_y + round(preis_gr * 0.22)), "letsdrink-pet.com",
         font(fuss_gr), (208, 208, 212), track=0.6)
    text(img, (W - m, fuss_y), PREIS, font(preis_gr, True), WEISS,
         anchor="rs")
    _pruefe(name, a, werte, ziele)
    speichern(img, name)


def quer_voll(W, H, *, bild, kopf, unterzeile, name, anker=0.5, hell=False):
    """Querformat: Foto randlos, Verlauf von links, Text in der linken Haelfte.

    hell=True dreht dieselbe Anordnung um: heller Schleier, dunkle
    Schrift. Gebraucht fuer H-tiere - dort liegen die sechs Flaschen in
    der linken Bildhaelfte, also genau unter der Textspalte, und ein
    dunkler Schleier verschluckt sie. Derselbe Fehler wie im Quadrat,
    nur eine Achse weiter; beim ersten Durchgang hatte ich ihn nur dort
    behoben und das Querformat wieder nicht angesehen.
    """
    img = randlos(bild, W, H, anker)
    m = round(W * 0.055)
    spalte = round(W * 0.46)

    marke_gr = round(W * 0.019)
    fuss_gr = round(W * 0.019)
    preis_gr = round(W * 0.026)
    sub_gr = round(W * 0.021)
    kopf_gr = min(round(W * 0.056),
                  min(fit_font(z, spalte, True, track=-2.0) for z in kopf))
    lh = round(kopf_gr * 1.06)
    bh = max(3, round(W * 0.0033))

    balken_y = round(H * 0.135)
    marke_y = balken_y + bh + round(H * 0.045)
    kopf_y = marke_y + round(H * 0.090)
    sub_y = kopf_y + lh * len(kopf) + round(H * 0.035)
    fuss_y = H - round(H * 0.105)
    regel_y = fuss_y - round(H * 0.048)

    kaesten = [(m, balken_y, m + round(W * 0.055), balken_y + bh),
               (m, marke_y, m + spalte, marke_y + marke_gr * 1.35),
               (m, kopf_y, m + spalte, kopf_y + lh * len(kopf)),
               (m, sub_y, m + spalte, sub_y + sub_gr * 1.4),
               (m, fuss_y, m + spalte, fuss_y + preis_gr * 1.4)]
    if hell:
        akzent, marke_f, kopf_f, sub_f = (TUERKIS_TIEF, TINTE_MATT, TINTE,
                                          TINTE_MATT)
        fuss_f, preis_f, regel_f, schleier = (TINTE_MATT, TINTE,
                                              (200, 198, 193), PAPIER)
    else:
        akzent, marke_f, kopf_f, sub_f = (TUERKIS, (236, 236, 238), WEISS,
                                          (232, 232, 234))
        fuss_f, preis_f, regel_f, schleier = ((208, 208, 212), WEISS,
                                              (120, 122, 126), SCHLEIER)
    farben = [akzent, marke_f, kopf_f, sub_f, preis_f]
    ziele = [3.0, ZIEL, ZIEL, ZIEL, ZIEL]

    a, werte, img = _regle(
        img, lambda b, al: deckung_seite(b, round(W * 0.54), round(W * 0.86),
                                         al, schleier),
        kaesten, farben, ziele)

    ImageDraw.Draw(img).rectangle(
        [m, balken_y, m + round(W * 0.055), balken_y + bh - 1], fill=akzent)
    text(img, (m, marke_y), "Let'sDrink", font(marke_gr, True), marke_f,
         track=0.6)
    block(img, (m, kopf_y), kopf, font(kopf_gr, True), lh=lh,
          fill=kopf_f, track=-kopf_gr * 0.028)
    text(img, (m, sub_y), unterzeile, font(sub_gr), sub_f)
    ImageDraw.Draw(img).rectangle([m, regel_y, m + spalte, regel_y],
                                  fill=regel_f)
    text(img, (m, fuss_y + round(preis_gr * 0.20)), "letsdrink-pet.com",
         font(fuss_gr), fuss_f, track=0.6)
    text(img, (m + spalte, fuss_y), PREIS, font(preis_gr, True), preis_f,
         anchor="rs")
    _pruefe(name, a, werte, ziele)
    speichern(img, name)


def alle_drei(*, bild, anker, kopf, unterzeile, praefix):
    hoch(1080, 1080, bild=bild, anker=anker, kopf=kopf,
         unterzeile=unterzeile, name="%s_1080x1080.png" % praefix)
    hoch(1080, 1920, bild=bild, anker=anker, kopf=kopf,
         unterzeile=unterzeile, name="%s_1080x1920.png" % praefix)
    quer_voll(1200, 628, bild=bild, anker=anker, kopf=kopf,
              unterzeile=unterzeile, name="%s_1200x628.png" % praefix)


# --- Helle Fassung: Text oben, Produkt unten unberuehrt ----------------
def deckung_oben(img, voll_bis, weich_bis, alpha, farbe):
    """Deckung von oben: voll bis voll_bis, danach weich auslaufend."""
    W, H = img.size
    voll_bis = max(0, round(voll_bis))
    weich_bis = max(voll_bis + 1, round(weich_bis))
    lay = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(lay)
    for y in range(0, min(H, weich_bis)):
        t = 1.0 if y <= voll_bis else 1 - (y - voll_bis) / (weich_bis - voll_bis)
        s = t * t * (3 - 2 * t)
        d.line([(0, y), (W, y)], fill=int(255 * alpha * s))
    img.paste(Image.new("RGB", (W, H), farbe), (0, 0), lay)
    return img


def dunkler(farbe, ziel, grund):
    """Denselben Farbton so weit abdunkeln, bis er ziel zu 1 gegen grund haelt.

    #45B6B2 hat Leuchtdichte 0.375. Gegen den hellen Schleier (0.905)
    sind das 2.3 zu 1 - und das ist keine Einstellungsfrage, sondern
    eine Obergrenze: fuer 3 zu 1 muesste die Farbe unter 0.268 liegen.
    Ein Markenton auf hellem Grund muss also dunkler sein. Er wird hier
    abgeleitet und nicht getippt, damit er derselbe Ton bleibt.
    """
    k = 1.0
    while k > 0.2:
        kand = tuple(max(0, round(c * k)) for c in farbe)
        if kontrast(kand, grund) >= ziel:
            return kand
        k -= 0.01
    return (0, 0, 0)


PAPIER = (250, 249, 246)      # derselbe Ton wie der Studiogrund
TINTE = (17, 17, 17)
TINTE_MATT = (92, 92, 98)
# Abgeleitet, nicht getippt: #338784, gemessen 4.04 zu 1 gegen PAPIER.
TUERKIS_TIEF = dunkler(TUERKIS, 4.0, PAPIER)



def hoch_hell(W, H, *, bild, kopf, unterzeile, name, anker=0.5):
    """Text OBEN auf hellem Schleier, Produkt unten unberuehrt.

    WARUM ES DIESE ZWEITE FASSUNG BRAUCHT

    H-tiere ist kein Stimmungsbild, sondern ein Produktfoto: sechs
    Flaschen auf hellem Karton, Hund und Katze dahinter. Der dunkle
    Verlauf der anderen drei Motive legte sich genau ueber die sechs
    Flaschen - also ueber das Einzige, was dieses Motiv zeigen soll.
    Gemessen war es richtig und gestalterisch trotzdem falsch.

    Hier laeuft es umgekehrt: heller Schleier von oben ueber den leeren
    Karton, dunkle Schrift darauf, und die untere Bildhaelfte mit den
    Flaschen bleibt unangetastet. Dieselbe Messung, dieselbe Grenze -
    nur andersherum.
    """
    img = randlos(bild, W, H, anker)
    m = round(W * 0.083)
    oben = round(H * 0.072)

    marke_gr = round(W * 0.022)
    fuss_gr = round(W * 0.023)
    preis_gr = round(W * 0.031)
    sub_gr = round(W * 0.026)
    kopf_gr = min(round(W * 0.090),
                  min(fit_font(z, W - 2 * m, True, track=-2.0) for z in kopf))
    lh = round(kopf_gr * 1.04)
    bh = max(3, round(W * 0.0037))

    balken_y = oben
    marke_y = balken_y + bh + round(H * 0.026)
    kopf_y = marke_y + marke_gr + round(H * 0.028)
    sub_y = kopf_y + lh * len(kopf) + round(H * 0.022)
    kopfende = sub_y + round(sub_gr * 1.4)

    # FUSSZEILE GANZ NACH UNTEN, NICHT DIREKT UNTER DIE UNTERZEILE.
    # Erste Fassung stellte sie gleich hinter den Block - sie landete
    # damit genau auf den Flaschendeckeln: "letsdrink-pet.com" auf der
    # tuerkisen Kappe, PREIS auf der weissen. Gemessen war es in
    # Ordnung (der Grund dort ist hell), zu sehen war es trotzdem als
    # Beschriftung quer ueber die Ware. Unten steht sie frei.
    fuss_y = H - round(H * 0.062) - fuss_gr
    regel_y = fuss_y - round(H * 0.030)

    kaesten = [(m, balken_y, m + round(W * 0.068), balken_y + bh),
               (m, marke_y, W - m, marke_y + marke_gr * 1.35),
               (m, kopf_y, W - m, kopf_y + lh * len(kopf)),
               (m, sub_y, W - m, sub_y + sub_gr * 1.4),
               (m, fuss_y, W - m, fuss_y + preis_gr * 1.4)]
    farben = [TUERKIS_TIEF, TINTE_MATT, TINTE, TINTE_MATT, TINTE]
    ziele = [3.0, ZIEL, ZIEL, ZIEL, ZIEL]

    def zwei_schleier(b, al):
        b = deckung_oben(b, kopfende, kopfende + round(H * 0.26), al, PAPIER)
        return deckung(b, regel_y - round(H * 0.15),
                       regel_y - round(H * 0.012), al, PAPIER)

    a, werte, img = _regle(img, zwei_schleier, kaesten, farben, ziele)

    ImageDraw.Draw(img).rectangle(
        [m, balken_y, m + round(W * 0.068), balken_y + bh - 1],
        fill=TUERKIS_TIEF)
    text(img, (m, marke_y), "Let'sDrink", font(marke_gr, True), TINTE_MATT,
         track=0.6)
    block(img, (m, kopf_y), kopf, font(kopf_gr, True), lh=lh,
          fill=TINTE, track=-kopf_gr * 0.028)
    text(img, (m, sub_y), unterzeile, font(sub_gr), TINTE_MATT)
    ImageDraw.Draw(img).rectangle([m, regel_y, W - m, regel_y],
                                  fill=(200, 198, 193))
    text(img, (m, fuss_y + round(preis_gr * 0.22)), "letsdrink-pet.com",
         font(fuss_gr), TINTE_MATT, track=0.6)
    text(img, (W - m, fuss_y), PREIS, font(preis_gr, True), TINTE,
         anchor="rs")
    _pruefe(name, a, werte, ziele)
    speichern(img, name)


def alle_drei_hell(*, bild, anker, kopf, unterzeile, praefix):
    hoch_hell(1080, 1080, bild=bild, anker=anker, kopf=kopf,
              unterzeile=unterzeile, name="%s_1080x1080.png" % praefix)
    hoch_hell(1080, 1920, bild=bild, anker=anker, kopf=kopf,
              unterzeile=unterzeile, name="%s_1080x1920.png" % praefix)
    quer_voll(1200, 628, bild=bild, anker=anker, kopf=kopf,
              unterzeile=unterzeile, name="%s_1200x628.png" % praefix,
              hell=True)
