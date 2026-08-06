#!/usr/bin/env python3
"""Werbebilder fuer Let'sDrink.

Gebaut aus den echten Produktfreistellern, nicht aus erzeugten Bildern.
Das ist keine Notloesung: ein Kunde, der eine erfundene Flasche anklickt
und eine andere geliefert bekommt, schreibt eine Rueckgabe statt einer
Empfehlung.

DREI FORMATE, weil die Plattformen drei brauchen:
  1080 x 1350  Beitrag, Hochformat 4:5 - nimmt im Verlauf am meisten Platz
  1080 x 1920  Kurzgeschichte 9:16 - oben und unten je rund 250 px
               Schutzzone, dort liegen Bedienelemente der App ueber dem Bild
  1080 x 1080  Quadrat - Katalog, Vorschaubild, Werbeanzeige

WARUM DIE PRODUKTMOTIVE DUNKEL SIND, DER SHOP ABER HELL
Der Flaschenkoerper ist weiss-durchscheinend. Auf dem hellen Grund des
Shops (#E8EEEB) verschwindet er zu einem weissen Klotz - erste Fassung
gebaut, angesehen, verworfen. Dasselbe Problem loest das Farbsystem des
Shops seit jeher mit einer Umkehrung: die WEISSE Flasche bekommt dort
einen DUNKLEN Grund. Hier gilt dieselbe Regel fuer alle sechs, weil der
Koerper immer weiss ist. Das Motiv, das keine Flasche zeigt (04), bleibt
hell - so hat der Verlauf beide Seiten der Marke.

WELCHE FARBE AUF WELCHEN GRUND
  dunkler Grund: tuerkis, gruen, rosa, weiss, grau - alle heben sich ab
  dunkler Grund: NIEMALS schwarz, die Kappe verschwindet
  heller Grund:  schwarz, grau - NIEMALS weiss

ROTE LINIEN (aus ENTWURF-A, gelten auch fuer Werbung):
  kein erfundener Beweis, keine Sterne, keine Verkaufszahlen
  keine Dringlichkeit, kein Countdown, keine Verknappung
  keine Produktangabe ausser 550 ml und sechs Farben
  die Flasche nie auf dem Kopf, Kippen hoechstens 20 Grad
  nie das Zeichen scharfes s
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HIER = os.path.dirname(os.path.abspath(__file__))
FREI = HIER + "/frei-sauber"
SCHRIFT = HIER + "/schriften"
AUS = HIER + "/bilder"

HELL = (232, 238, 235)
DUNKEL = (18, 33, 31)
TEXT_HELL = (11, 26, 24)
TEXT_DUNKEL = (244, 248, 246)
AKZENT = (22, 110, 118)
AKZENT_HELL = (93, 225, 220)

FARBEN = ["tuerkis", "gruen", "rosa", "grau", "schwarz", "weiss"]

# Breite, Hoehe, Schutzzone oben, Schutzzone unten
FORMATE = {
    "beitrag": (1080, 1350, 90, 90),
    "geschichte": (1080, 1920, 260, 260),
    "quadrat": (1080, 1080, 80, 80),
}


def schrift(datei, groesse, wght=None, opsz=None):
    f = ImageFont.truetype(SCHRIFT + "/" + datei, groesse)
    achsen = []
    if opsz is not None:
        achsen.append(opsz)
    if wght is not None:
        achsen.append(wght)
    if achsen:
        try:
            f.set_variation_by_axes(achsen)
        except Exception:
            pass
    return f


def titel(g, w=700):
    return schrift("v4-fraunces-latin.ttf", g, wght=w, opsz=min(144, max(9, g)))


def satz(g, w=400):
    return schrift("v4-ibmplexsans-latin.ttf", g, wght=w)


def flasche(name, hoehe):
    im = Image.open(FREI + "/" + name + ".png").convert("RGBA")
    b = max(1, int(round(im.width * hoehe / im.height)))
    return im.resize((b, hoehe), Image.LANCZOS)


def mit_schatten(grund, bild, x, y, dunkel=True):
    """Ein einziger Schatten, der die Silhouette freistellt. Auf dunklem
    Grund traegt er nichts - dort uebernimmt eine schwache Aufhellung
    unter der Flasche, damit sie steht statt zu schweben."""
    if dunkel:
        w, h = bild.width, int(bild.height * 0.10)
        sockel = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sockel).ellipse((0, 0, w, h), fill=(120, 190, 190, 55))
        sockel = sockel.filter(ImageFilter.GaussianBlur(22))
        grund.alpha_composite(sockel, (x, y + bild.height - h // 2))
    else:
        s = Image.new("RGBA", bild.size, (0, 0, 0, 0))
        s.paste((11, 26, 24, 85), (0, 0), bild)
        s = s.filter(ImageFilter.GaussianBlur(16))
        grund.alpha_composite(s, (x + 4, y + 14))
    grund.alpha_composite(bild, (x, y))


def umbruch(d, text, font, breite):
    zeilen, jetzt = [], ""
    for wort in text.split():
        probe = (jetzt + " " + wort).strip()
        if d.textlength(probe, font=font) <= breite or not jetzt:
            jetzt = probe
        else:
            zeilen.append(jetzt)
            jetzt = wort
    if jetzt:
        zeilen.append(jetzt)
    return zeilen


def block(d, x, y, text, font, farbe, breite, zeilenhoehe):
    for z in umbruch(d, text, font, breite):
        d.text((x, y), z, font=font, fill=farbe)
        y += zeilenhoehe
    return y


def marke(d, x, y, farbe, akzent, groesse=34):
    f = titel(groesse, 700)
    d.text((x, y), "Let'sDrink", font=f, fill=farbe)
    d.text((x + d.textlength("Let'sDrink", font=f), y), ".",
           font=f, fill=akzent)
    return groesse * 1.5


def leinwand(fmt, dunkel):
    B, H, ro, ru = FORMATE[fmt]
    im = Image.new("RGBA", (B, H), (DUNKEL if dunkel else HELL) + (255,))
    return im, ImageDraw.Draw(im), B, H, ro, ru


# ---------------------------------------------------------------- Motive

def nebeneinander(fmt):
    """Im Quadrat bleibt unter dem Text kaum Hoehe uebrig - die Flasche
    wuerde auf ein Drittel der Groesse schrumpfen, die sie im Hochformat
    hat. Ist das Bild breiter als hoch mal 1.2, stellt sich die Flasche
    deshalb NEBEN den Text statt darunter. Entschieden wird am
    Seitenverhaeltnis, nicht am Formatnamen."""
    B, H, ro, ru = FORMATE[fmt]
    return H < B * 1.2


def motiv_knopf(fmt):
    """01 - Was das Ding tut. Eine Flasche, eine Aussage."""
    im, d, B, H, ro, ru = leinwand(fmt, True)
    rand = 88
    t, g = TEXT_DUNKEL, (168, 186, 183)
    quer = nebeneinander(fmt)
    spalte = int(B * 0.56) - rand if quer else B - 2 * rand

    y = ro
    y += marke(d, rand, y, t, AKZENT_HELL) + 20

    ft = titel(int(B * (0.098 if quer else 0.125)), 800)
    y = block(d, rand, y, "Ein Knopf.", ft, t, spalte, ft.size * 1.02)
    y = block(d, rand, y, "Ein Napf.", ft, t, spalte, ft.size * 1.02)
    y += 18

    fs = satz(int(B * 0.036))
    y = block(d, rand, y, "Drücken, der Napf füllt sich. Aufrichten, "
              "das Übrige läuft zurück.", fs, g, spalte - 30, fs.size * 1.5)

    fk = satz(int(B * 0.031), 500)
    fussy = H - ru - fk.size * 1.4
    if quer:
        fl = flasche("tuerkis", int(fussy - ro - 40))
        mit_schatten(im, fl, int(B * 0.60) + (int(B * 0.40) - rand - fl.width) // 2,
                     int(ro + 20))
    else:
        fl = flasche("tuerkis", int(max(360, fussy - y - 70)))
        mit_schatten(im, fl, (B - fl.width) // 2, int(y) + 40)
    d.text((rand, fussy), "550 ml · sechs Farben · CHF 39.90", font=fk, fill=t)
    return im


def motiv_farben(fmt):
    """02 - Der einzige echte Unterschied zu jeder anderen Flasche."""
    im, d, B, H, ro, ru = leinwand(fmt, True)
    rand = 88
    t, g = TEXT_DUNKEL, (168, 186, 183)

    y = ro
    y += marke(d, rand, y, t, AKZENT_HELL) + 20

    ft = titel(int(B * 0.108), 800)
    y = block(d, rand, y, "Sechs Farben.", ft, t, B - 2 * rand, ft.size * 1.02)
    y = block(d, rand, y, "Eine Flasche.", ft, t, B - 2 * rand, ft.size * 1.02)
    y += 24

    fk = satz(int(B * 0.031), 500)
    fussy = H - ru - fk.size * 1.4

    # Die Hoehe der Flaschen ergibt sich aus der Breite, damit nichts
    # ueber den Rand laeuft. Der gesaeuberte Freisteller ist 329 x 1116.
    #
    # Sechs nebeneinander passen in jedes Format - aber im Hochformat
    # 9:16 waeren sie dann winzig und die untere Haelfte bliebe leer.
    # Reicht die Hoehe fuer zwei Reihen zu dritt, wird umgebrochen: die
    # Flaschen werden dadurch fast doppelt so gross. Entschieden wird
    # nach dem vorhandenen Platz, nicht nach dem Formatnamen - so
    # stimmt es auch, wenn jemand spaeter ein Format ergaenzt.
    aussen, luft = 52, 8
    platz = fussy - y - 60

    def reihe_hoehe(je_reihe):
        breite_je = (B - 2 * aussen - (je_reihe - 1) * luft) / je_reihe
        return int(breite_je * 1116 / 329)

    h1 = reihe_hoehe(6)
    h2 = reihe_hoehe(3)
    if platz >= 2 * h2 + 40:
        reihen, hoehe = [FARBEN[:3], FARBEN[3:]], h2
    else:
        reihen, hoehe = [FARBEN], min(h1, int(platz))

    gesamthoehe = len(reihen) * hoehe + (len(reihen) - 1) * 40
    oben = int(y + (platz - gesamthoehe) / 2)
    for r in reihen:
        bilder = [flasche(f, hoehe) for f in r]
        x = (B - (sum(b.width for b in bilder) + (len(r) - 1) * luft)) / 2
        for b in bilder:
            mit_schatten(im, b, int(x), oben)
            x += b.width + luft
        oben += hoehe + 40

    d.text((rand, fussy), "Jede 550 ml · jede CHF 39.90", font=fk, fill=t)
    return im


def motiv_preis(fmt):
    """03 - Preis und Bedingungen, ohne Dringlichkeit."""
    im, d, B, H, ro, ru = leinwand(fmt, True)
    rand = 88
    t, g = TEXT_DUNKEL, (168, 186, 183)
    quer = nebeneinander(fmt)
    spalte = int(B * 0.58) - rand if quer else B - 2 * rand

    y = ro
    y += marke(d, rand, y, t, AKZENT_HELL) + 24

    # Der Preis ist das groesste Wort im Bild und darf trotzdem nie in
    # die Flasche laufen. Statt eine Groesse zu raten, wird sie so lange
    # verkleinert, bis sie in die Textspalte passt. Der Preis kommt aus
    # dem Shop und kann sich aendern - eine feste Groesse waere eine
    # Falle fuer den naechsten, der ihn anpasst.
    groesse = int(B * (0.125 if quer else 0.165))
    while groesse > 40:
        fp = titel(groesse, 800)
        if d.textlength("CHF 39.90", font=fp) <= spalte:
            break
        groesse -= 4
    d.text((rand, y), "CHF 39.90", font=fp, fill=t)
    y += fp.size * 1.06

    fs = satz(int(B * 0.035))
    y = block(d, rand, y, "Trinkflasche mit fest angebautem Napf, 550 ml.",
              fs, g, spalte - 30, fs.size * 1.5)
    y += 20

    fz = satz(int(B * 0.030), 500)
    for zeile in ["Gratisversand in der Schweiz",
                  "Lieferung in 7 bis 14 Werktagen",
                  "14 Tage Rückgabe, ohne Begründung"]:
        r = fz.size * 0.22
        m = y + fz.size * 0.58
        d.ellipse((rand + 2, m - r, rand + 2 + 2 * r, m + r), fill=AKZENT_HELL)
        d.text((rand + int(4 * r) + 12, y), zeile, font=fz, fill=t)
        y += fz.size * 1.7

    if quer:
        fl = flasche("tuerkis", int(H - ro - ru - 40))
        mit_schatten(im, fl, int(B * 0.62) + (int(B * 0.38) - rand - fl.width) // 2,
                     int(ro + 20))
    else:
        fl = flasche("tuerkis", int(max(340, H - ru - y - 60)))
        mit_schatten(im, fl, B - fl.width - rand, int(y) + 30)
    return im


def motiv_ehrlich(fmt):
    """04 - Der Grund, hier zu kaufen statt anderswo. Kein Bild-Motiv,
    ein Satz-Motiv: die Ehrlichkeit ist das Versprechen. Hell, damit der
    Verlauf beide Seiten der Marke zeigt."""
    im, d, B, H, ro, ru = leinwand(fmt, False)
    rand = 88
    t, g = TEXT_HELL, (86, 98, 96)

    y = ro
    y += marke(d, rand, y, t, AKZENT) + 30

    ft = titel(int(B * 0.082), 700)
    y = block(d, rand, y, "Ich schreibe hin, was ich weiss – und was nicht.",
              ft, t, B - 2 * rand, ft.size * 1.2)
    y += 26

    fs = satz(int(B * 0.034))
    y = block(d, rand, y,
              "Kein Lager, kein Callcenter. Ein Betrieb in Rapperswil-Jona. "
              "Wenn du schreibst, antwortet dir auch wirklich ich.",
              fs, g, B - 2 * rand - 20, fs.size * 1.55)

    d.line((rand, y + 36, rand + 110, y + 36), fill=AKZENT, width=3)
    fn = satz(int(B * 0.030), 500)
    d.text((rand, y + 62), "Nate · Let'sDrink", font=fn, fill=t)
    unten = y + 62 + fn.size * 1.6

    platz = int(H - ru - unten - 30)
    if platz > 300:
        fl = flasche("schwarz", platz)
        mit_schatten(im, fl, B - fl.width - rand, int(unten) + 20, dunkel=False)
    return im


MOTIVE = {
    "01-knopf": motiv_knopf,
    "02-farben": motiv_farben,
    "03-preis": motiv_preis,
    "04-ehrlich": motiv_ehrlich,
}


def main():
    os.makedirs(AUS, exist_ok=True)
    for mname, fn in MOTIVE.items():
        for fmt in FORMATE:
            im = fn(fmt)
            p = f"{AUS}/{mname}_{fmt}.jpg"
            im.convert("RGB").save(p, quality=92, subsampling=0)
            print(p.split("/")[-1], im.size)


main()
