#!/usr/bin/env python3
"""
folien.py - Bilder fuer das Erklaervideo zum Agenten-Plugin.

Nate hat gefragt: Was brauchen wir fuer das neue Plugin, wie funktioniert
es, welche benutzen wir wofuer und wie helfen sie? Er ist Anfaenger. Also
gilt dieselbe Regel wie beim Curbcut-Video:

  - Ein Gedanke pro Folie.
  - Kein Fachbegriff, den er nicht kennt. Kein "Agent-Orchestrierung".
    Ein Agent ist ein Helfer mit einem Beruf.
  - Nichts behaupten, was nicht stimmt. Ein Helfer, der Texte schreibt,
    verkauft nicht von selbst.

Die Layout-Funktionen sind dieselben wie beim Curbcut-Video, damit beide
Videos wie aus einem Haus aussehen. Farben aber anders - hier Tinte auf
Papier mit einem ruhigen Blau, nicht das Sicherheitsgelb von Curbcut.
"""

import os
from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
BREIT, HOCH = 1080, 1350
RAND = 96

# Ruhiges Arbeitsblau auf warmem Papier - ein Werkzeugkasten, kein Alarm.
GRUND = (238, 236, 231)
TINTE = (24, 26, 30)
MATT = (92, 96, 104)
MARK = (36, 92, 158)          # Arbeitsblau
GOLD = (183, 130, 30)
FREI = (37, 96, 57)
FLAECHE = (250, 249, 246)
LINIE = (206, 204, 196)

S = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def f(p, g):
    return ImageFont.truetype(p, g)


def breite(d, t, s):
    k = d.textbbox((0, 0), t, font=s)
    return k[2] - k[0]


def mitte(d, t, s, y, farbe=TINTE):
    d.text(((BREIT - breite(d, t, s)) // 2, y), t, font=s, fill=farbe)


def passend(d, text, pfad, wunsch, max_breite, klein=40):
    g = wunsch
    while g > klein:
        s = f(pfad, g)
        if breite(d, text, s) <= max_breite:
            return s
        g -= 4
    return f(pfad, klein)


def hoehe_fuer(d, text, s, max_breite, zh):
    worte, zeilen, jetzt = text.split(), 0, ""
    for w in worte:
        probe = (jetzt + " " + w).strip()
        if breite(d, probe, s) > max_breite and jetzt:
            zeilen += 1
            jetzt = w
        else:
            jetzt = probe
    return (zeilen + (1 if jetzt else 0)) * zh


def umbruch(d, text, s, x, y, max_breite, zh, farbe=TINTE, zentriert=False):
    worte, zeilen, jetzt = text.split(), [], ""
    for w in worte:
        probe = (jetzt + " " + w).strip()
        if breite(d, probe, s) > max_breite and jetzt:
            zeilen.append(jetzt)
            jetzt = w
        else:
            jetzt = probe
    if jetzt:
        zeilen.append(jetzt)
    for i, z in enumerate(zeilen):
        zx = (BREIT - breite(d, z, s)) // 2 if zentriert else x
        d.text((zx, y + i * zh), z, font=s, fill=farbe)
    return y + len(zeilen) * zh


def grundplatte():
    b = Image.new("RGB", (BREIT, HOCH), GRUND)
    d = ImageDraw.Draw(b)
    for i in range(3):
        deck = (MARK, (120, 156, 196), (176, 196, 220))[i]
        d.rectangle([RAND + i * 18, 70, RAND + i * 18 + 10, 114], fill=deck)
    d.text((RAND + 74, 79), "DEINE HELFER", font=f(M, 24), fill=MATT)
    return b, d


def folie_titel(ober, gross, unter, farbe=TINTE):
    b, d = grundplatte()
    y = 300
    if ober:
        mitte(d, ober.upper(), f(M, 30), y, MARK)
        y += 76
    y = umbruch(d, gross, f(SB, 88), RAND, y, BREIT - 2 * RAND, 104, farbe, True)
    if unter:
        y += 44
        umbruch(d, unter, f(S, 40), RAND, y, BREIT - 2 * RAND - 60, 58, MATT, True)
    return b


def folie_zahl(ober, zahl, unter, farbe=MARK):
    b, d = grundplatte()
    mitte(d, ober.upper(), f(M, 30), 270, MARK)
    s = passend(d, zahl, SB, 220, BREIT - 2 * RAND)
    k = d.textbbox((0, 0), zahl, font=s)
    mitte(d, zahl, s, 430 - (k[3] - k[1]) // 2, farbe)
    umbruch(d, unter, f(S, 42), RAND, 700, BREIT - 2 * RAND - 40, 60, TINTE, True)
    return b


def folie_liste(ober, titel, punkte, marke=MARK):
    b, d = grundplatte()
    mitte(d, ober.upper(), f(M, 30), 220, MARK)
    y = umbruch(d, titel, f(SB, 64), RAND, 292, BREIT - 2 * RAND, 80, TINTE, True)
    y += 60
    innen = BREIT - 2 * RAND - 130
    klein = f(S, 32)
    for i, (kopf, text) in enumerate(punkte, 1):
        th = hoehe_fuer(d, text, klein, innen, 40)
        h = 82 + th + 22
        d.rounded_rectangle([RAND, y, BREIT - RAND, y + h], 6,
                            fill=FLAECHE, outline=LINIE, width=2)
        d.rectangle([RAND, y, RAND + 7, y + h], fill=marke)
        d.text((RAND + 40, y + 26), f"{i}", font=f(M, 34), fill=marke)
        d.text((RAND + 86, y + 24), kopf, font=f(SB, 38), fill=TINTE)
        umbruch(d, text, klein, RAND + 86, y + 80, innen, 40, MATT)
        y += h + 22
    return b


FOLIEN = [
    ("01", lambda: folie_titel("Das neue Plugin",
        "Du hast jetzt ein Team von Helfern.",
        "Ich zeige dir, was sie sind und wie du sie einsetzt.")),

    ("02", lambda: folie_titel("Was ist ein Agent",
        "Ein Agent ist ein Helfer mit einem Beruf.",
        "Der eine kann SEO, der andere schreibt Texte, der dritte "
        "beantwortet Kundenfragen. Du sagst nur, was du brauchst.")),

    ("03", lambda: folie_zahl("Was installiert wurde", "17",
        "Helfer sind fuer deinen Shop aktiv. Weitere 74 warten im "
        "Katalog, falls du sie je brauchst.")),

    ("04", lambda: folie_liste("Dein SEO-Team", "Damit dich Google findet", [
        ("Keyword-Helfer", "Findet die Woerter, nach denen Leute suchen."),
        ("Text-Helfer", "Schreibt die Produktseite so, dass Google sie mag."),
        ("Meta-Helfer", "Macht den Titel, der in den Suchergebnissen steht."),
    ])),

    ("05", lambda: folie_liste("Dein Verkaufs-Team", "Damit aus Besuchern Kunden werden", [
        ("Sales-Helfer", "Schreibt Nachfass-Mails und Angebotstexte."),
        ("Support-Helfer", "Beantwortet Kundenfragen freundlich und schnell."),
        ("Inhalt-Helfer", "Plant, was du wann posten koenntest."),
    ])),

    ("06", lambda: folie_liste("Dein Denk-Team", "Damit du klarer entscheidest", [
        ("Startup-Helfer", "Rechnet Markt, Preis und Zahlen durch."),
        ("Analyse-Helfer", "Macht aus deinen Zahlen eine klare Aussage."),
        ("Recherche-Helfer", "Sucht und prueft, was die Konkurrenz macht."),
    ])),

    ("07", lambda: folie_titel("So benutzt du sie",
        "Du tippst einfach, was du willst.",
        "Zum Beispiel: Nutz den SEO-Keyword-Helfer und finde die besten "
        "Suchbegriffe fuer die Trinkflasche. Mehr nicht.")),

    ("08", lambda: folie_titel("Ehrlich",
        "Ein Helfer schreibt. Verkaufen tut er nicht.",
        "Die Helfer machen die Arbeit schneller. Aber der Umsatz haengt "
        "zuerst an einer Sache: dass die Werbung die richtigen Leute holt.")),

    ("09", lambda: folie_titel("Das Wichtigste zuerst",
        "Erst der Pixel. Dann die Helfer.",
        "Sobald die Werbung meldet, wer kauft, machen dich die SEO- und "
        "Text-Helfer richtig gross. Vorher arbeiten sie ins Leere.")),
]


def bauen():
    ziel = os.path.join(HIER, "bilder")
    os.makedirs(ziel, exist_ok=True)
    for name, mach in FOLIEN:
        mach().save(os.path.join(ziel, f"{name}.png"))
        print(f"  {name}.png")


if __name__ == "__main__":
    bauen()
