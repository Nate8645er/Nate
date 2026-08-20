#!/usr/bin/env python3
"""
farbe.py - Kontrast messen, nicht schaetzen.

Kontrast ist der haeufigste Fehler im Web: 83,9 Prozent der eine Million
meistbesuchten Startseiten haben zu wenig davon (WebAIM Million 2026). Es
ist zugleich der Fehler, den ein Overlay-Widget am schlechtesten loest -
es kann Farben zur Laufzeit umfaerben, aber damit bricht es Layouts und
verletzt die Gestaltung, weshalb die meisten Betreiber es wieder abschalten.

Hier wird gerechnet, nicht geschaut. Die Formel steht in WCAG 2.2 und ist
nicht verhandelbar:

    Luminanz  L = 0.2126*R + 0.7152*G + 0.0722*B   (linearisiert)
    Kontrast  (L_hell + 0.05) / (L_dunkel + 0.05)

Die Gewichte sind kein Geschmack. Das Auge ist fuer Gruen etwa siebenmal
empfindlicher als fuer Blau - darum wiegt Gruen 0.7152 und Blau 0.0722.
Wer Kontrast nach Augenmass beurteilt, taeuscht sich bei Gelb und Cyan
regelmaessig, und zwar immer in dieselbe Richtung: er haelt sie fuer
kontrastreicher als sie sind.
"""

import re

# WCAG 2.2, Kriterium 1.4.3 und 1.4.11
NORMAL = 4.5      # Text bis 24px, oder bis 18.66px wenn nicht fett
GROSS = 3.0       # ab 24px, oder ab 18.66px fett
BEDIENELEMENT = 3.0   # Rahmen von Eingabefeldern, Symbole, Diagramme

# Die 148 benannten CSS-Farben in Kurzform - nur die, die wirklich
# vorkommen. Wer "rebeccapurple" schreibt, weiss was er tut.
NAMEN = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (255, 0, 0),
    "green": (0, 128, 0), "blue": (0, 0, 255), "yellow": (255, 255, 0),
    "gray": (128, 128, 128), "grey": (128, 128, 128),
    "silver": (192, 192, 192), "lightgray": (211, 211, 211),
    "lightgrey": (211, 211, 211), "darkgray": (169, 169, 169),
    "darkgrey": (169, 169, 169), "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105), "whitesmoke": (245, 245, 245),
    "gainsboro": (220, 220, 220), "lightslategray": (119, 136, 153),
    "slategray": (112, 128, 144), "darkslategray": (47, 79, 79),
    "navy": (0, 0, 128), "teal": (0, 128, 128), "olive": (128, 128, 0),
    "purple": (128, 0, 128), "maroon": (128, 0, 0), "aqua": (0, 255, 255),
    "cyan": (0, 255, 255), "magenta": (255, 0, 255), "fuchsia": (255, 0, 255),
    "lime": (0, 255, 0), "orange": (255, 165, 0), "pink": (255, 192, 203),
    "brown": (165, 42, 42), "beige": (245, 245, 220),
    "ivory": (255, 255, 240), "khaki": (240, 230, 140),
    "lavender": (230, 230, 250), "salmon": (250, 128, 114),
    "gold": (255, 215, 0), "coral": (255, 127, 80),
    "crimson": (220, 20, 60), "indigo": (75, 0, 130),
    "violet": (238, 130, 238), "tan": (210, 180, 140),
    "transparent": None,
}

HEX = re.compile(r"^#([0-9a-fA-F]{3,8})$")
FUNKTION = re.compile(r"^(rgba?|hsla?)\s*\(([^)]*)\)$", re.IGNORECASE)


def lesen(text):
    """CSS-Farbe zu (r, g, b, a). None wenn nicht lesbar oder durchsichtig.

    Gibt bewusst None zurueck statt zu raten. Eine geratene Farbe erzeugt
    einen Befund, den es nicht gibt - und ein falscher Befund kostet mehr
    Vertrauen, als ein uebersehener kostet.
    """
    if not text:
        return None
    t = text.strip().lower()

    if t in NAMEN:
        v = NAMEN[t]
        return None if v is None else (*v, 1.0)

    m = HEX.match(t)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(z * 2 for z in h)
        elif len(h) == 4:
            h = "".join(z * 2 for z in h)
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
        if len(h) == 8:
            return (int(h[0:2], 16), int(h[2:4], 16),
                    int(h[4:6], 16), int(h[6:8], 16) / 255)
        return None

    m = FUNKTION.match(t)
    if m:
        art = m.group(1).lower()
        teile = [x.strip() for x in re.split(r"[,\s/]+", m.group(2)) if x.strip()]
        if len(teile) < 3:
            return None
        try:
            if art.startswith("rgb"):
                werte = []
                for x in teile[:3]:
                    if x.endswith("%"):
                        werte.append(round(float(x[:-1]) * 255 / 100))
                    else:
                        werte.append(int(float(x)))
                a = _alpha(teile[3]) if len(teile) > 3 else 1.0
                return (*[max(0, min(255, v)) for v in werte], a)
            else:
                h = float(teile[0].replace("deg", "")) % 360
                s = float(teile[1].rstrip("%")) / 100
                li = float(teile[2].rstrip("%")) / 100
                a = _alpha(teile[3]) if len(teile) > 3 else 1.0
                return (*_hsl_zu_rgb(h, s, li), a)
        except (ValueError, IndexError):
            return None
    return None


def _alpha(x):
    x = x.strip()
    return float(x[:-1]) / 100 if x.endswith("%") else float(x)


def _hsl_zu_rgb(h, s, li):
    c = (1 - abs(2 * li - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = li - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
    return tuple(round((v + m) * 255) for v in (r, g, b))


def luminanz(farbe):
    """Relative Leuchtdichte nach WCAG. 0 ist Schwarz, 1 ist Weiss."""
    def lineare(k):
        k = k / 255
        return k / 12.92 if k <= 0.03928 else ((k + 0.055) / 1.055) ** 2.4
    r, g, b = farbe[0], farbe[1], farbe[2]
    return 0.2126 * lineare(r) + 0.7152 * lineare(g) + 0.0722 * lineare(b)


def ueber(vorne, hinten):
    """Legt eine halbdurchsichtige Farbe ueber eine deckende.

    Ohne das misst man rgba(0,0,0,.5) als reines Schwarz und meldet einen
    Kontrast, der auf dem Bildschirm nie so aussieht.
    """
    a = vorne[3] if len(vorne) > 3 else 1.0
    if a >= 1.0:
        return vorne[:3]
    return tuple(round(vorne[i] * a + hinten[i] * (1 - a)) for i in range(3))


def kontrast(vorne, hinten):
    """Kontrastverhaeltnis. 1.0 heisst gleich, 21.0 ist Schwarz auf Weiss."""
    if vorne is None or hinten is None:
        return None
    v = luminanz(ueber(vorne, hinten))
    h = luminanz(hinten[:3])
    hell, dunkel = max(v, h), min(v, h)
    return (hell + 0.05) / (dunkel + 0.05)


def ziel_fuer(groesse_px, fett=False):
    """Welcher Wert reicht bei dieser Schriftgroesse?

    WCAG nennt Punkt, das Web rechnet in Pixel: 18pt sind 24px, 14pt sind
    18.66px. Grosse Schrift darf weniger Kontrast haben, weil die Buchstaben
    dickere Striche haben und dadurch besser lesbar bleiben.
    """
    if groesse_px is None:
        return NORMAL
    if groesse_px >= 24 or (fett and groesse_px >= 18.66):
        return GROSS
    return NORMAL


def als_hex(farbe):
    return "#{:02X}{:02X}{:02X}".format(*farbe[:3])


def _schieben(farbe, gegen, ziel, nach_dunkel, schritte=200):
    """Schiebt eine Farbe schrittweise in eine Richtung, bis das Ziel haelt."""
    r, g, b = farbe[0], farbe[1], farbe[2]
    for i in range(1, schritte + 1):
        t = i / schritte
        if nach_dunkel:
            k = (round(r * (1 - t)), round(g * (1 - t)), round(b * (1 - t)), 1.0)
        else:
            k = (round(r + (255 - r) * t), round(g + (255 - g) * t),
                 round(b + (255 - b) * t), 1.0)
        if kontrast(k, gegen) >= ziel:
            return k, t
    return None, 1.0


def abdunkeln_bis(vorne, hinten, ziel, schritte=200):
    """Der naechstliegende Ton derselben Farbe, der das Ziel haelt.

    Probiert beide Richtungen und nimmt die mit der KLEINEREN Aenderung.
    Zu raten, ob man hell oder dunkel muss, geht schief: Bei einem Grund
    mittlerer Helligkeit - etwa #999999 - reicht Aufhellen bis Weiss nicht
    aus (nur 2.85 zu 1), Abdunkeln bis Schwarz dagegen locker (7.36 zu 1).
    Eine Faustregel nach "ist der Grund hell" faellt genau dort um. Also
    wird gerechnet statt geschaetzt.

    Der Betreiber akzeptiert eine Korrektur eher, wenn seine Markenfarbe
    erkennbar bleibt - darum die kleinere Verschiebung, nicht der Sprung
    auf Schwarz oder Weiss.
    """
    dunkel, t_d = _schieben(vorne, hinten, ziel, True, schritte)
    hell, t_h = _schieben(vorne, hinten, ziel, False, schritte)
    if dunkel and hell:
        return dunkel if t_d <= t_h else hell
    return dunkel or hell or (0, 0, 0, 1.0)


def vorschlag(vorne, hinten, ziel):
    """Was muss sich aendern, damit das Ziel gehalten wird?

    Gibt (welches, farbe, erklaerung) zurueck - welches ist "text" oder "grund".

    Warum nicht immer der Text: Weisser Text kann nicht heller werden,
    schwarzer nicht dunkler. Bei weisser Schrift auf einer mittelhellen
    Markenfarbe - der haeufigste Fall bei Knoepfen - ist am Text nichts
    mehr zu holen, die Farbe dahinter ist zu hell. Ein Werkzeug, das dann
    trotzdem "aendere den Text" sagt, gibt einen Rat, der nicht ausfuehrbar
    ist, und der Betreiber merkt beim ersten Versuch, dass es nicht denkt.
    """
    jetzt = kontrast(vorne, hinten)
    if jetzt is None or jetzt >= ziel:
        return None

    # Halbdurchsichtige Schrift zuerst: Deckkraft erhoehen ist der
    # eleganteste Fix, weil die gewaehlte Farbe unangetastet bleibt.
    # rgba(0,0,0,.5) fuer Hilfstexte ist ein sehr haeufiges Muster - wer
    # das uebersieht, schlaegt dem Betreiber vor, sein Schwarz dunkler
    # zu machen, und das ist offensichtlicher Unsinn.
    a = vorne[3] if len(vorne) > 3 else 1.0
    if a < 1.0:
        for schritt in range(1, 21):
            neu_a = min(1.0, a + schritt * 0.05)
            probe = (vorne[0], vorne[1], vorne[2], neu_a)
            if kontrast(probe, hinten) >= ziel:
                return ("deckkraft", probe,
                        f"Die Schrift ist halbdurchsichtig ({a:g}). Deckkraft "
                        f"auf {neu_a:.2f} erhoehen - die Farbe selbst bleibt, "
                        f"wie sie ist.")

    kopf = luminanz(ueber(vorne, hinten))
    grund = luminanz(hinten[:3])

    # Ist am Text ueberhaupt noch Weg? Text muss sich vom Grund WEG bewegen.
    text_am_anschlag = (kopf > grund and kopf > 0.95) or (kopf < grund and kopf < 0.02)

    if not text_am_anschlag:
        neu = abdunkeln_bis(vorne, hinten, ziel)
        if kontrast(neu, hinten) >= ziel:
            richtung = "dunkler" if luminanz(neu[:3]) < kopf else "heller"
            return ("text", neu,
                    f"Schrift {richtung} setzen: {als_hex(vorne)} wird "
                    f"{als_hex(neu)}. Derselbe Farbton, nur so weit "
                    f"verschoben, wie noetig - die Marke bleibt erkennbar.")

    # Am Text ist nichts mehr zu holen: der Grund muss weg vom Text.
    neu_grund = abdunkeln_bis(hinten, vorne, ziel)
    if kontrast(vorne, neu_grund) >= ziel:
        richtung = "dunkler" if luminanz(neu_grund[:3]) < grund else "heller"
        return ("grund", neu_grund,
                f"Die Schrift ist schon am Anschlag - hier muss der "
                f"Hintergrund {richtung} werden: {als_hex(hinten)} wird "
                f"{als_hex(neu_grund)}.")

    return ("beides", None,
            "Diese Kombination laesst sich nicht durch Nachjustieren "
            "retten. Beide Farben liegen zu nah beieinander. Hier braucht "
            "es eine gestalterische Entscheidung, kein Rechenergebnis.")


if __name__ == "__main__":
    proben = [
        ("#777777", "#FFFFFF", "Graue Hilfstexte - der Klassiker"),
        ("#FFFFFF", "#45B6B2", "Weiss auf Tuerkis"),
        ("#000000", "#FFFFFF", "Schwarz auf Weiss"),
        ("rgba(0,0,0,0.5)", "#FFFFFF", "Halbdurchsichtiges Schwarz"),
        ("hsl(210, 80%, 60%)", "white", "Ein typisches Link-Blau"),
    ]
    print(f"{'VORNE':<22}{'HINTEN':<12}{'WERT':>7}  {'4.5?':<6} REPARATUR")
    print("-" * 78)
    for v, h, was in proben:
        fv, fh = lesen(v), lesen(h)
        k = kontrast(fv, fh)
        ok = "ja" if k >= NORMAL else "NEIN"
        rep = "" if k >= NORMAL else als_hex(abdunkeln_bis(fv, fh, NORMAL))
        print(f"{v:<22}{h:<12}{k:>6.2f}  {ok:<6} {rep}   {was}")
