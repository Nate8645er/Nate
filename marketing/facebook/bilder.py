#!/usr/bin/env python3
"""Profilbild und Titelbild fuer die Facebook-Seite.

BEIDE AUS DEM SHOP, NICHT NEU ERFUNDEN. Das Zeichen ist derselbe
Wassertropfen wie im Kopf des Shops und im Browser-Symbol (der Pfad
steht in layout/theme.liquid). Die Schrift ist Outfit Bold - dieselbe
Datei, die der Shop ausliefert; ich habe sie vom eigenen CDN geholt
und aus woff2 zurueckgerechnet. Die Farben sind die Marken-Token aus
n-nova.css: #111111 auf #F5F4F1. Wer von der Anzeige auf die Seite
kommt und von dort in den Shop, sieht dreimal dasselbe.

PROFILBILD
Facebook schneidet es zu einem KREIS. Deshalb liegt der Tropfen weit
innen und der Grund ist randlos schwarz - so bleibt am Rand nichts
haengen, was abgeschnitten wirkt.

TITELBILD
Facebook zeigt es am Rechner in 820 x 312, laedt aber am besten
1640 x 856. Am Handy wird es MITTIG UND SCHMALER beschnitten. Alles,
was gelesen werden muss, sitzt deshalb im mittleren Drittel; die
Flasche rechts darf wegfallen, ohne dass etwas fehlt.

WAS DRAUFSTEHT: nur was auch im Shop steht. 550 ml, sechs Farben,
Gratisversand Schweiz. Keine Bewertung, keine Zahl, kein Versprechen
zur Dichtigkeit.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ZIEL = "/tmp/claude-0/-home-user-Nate/2d96a9a6-93ca-5da3-99c5-55dbdd35f6e9/scratchpad/fbseite"
SCHRIFT = "/tmp/a-sans-bold.ttf"
FLASCHE = "/tmp/flasche.webp"

TEXT = "#111111"
GRUND = "#F5F4F1"
SANFT = "#6E6E73"


def tropfen(groesse, farbe):
    """Der Wassertropfen aus dem Shop, als Bild in der gewuenschten Groesse.

    Der Pfad im Theme ist eine Bezier-Kurve auf 24 x 24. Hier wird sie
    aus Polygonpunkten nachgezogen - das reicht bei dieser Groesse und
    spart eine SVG-Bibliothek, die es hier nicht gibt.
    """
    ue = 8                                   # ueberabtasten, dann verkleinern
    n = groesse * ue
    b = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)

    # Kreis unten (der Bauch) und Dreieck oben (die Spitze), zusammen
    # ergeben sie die Tropfenform des Originals.
    r = n * 0.242                            # 5.8 von 24
    mx, my = n / 2, n * 0.575                # Mittelpunkt 13.8 von 24
    d.ellipse([mx - r, my - r, mx + r, my + r], fill=farbe)
    d.polygon([(mx, n * 0.133),              # Spitze bei 3.2 von 24
               (mx - r * 0.995, my + r * 0.10),
               (mx + r * 0.995, my + r * 0.10)], fill=farbe)
    return b.resize((groesse, groesse), Image.LANCZOS)


def profilbild(pfad, kante=1024):
    b = Image.new("RGB", (kante, kante), TEXT)
    t = tropfen(int(kante * 0.46), "#FFFFFF")
    b.paste(t, ((kante - t.width) // 2, (kante - t.height) // 2), t)
    b.save(pfad, quality=95)
    return b.size


def titelbild(pfad, breite=1640, hoehe=856):
    b = Image.new("RGB", (breite, hoehe), GRUND)
    d = ImageDraw.Draw(b)

    # Die Flasche rechts. GANZ, nicht angeschnitten: sie lief vorher
    # unten aus dem Bild, was nach Versehen aussah statt nach Absicht.
    # Sie ist Dekor - am Handy faellt sie ohnehin weg.
    fl = Image.open(FLASCHE).convert("RGBA")
    fl = fl.crop(fl.getbbox())
    h_neu = int(hoehe * 0.82)
    fl = fl.resize((max(1, int(fl.width * h_neu / fl.height)), h_neu),
                   Image.LANCZOS)
    b.paste(fl, (int(breite * 0.795), (hoehe - h_neu) // 2), fl)

    # Alles Lesbare in die Mitte: am Handy bleibt nur der mittlere Teil.
    mitte_x = int(breite * 0.375)

    f_gross = ImageFont.truetype(SCHRIFT, 104)
    f_mittel = ImageFont.truetype(SCHRIFT, 46)
    f_klein = ImageFont.truetype(SCHRIFT, 34)

    tr = tropfen(96, TEXT)
    y = int(hoehe * 0.285)
    b.paste(tr, (mitte_x - tr.width - 26, y - 8), tr)
    d.text((mitte_x, y), "Let'sDrink", font=f_gross, fill=TEXT)

    y += 150
    d.text((mitte_x - tr.width - 26, y), "Trinkflasche mit Napf.",
           font=f_mittel, fill=TEXT)

    y += 82
    d.line([(mitte_x - tr.width - 26, y), (mitte_x + 470, y)],
           fill="#D8D5CE", width=2)

    y += 34
    d.text((mitte_x - tr.width - 26, y),
           "550 ml · sechs Farben · Gratisversand Schweiz",
           font=f_klein, fill=SANFT)

    b.save(pfad, quality=92)
    return b.size


os.makedirs(ZIEL, exist_ok=True)
p = os.path.join(ZIEL, "fb-profilbild.jpg")
t = os.path.join(ZIEL, "fb-titelbild.jpg")
print("Profilbild", profilbild(p), os.path.getsize(p) // 1024, "KB")
print("Titelbild ", titelbild(t), os.path.getsize(t) // 1024, "KB")

# Vorschau: so sieht das Profilbild im Kreis aus, und so das Titelbild
# in dem Ausschnitt, den ein Handy zeigt.
pb = Image.open(p).resize((260, 260), Image.LANCZOS)
maske = Image.new("L", (260, 260), 0)
ImageDraw.Draw(maske).ellipse([0, 0, 259, 259], fill=255)
kreis = Image.new("RGB", (260, 260), (255, 255, 255))
kreis.paste(pb, (0, 0), maske)

tb = Image.open(t)
handy = tb.crop((int(tb.width * 0.20), 0, int(tb.width * 0.80), tb.height))
handy = handy.resize((640, int(640 * handy.height / handy.width)), Image.LANCZOS)

blatt = Image.new("RGB", (940, max(300, handy.height + 40)), (255, 255, 255))
blatt.paste(kreis, (20, 20))
blatt.paste(handy, (300, 20))
blatt.save(os.path.join(ZIEL, "_vorschau.png"))
print("Vorschau geschrieben")
