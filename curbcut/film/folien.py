#!/usr/bin/env python3
"""
folien.py - baut die Bilder fuer das Erklaervideo.

Nate hat gefragt, worum es bei diesem Geschaeft ueberhaupt geht. Das
war ein Befund ueber meine Erklaerung, nicht ueber ihn: Ich hatte ein
Geschaeft gebaut, das ich verstehe und er nicht.

Darum diese Regeln fuer jede Folie:
  - Hoechstens ein Gedanke. Wer zwei Sachen gleichzeitig sagt, sagt keine.
  - Die Zahl gross, der Satz klein. Zahlen bleiben haengen, Saetze nicht.
  - Keine Fachbegriffe. Kein WCAG, kein Quelltext, kein Overlay.
  - Nichts, was nicht gemessen wurde.

Format 1080 mal 1350. Das laeuft am Handy und am Rechner, ohne dass
die Schrift auf einem von beiden zu klein wird.
"""

import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
BREIT, HOCH = 1080, 1350
RAND = 96

# Dieselben Farben wie Bericht und Website. Beton und Sicherheitsgelb.
GRUND = (233, 234, 229)
TINTE = (22, 25, 28)
MATT = (88, 94, 99)
MARK = (200, 147, 10)
SPERR = (168, 30, 22)
FREI = (37, 96, 57)
FLAECHE = (248, 248, 245)
LINIE = (198, 200, 190)

S = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def f(pfad, groesse):
    return ImageFont.truetype(pfad, groesse)


def breite(d, text, schrift):
    k = d.textbbox((0, 0), text, font=schrift)
    return k[2] - k[0]


def mitte(d, text, schrift, y, farbe=TINTE):
    d.text(((BREIT - breite(d, text, schrift)) // 2, y), text,
           font=schrift, fill=farbe)


def passend(d, text, pfad, wunsch, max_breite, kleinstens=40):
    """Die groesste Schrift, mit der der Text noch hineinpasst.

    Ohne das laeuft die Zahl aus dem Bild. Beim ersten Bau stand auf
    Folie 3 "100'000" bei Schriftgrad 240 - das sind sieben Zeichen mal
    rund 150 Pixel, also gut 1050 von 888 verfuegbaren. Auf Folie 4 war
    "17 von 18" an beiden Seiten abgeschnitten und las sich als
    ".7 von 18".

    Ein fester Schriftgrad geht bei kurzen Zeilen gut und bei langen
    nicht, und man sieht es erst, wenn das Bild fertig ist. Darum wird
    hier gemessen statt gesetzt.
    """
    groesse = wunsch
    while groesse > kleinstens:
        s = f(pfad, groesse)
        if breite(d, text, s) <= max_breite:
            return s
        groesse -= 4
    return f(pfad, kleinstens)


def hoehe_fuer(d, text, schrift, max_breite, zeilenhoehe):
    """Wie hoch wird der Text nach dem Umbruch? Vor dem Zeichnen wissen."""
    worte, zeilen, jetzt = text.split(), 0, ""
    for w in worte:
        probe = (jetzt + " " + w).strip()
        if breite(d, probe, schrift) > max_breite and jetzt:
            zeilen += 1
            jetzt = w
        else:
            jetzt = probe
    return (zeilen + (1 if jetzt else 0)) * zeilenhoehe


def umbruch(d, text, schrift, x, y, max_breite, zeilenhoehe, farbe=TINTE,
            zentriert=False):
    """Bricht auf Wortgrenzen um. Zeichenzahl schaetzen reicht nicht -
    bei einer Proportionalschrift ist ein W dreimal so breit wie ein i."""
    worte, zeilen, jetzt = text.split(), [], ""
    for w in worte:
        probe = (jetzt + " " + w).strip()
        if breite(d, probe, schrift) > max_breite and jetzt:
            zeilen.append(jetzt)
            jetzt = w
        else:
            jetzt = probe
    if jetzt:
        zeilen.append(jetzt)
    for i, z in enumerate(zeilen):
        zx = (BREIT - breite(d, z, schrift)) // 2 if zentriert else x
        d.text((zx, y + i * zeilenhoehe), z, font=schrift, fill=farbe)
    return y + len(zeilen) * zeilenhoehe


def rippen(d, x, y, farbe=MARK):
    """Das Zeichen: drei Rippen wie ein taktiles Leitsystem."""
    for i, deckung in enumerate((255, 158, 87)):
        d.rectangle([x + i * 16, y, x + i * 16 + 9, y + 44],
                    fill=farbe + (deckung,) if len(farbe) == 3 else farbe)


def grundplatte():
    b = Image.new("RGB", (BREIT, HOCH), GRUND)
    d = ImageDraw.Draw(b)
    # Leitspur oben - dieselbe Struktur wie im Bericht
    for i in range(3):
        deck = (MARK, (214, 178, 84), (226, 205, 150))[i]
        d.rectangle([RAND + i * 18, 70, RAND + i * 18 + 10, 114], fill=deck)
    d.text((RAND + 74, 79), "CURBCUT", font=f(M, 26), fill=MATT)
    return b, d


def folie_titel(nummer, ober, gross, unter, farbe=TINTE):
    b, d = grundplatte()
    y = 300
    if ober:
        mitte(d, ober.upper(), f(M, 30), y, MARK)
        y += 76
    y = umbruch(d, gross, f(SB, 92), RAND, y, BREIT - 2 * RAND, 108,
                farbe, zentriert=True)
    if unter:
        y += 44
        umbruch(d, unter, f(S, 40), RAND, y, BREIT - 2 * RAND - 60, 58,
                MATT, zentriert=True)
    return b


def folie_zahl(ober, zahl, unter, farbe=TINTE):
    b, d = grundplatte()
    mitte(d, ober.upper(), f(M, 30), 270, MARK)
    schrift = passend(d, zahl, SB, 240, BREIT - 2 * RAND)
    k = d.textbbox((0, 0), zahl, font=schrift)
    mitte(d, zahl, schrift, 400 - (k[3] - k[1]) // 2 + 60, farbe)
    umbruch(d, unter, f(S, 42), RAND, 700, BREIT - 2 * RAND - 40, 60,
            TINTE, zentriert=True)
    return b


def folie_liste(ober, titel, punkte, marke=MARK):
    b, d = grundplatte()
    mitte(d, ober.upper(), f(M, 30), 230, MARK)
    y = umbruch(d, titel, f(SB, 68), RAND, 300, BREIT - 2 * RAND, 84,
                TINTE, zentriert=True)
    y += 70
    innen = BREIT - 2 * RAND - 130
    klein = f(S, 32)
    for i, (kopf, text) in enumerate(punkte, 1):
        # Kastenhoehe aus dem Text, nicht aus einer Zahl, die einmal
        # gepasst hat. Sonst laeuft die dritte Zeile unten heraus.
        th = hoehe_fuer(d, text, klein, innen, 40)
        h = 82 + th + 24
        d.rounded_rectangle([RAND, y, BREIT - RAND, y + h], 6,
                            fill=FLAECHE, outline=LINIE, width=2)
        d.rectangle([RAND, y, RAND + 7, y + h], fill=marke)
        d.text((RAND + 40, y + 26), f"{i}", font=f(M, 34), fill=marke)
        d.text((RAND + 86, y + 24), kopf, font=f(SB, 40), fill=TINTE)
        umbruch(d, text, klein, RAND + 86, y + 82, innen, 40, MATT)
        y += h + 24
    return b


def folie_gegen(ober, titel, links, rechts):
    """Zwei Sachen nebeneinander - das ist der ganze Verkaufsgedanke."""
    b, d = grundplatte()
    mitte(d, ober.upper(), f(M, 30), 230, MARK)
    umbruch(d, titel, f(SB, 68), RAND, 300, BREIT - 2 * RAND, 84,
            TINTE, zentriert=True)
    y = 500
    innen = BREIT - 2 * RAND - 90
    klein = f(S, 32)
    for (kopf, zahl, text), farbe in ((links, SPERR), (rechts, FREI)):
        th = hoehe_fuer(d, text, klein, innen, 40)
        h = 176 + th + 26
        d.rounded_rectangle([RAND, y, BREIT - RAND, y + h], 6,
                            fill=FLAECHE, outline=LINIE, width=2)
        d.rectangle([RAND, y, RAND + 7, y + h], fill=farbe)
        d.text((RAND + 44, y + 30), kopf, font=f(SB, 42), fill=farbe)
        d.text((RAND + 44, y + 92), zahl, font=f(M, 66), fill=TINTE)
        umbruch(d, text, klein, RAND + 44, y + 176, innen, 40, MATT)
        y += h + 30
    return b


# --------------------------------------------------------------- die Folien

FOLIEN = [
    ("01", lambda: folie_titel(1, "Das dritte Geschäft", "Curbcut",
        "Was es ist, und wie du es startest.")),

    ("02", lambda: folie_titel(2, "Das Problem",
        "Seit Juni 2025 gilt ein Gesetz.",
        "Webseiten in Europa müssen auch für blinde Menschen "
        "benutzbar sein. Wer das nicht macht, zahlt.")),

    ("03", lambda: folie_zahl("Die Busse", "100'000",
        "Euro. Und es wird wirklich vollstreckt - ein Gericht in "
        "Frankreich hat 500 Euro pro Tag verhängt.", SPERR)),

    ("04", lambda: folie_zahl("Ich habe nachgemessen", "17 von 18",
        "Schweizer Seiten hatten Fehler. Bei 12 davon war die Seite "
        "wirklich nicht bedienbar.")),

    ("05", lambda: folie_liste("Was Curbcut macht", "Wie die MFK, aber für Webseiten", [
        ("Anschauen", "Adresse eingeben. Curbcut liest die Seite."),
        ("Sagen was kaputt ist", "Nicht 113 Fehler. Fünf Stellen, die man "
                                 "wirklich anfassen muss."),
        ("Jeden Tag nachschauen", "Weil so eine Seite ständig wieder "
                                  "kaputtgeht."),
    ])),

    ("06", lambda: folie_gegen("Warum bei uns", "Es gibt nur zwei Sachen am Markt",
        ("Billige Widgets", "ab 9.-", "Kleben etwas ueber die Seite. Wer "
         "prüft, schaut darunter. Ein Viertel der Klagen traf Seiten, die "
         "so ein Widget hatten."),
        ("Richtige Lösungen", "ab 400.-", "Funktionieren, aber kein "
         "normaler Betrieb zahlt das. Dazwischen ist nichts. Da sitzen wir."))),

    ("07", lambda: folie_gegen("Die Rechnung", "Was rein und was raus geht",
        ("Kostet dich", "6.- im Monat", "Domain und ein kleiner Server. "
         "Nicht pro Kunde - insgesamt."),
        ("Zahlt ein Kunde", "19 bis 149.-", "Im Monat. Der erste Kunde deckt "
         "die Kosten fast dreimal."))),

    ("08", lambda: folie_titel(8, "Warum sie kaufen",
        "Nicht weil es schön ist.",
        "Sondern weil sie Angst vor der Busse haben. Das ist der "
        "Unterschied zur Trinkflasche.")),

    ("09", lambda: folie_liste("So aktivierst du es", "Drei Schritte", [
        ("Domain kaufen", "curbcut.com, rund 12 Franken im Jahr. Das musst "
                          "du machen - ich habe kein Zahlungsmittel."),
        ("Paddle-Konto", "Nimmt Einzelpersonen ohne Firma und kümmert sich "
                         "um die Steuern weltweit."),
        ("Sag Bescheid", "Dann schalte ich die Seite online. Der Rest ist "
                         "gebaut und getestet."),
    ], FREI)),

    ("10", lambda: folie_titel(10, "Ehrlich",
        "Kunden kann dir niemand versprechen.",
        "Der Wächter läuft ab heute jeden Tag. Alles andere hängt "
        "daran, ob dich jemand findet.")),
]


def bauen():
    ziel = os.path.join(HIER, "bilder")
    os.makedirs(ziel, exist_ok=True)
    aus = []
    for name, mach in FOLIEN:
        b = mach()
        pfad = os.path.join(ziel, f"{name}.png")
        b.save(pfad)
        aus.append(pfad)
        print(f"  {name}.png")
    return aus


if __name__ == "__main__":
    bauen()
