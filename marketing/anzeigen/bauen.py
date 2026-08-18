#!/usr/bin/env python3
"""Bildanzeigen fuer Meta - drei Motive in drei Formaten.

ALLES AUS DEM SHOP. Die Flaschen sind die freigestellten Bilder, die der
Shop selbst ausliefert; die Schrift ist Outfit, dieselbe Datei vom
eigenen CDN, aus woff2 zurueckgerechnet; die Farben sind die Token aus
n-nova.css. Wer die Anzeige sieht und danach den Laden, sieht zweimal
dasselbe. Das ist der ganze Zweck.

WAS NICHT DRAUFSTEHT, UND WARUM

Kein Preis. Nicht aus Vorsicht, sondern weil ein Betrag im Bild
einbrennt: aendert Nate ihn im Shop, laeuft die Anzeige mit dem alten
weiter, und die Preisbekanntgabeverordnung will am Ort des Kaufs den
Betrag, der wirklich faellig wird. Der Preis gehoert in den Anzeigentext
- der ist in zehn Sekunden geaendert, das Bild nicht.

Keine Bewertung, keine Sterne, keine Verkaufszahl: der Laden hat null
Bestellungen. Keine Dringlichkeit, kein Countdown, keine Verknappung.
Keine Aussage zur Dichtigkeit, kein Material, keine Masse, kein
Gewicht - belegt sind 550 ml und sechs Farben, mehr nicht.

DIE DREI MOTIVE

1 farben   Die sechs Flaschen nebeneinander. Das ist das einzige echte
           Unterscheidungsmerkmal, das sich beweisen laesst.
2 napf     Der Napf von nahem, mit Wasser darin. Zeigt die Produktidee
           in einem Bild, ohne ein Wort zu behaupten.
3 bank     Bank, Rucksack, Leine, Hundepfoten. Das Bild, das im Vorbei-
           scrollen anhaelt, weil es eine Lage zeigt statt ein Produkt.

DIE DREI FORMATE

1:1  1080x1080   Feed, aeltere Platzierungen
4:5  1080x1350   Feed - nimmt am Handy am meisten Hoehe ein
9:16 1080x1920   Reels, Stories

Im 9:16 sitzt der Text bewusst NICHT am Rand: Stories legen oben ihre
Fortschrittsbalken und unten den Absender darueber. Der Textblock haelt
sich deshalb zwischen 60 und 80 Prozent der Hoehe.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.path.join(HIER, "quelle")
THEME = os.path.abspath(os.path.join(HIER, "..", "..", "shop", "theme-nova", "assets"))
ZIEL = os.path.join(HIER, "bilder")

FETT = os.path.join(QUELLE, "a-sans-bold.ttf")
MAGER = os.path.join(QUELLE, "a-sans.ttf")

TEXT = "#111111"
GRUND = "#F5F4F1"
SANFT = "#6E6E73"
LINIE = "#D8D5CE"

FARBEN = ["rosa", "schwarz", "grau", "tuerkis", "gruen", "weiss"]
FORMATE = {"1x1": (1080, 1080), "4x5": (1080, 1350), "9x16": (1080, 1920)}


def schrift(pfad, groesse):
    return ImageFont.truetype(pfad, groesse)


def tropfen(groesse, farbe):
    """Der Wassertropfen aus dem Kopf des Shops.

    Der Pfad im Theme ist eine Bezier-Kurve auf 24x24. Hier aus Kreis
    und Dreieck nachgezogen und ueberabgetastet - das reicht bei dieser
    Groesse und spart eine SVG-Bibliothek, die es hier nicht gibt.
    """
    ue = 8
    n = groesse * ue
    b = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    r = n * 0.242
    mx, my = n / 2, n * 0.575
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=farbe)
    d.polygon([(mx, n * 0.133),
               (mx - r * 0.995, my + r * 0.10),
               (mx + r * 0.995, my + r * 0.10)], fill=farbe)
    return b.resize((groesse, groesse), Image.LANCZOS)


def marke(d, blatt, x, y, hoehe, farbe=TEXT):
    """Wortmarke mit Tropfen. Gibt die Unterkante zurueck."""
    t = tropfen(int(hoehe * 0.95), farbe)
    blatt.paste(t, (x, y), t)
    f = schrift(FETT, hoehe)
    d.text((x + t.width + int(hoehe * 0.28), y - int(hoehe * 0.08)),
           "Let'sDrink", font=f, fill=farbe)
    return y + hoehe


def fuellen(bild, breite, hoehe, anker=0.5):
    """Bild formatfuellend beschneiden.

    anker sagt, WELCHER Teil erhalten bleibt, wenn in der Hoehe
    beschnitten wird: 0 haelt die Oberkante, 1 die Unterkante, 0.5 die
    Mitte. Beim Napf-Motiv liegt der Napf oben - mit der Mitte als Anker
    schnitt er weg, und genau er ist das Motiv.
    """
    v_soll = breite / hoehe
    v_ist = bild.width / bild.height
    if v_ist > v_soll:
        neu = int(bild.height * v_soll)
        links = (bild.width - neu) // 2
        bild = bild.crop((links, 0, links + neu, bild.height))
    else:
        neu = int(bild.width / v_soll)
        oben = int((bild.height - neu) * anker)
        bild = bild.crop((0, oben, bild.width, oben + neu))
    return bild.resize((breite, hoehe), Image.LANCZOS)


def block_hoehe(breite, kopf, skala=None):
    """Wie hoch der Textblock wird - VOR dem Zeichnen.

    Die erste Fassung schaetzte die Feldhoehe und schnitt bei 1:1 und
    4:5 die Beizeile unten ab. Gemessen statt geraten: die Motive
    bestellen jetzt genau so viel Flaeche, wie der Block braucht.
    """
    s = skala or breite
    h = int(s * 0.052) + int(s * 0.055)                 # Wortmarke
    h += int(s * 0.105) * len(kopf)                     # Schlagzeilen
    h += int(s * 0.018) + int(s * 0.032)                # Strich und Abstand
    h += int(s * 0.050)                                 # Beizeile
    return h


def textblock(d, blatt, x, y, breite, kopf, zeile, skala=None):
    """Wortmarke, Schlagzeile, Trennstrich, Beizeile. Untere Kante zurueck.

    skala trennt die SCHRIFTGROESSE von der Spaltenbreite. Im geteilten
    Quadrat ist die Textspalte nur halb so breit wie das Bild - haengte
    die Groesse daran, schrumpfte die Schlagzeile auf die Haelfte und war
    im Feed nicht mehr zu lesen.
    """
    s = skala or breite
    y = marke(d, blatt, x, y, int(s * 0.052)) + int(s * 0.055)
    f_kopf = schrift(FETT, int(s * 0.088))
    for z in kopf:
        d.text((x, y), z, font=f_kopf, fill=TEXT)
        y += int(s * 0.105)
    y += int(s * 0.018)
    d.line([(x, y), (x + int(min(breite, s) * 0.72), y)], fill=LINIE, width=2)
    y += int(s * 0.032)
    d.text((x, y), zeile, font=schrift(MAGER, int(s * 0.040)), fill=SANFT)
    return y + int(s * 0.05)


def reihe(hoehe):
    """Die sechs Flaschen nebeneinander, als ein Bild mit Alpha."""
    bs = [Image.open(os.path.join(QUELLE, "a-flasche-%s.webp" % c)).convert("RGBA")
          for c in FARBEN]
    bs = [b.crop(b.getbbox()) for b in bs]
    skal = [b.resize((max(1, int(b.width * hoehe / b.height)), hoehe), Image.LANCZOS)
            for b in bs]
    lueck = int(hoehe * 0.055)
    br = sum(b.width for b in skal) + lueck * (len(skal) - 1)
    aus = Image.new("RGBA", (br, hoehe), (0, 0, 0, 0))
    x = 0
    for b in skal:
        aus.paste(b, (x, 0), b)
        x += b.width + lueck
    return aus


# ---------------------------------------------------------------- Motive

def motiv_farben(breite, hoehe):
    """Sechs Flaschen auf Markengrund. Text unten, Flaschen darueber."""
    kopf = ["Sechs Farben.", "Eine Flasche."]
    b = Image.new("RGB", (breite, hoehe), GRUND)
    d = ImageDraw.Draw(b)
    rand = int(breite * 0.085)

    feld = block_hoehe(breite, kopf) + int(breite * 0.10)
    bereich = hoehe - feld
    r = reihe(int(bereich * 0.86))
    if r.width > breite - rand * 2:
        neu_b = breite - rand * 2
        r = r.resize((neu_b, max(1, int(r.height * neu_b / r.width))), Image.LANCZOS)
    b.paste(r, ((breite - r.width) // 2, (bereich - r.height) // 2), r)

    textblock(d, b, rand, hoehe - feld, breite, kopf,
              "550 ml · Gratisversand Schweiz")
    return b


def motiv_napf(breite, hoehe):
    """Der Napf von nahem. Bild oben, Textfeld unten.

    Der Zuschnitt ist oben verankert: bei 1:1 und 4:5 schnitt die Mitte
    den Napf weg, und genau der Napf ist das Motiv. Einpassen statt
    beschneiden war der erste Versuch - das Foto hat aber einen Verlauf
    zum Rand hin, sodass die eingepasste Flaeche als sichtbarer Kasten
    im Bild stand.
    """
    kopf = ["Der Napf ist", "schon dran."]
    quelle = Image.open(os.path.join(THEME, "a-napf-nah.webp")).convert("RGB")
    b = Image.new("RGB", (breite, hoehe), GRUND)
    d = ImageDraw.Draw(b)
    rand = int(breite * 0.085)
    luft = int(breite * 0.055)

    if hoehe <= breite * 1.1:
        # QUADRAT: geteilt statt gestapelt. Das Foto ist hochkant; ueber
        # die volle Breite gestapelt blieb im Quadrat nur noch der Napf
        # ohne Flasche stehen - ein Ausschnitt, den man ohne Vorwissen
        # nicht mehr zuordnet. Senkrecht geteilt behaelt das Foto die
        # ganze Hoehe und damit die ganze Flasche.
        f_br = int(breite * 0.52)
        b.paste(fuellen(quelle, f_br, hoehe, anker=0.3), (0, 0))
        t_br = breite - f_br
        skala = int(breite * 0.66)
        x = f_br + int(t_br * 0.10)
        y = (hoehe - block_hoehe(t_br, kopf, skala)) // 2
        textblock(d, b, x, y, t_br - int(t_br * 0.16), kopf,
                  "550 ml · sechs Farben", skala=skala)
        return b

    feld = block_hoehe(breite, kopf) + luft * 2
    b.paste(fuellen(quelle, breite, hoehe - feld, anker=0.12), (0, 0))
    d.rectangle([0, hoehe - feld, breite, hoehe], fill=GRUND)
    textblock(d, b, rand, hoehe - feld + luft, breite, kopf,
              "550 ml · sechs Farben")
    return b


def motiv_bank(breite, hoehe):
    """Die Bank. Vollflaechig, Textblock im unteren Drittel auf Band."""
    kopf = ["Wasser dabei,", "Napf inklusive."]
    # Bei 1:1 wird das hochkant aufgenommene Foto stark in der Hoehe
    # beschnitten. Mittig verankert rutschte die Flasche unter die
    # Textflaeche; der hoehere Anker haelt sie frei.
    b = fuellen(Image.open(os.path.join(THEME, "a-film-napf-start.webp")).convert("RGB"),
                breite, hoehe, anker=0.62 if hoehe <= breite * 1.1 else 0.5)
    d = ImageDraw.Draw(b)
    rand = int(breite * 0.085)
    luft = int(breite * 0.050)

    band_h = block_hoehe(breite, kopf) + luft * 2
    # Bei 9:16 haelt sich das Band aus den Randzonen heraus, die Stories
    # mit Fortschrittsbalken und Absender ueberdecken; sonst sitzt es
    # buendig unten.
    band_y = int(hoehe * 0.60) if hoehe / breite > 1.6 else hoehe - band_h
    band_y = min(band_y, hoehe - band_h)

    d.rectangle([0, band_y, breite, band_y + band_h], fill=GRUND)
    textblock(d, b, rand, band_y + luft, breite, kopf,
              "550 ml · sechs Farben · Gratisversand Schweiz")
    return b


MOTIVE = {"1-farben": motiv_farben, "2-napf": motiv_napf, "3-bank": motiv_bank}


def main():
    os.makedirs(ZIEL, exist_ok=True)
    for m_name, bauer in MOTIVE.items():
        for f_name, (br, ho) in FORMATE.items():
            p = os.path.join(ZIEL, "%s-%s.jpg" % (m_name, f_name))
            bauer(br, ho).save(p, quality=90, optimize=True)
            print("%-22s %4dx%-5d %5d KB" % (os.path.basename(p), br, ho,
                                             os.path.getsize(p) // 1024))


if __name__ == "__main__":
    main()
