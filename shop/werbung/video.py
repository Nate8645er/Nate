# -*- coding: utf-8 -*-
"""Werbevideo aus Nates hochgeladenem Film - Rahmen, Marke, Abspann.

WAS DER FILM IST

Nate am 19.8.2026: "Das koennen wir als werbe video benutzen."
13.05 Sekunden, 888x490, HEVC, mit Ton. Inhalt: Produktnahaufnahmen
auf Schwarz, Hund trinkt im Wald, Wanderung im Geroell, Katze trinkt
im Auto, Kuestenstrasse. Professionell gedreht.

DREI BEFUNDE AUS DER PRUEFUNG

1. DER KNOPF STIMMT NICHT GANZ. Bei voller Aufloesung gegen den
   Freisteller gehalten: die Flasche im Film traegt auf dem Knopf
   einen Wirbel mit zwei Punkten, Nates Flasche einen Pfotenabdruck
   (Ballen mit Ring, drei Zehen). Alles andere passt - klarer
   Koerper, tuerkiser Kopf, Napfform, und die beiden Schloss-Zeichen
   sitzen an derselben Stelle in derselben Form. Also dieselbe
   Bauform mit anderem Knopf, nicht das andere Modell aus dem
   30-Sekunden-Film (das hatte einen CREMEFARBENEN Koerper).
   Der Wirbel ist vermutlich ein Markenzeichen des Herstellers.

2. DIE AUFLOESUNG IST KNAPP. 888 Pixel Breite, Meta will 1080.
   Hochskaliert sind das Faktor 1.22 - vertretbar, aber nicht mehr.
   Deshalb wird NICHT beschnitten: der Film liegt in voller Breite im
   Rahmen, Text steht auf den Baendern darueber und darunter. Ein
   1:1-Zuschnitt haette 490 auf 1080 gestreckt, Faktor 2.2 - matsch.

3. DER TON BLEIBT - AUF NATES ANSAGE. Erste Fassung lief stumm:
   Meta spielt Anzeigen stumm an, und Musik in einem fremd
   produzierten Film ist die haeufigste Urheberrechtsfalle bei
   Videoanzeigen. Nate am 19.8.2026: "Benutz den sound vom video."
   Also bleibt er. Das aendert nichts an Befund 4 - es macht ihn nur
   wichtiger, weil jetzt Bild UND Musik daran haengen.

   Sauber gemacht heisst: der Ton bekommt am Schluss einen Ausklang
   von 0.8 Sekunden, und der Abspann traegt eine echte Stille-Spur.
   Ohne beides reisst die Musik am Schnitt hart ab, und ohne Tonspur
   im Abspann laesst sich gar nicht erst zusammensetzen.

4. OFFEN UND NUR VON NATE ZU BEANTWORTEN: woher der Film stammt und ob
   er ihn verwenden darf. Lieferanten geben Haendlern solche Filme
   haeufig ausdruecklich frei - dann ist alles in Ordnung. Stammt er
   von einer fremden Marke, kann Meta die Anzeige sperren. Diese
   Datei baut die Fassungen, sie veroeffentlicht nichts.
"""
import os
import subprocess
from PIL import Image, ImageDraw
from lib_studio import HIER, PREIS, font, text, block, fit_font
from lib_foto import TUERKIS, WEISS

QUELLE = os.environ.get(
    "LD_FILM",
    "/root/.claude/uploads/2d96a9a6-93ca-5da3-99c5-55dbdd35f6e9/"
    "cf1b6b76-2c5943c49ac14806a0023ed0197f45dc.mov")
AUS = os.path.join(HIER, "video")
GRUND = (11, 13, 15)          # derselbe Ton wie der Schleier der Fotomotive
MATT = (208, 208, 212)
FILM_B = 1080                 # Filmbreite im Rahmen
FILM_H = 596                  # 888x490 auf 1080 skaliert, gerade Zahl

# Ton: eine Einstellung fuer beide Abschnitte. Zusammensetzen mit
# "-c copy" geht nur, wenn Haupteil und Abspann dieselbe Tonspur-Form
# haben - gleiche Abtastrate, gleiche Kanalzahl, gleicher Kodierer.
TON = ["-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]
ENDE = 2.6                   # Sekunden Abspann
UEBER = 0.45                 # Sekunden Ueberblendung Film -> Abspann.
                             # 0.7 war zu lang: waehrend der Blende standen
                             # das Band des Films und der Text des Abspanns
                             # gleichzeitig da und lasen sich als
                             # Doppelbelichtung.

KOPF = ["Für Hund", "und Katze."]
SUB = "550 ml  ·  Sechs Farben"
KOPF_ENDE = ["Sechs Farben.", "Ein Napf."]
SUB_ENDE = "Für Hund und Katze  ·  550 ml"
HERO = os.path.join(HIER, "tiere", "letsdrink-hero-banner.jpg")
HERO_MITTE = 760              # Bildzeile, um die der Ausschnitt zentriert


def _plan(W, H, kopf_gr, mit_sub):
    """Wie hoch das untere Band bei dieser Schriftgroesse wirklich wird."""
    marke_gr = round(W * 0.021)
    sub_gr = round(W * 0.025)
    preis_gr = round(W * 0.030)
    bh = max(3, round(W * 0.0037))
    lh = round(kopf_gr * 1.04)
    p = dict(marke_gr=marke_gr, sub_gr=sub_gr, preis_gr=preis_gr,
             fuss_gr=round(W * 0.022), bh=bh, lh=lh, kopf_gr=kopf_gr,
             mit_sub=mit_sub,
             luft=round(W * 0.038), nach_balken=round(W * 0.021),
             nach_marke=round(W * 0.026), nach_kopf=round(W * 0.021),
             vor_regel=round(W * 0.036), nach_regel=round(W * 0.024))
    p["hoehe"] = (p["luft"] + bh + p["nach_balken"]
                  + round(marke_gr * 1.35) + p["nach_marke"]
                  + lh * len(KOPF)
                  + (p["nach_kopf"] + round(sub_gr * 1.4) if mit_sub else 0)
                  + p["vor_regel"] + 1 + p["nach_regel"]
                  + round(preis_gr * 1.4) + p["luft"])
    return p


def _schutz(W, H):
    """Bereiche, die die App mit Bedienelementen ueberdeckt.

    Bei 1080x1920 liegen oben rund 250 und unten rund 340 Pixel unter
    Namen, Fortschrittsbalken und dem Aktionsknopf von Meta. Erste
    Fassung liess das Band bis zum unteren Bildrand laufen - Preis und
    Adresse waeren genau dort gelandet, wo der Knopf sitzt. Im Verlauf
    (1:1 und 4:5) gibt es diese Zonen nicht.
    """
    return (250, 340) if H / W >= 1.6 else (0, 0)


def _passt(W, H):
    """Groesste Kopfzeile, die samt Band unter den Film passt.

    WARUM GERECHNET UND NICHT GEWAEHLT

    Erste Fassung setzte die Kopfgroesse auf 7.8 Prozent der Breite und
    das Band auf den Rest. Im Quadrat blieben aber nur 484 Pixel unter
    dem Film, waehrend der Text 647 brauchte - "und Katze." lief durch
    die Trennlinie und die Unterzeile aus dem Bild. Derselbe Fehler wie
    schon zweimal bei den Standbildern: ein Mass geraten, statt es
    ausrechnen zu lassen.

    Jetzt laeuft es andersherum. Der Film ist so hoch, wie er ist; was
    darunter bleibt, gibt die Schriftgroesse vor. Reicht es auch bei der
    Untergrenze nicht, faellt zuerst die Unterzeile weg - und wenn es
    dann immer noch nicht passt, bricht der Bau ab.
    """
    s_oben, s_unten = _schutz(W, H)
    breite = W - 2 * round(W * 0.074)
    deckel = min(round(W * 0.086),
                 min(fit_font(z, breite, True, track=-2.0)
                     for z in KOPF + KOPF_ENDE))
    for mit_sub in (True, False):
        gr = deckel
        while gr >= round(W * 0.042):
            p = _plan(W, H, gr, mit_sub)
            if s_unten:
                # HOCHFORMAT: der Film fuellt, was das Band uebriglaesst.
                # Bei fester Filmhoehe von 596 sass er als Streifen im
                # oberen Drittel und darunter stand Schwarz. Statt den
                # Rest leer zu lassen, wird der Film auf die freie Hoehe
                # gezogen und seitlich beschnitten - die Nahaufnahmen
                # sind mittig, der Beschnitt kostet nichts Wesentliches.
                fh = H - s_oben - s_unten - p["hoehe"]
                if fh >= 620:
                    p["film_h"] = fh - (fh % 2)
                    p["fuellen"] = True
                    p["oben"] = s_oben
                    return p
            else:
                frei = H - FILM_H
                if frei - p["hoehe"] >= round(W * 0.037):
                    p["film_h"] = FILM_H
                    p["fuellen"] = False
                    p["oben"] = frei - p["hoehe"]
                    return p
            gr -= 2
    raise ValueError("%dx%d: unter dem Film ist zu wenig Platz fuer den Text"
                     % (W, H))


def rahmen(W, H, name, *, kopf=None, sub=None, foto=None):
    """Rahmen mit Fenster. Ohne foto durchsichtig (fuer den Film),
    mit foto gleich gefuellt (fuer den Abspann)."""
    kopf = kopf or KOPF
    sub = sub or SUB
    p = _passt(W, H)
    oben = p["oben"]
    img = Image.new("RGBA", (W, H), GRUND + (255,))
    d = ImageDraw.Draw(img)
    if foto is None:
        d.rectangle([0, oben, W, oben + p["film_h"]], fill=(0, 0, 0, 0))
    else:
        img.paste(_streifen(foto, W, p["film_h"]), (0, oben))

    m = round(W * 0.074)
    breite = W - 2 * m
    y = oben + p["film_h"] + p["luft"]
    d.rectangle([m, y, m + round(W * 0.068), y + p["bh"] - 1], fill=TUERKIS)
    y += p["bh"] + p["nach_balken"]
    text(img, (m, y), "Let'sDrink", font(p["marke_gr"], True),
         (236, 236, 238), track=0.6)
    y += round(p["marke_gr"] * 1.35) + p["nach_marke"]
    y = block(img, (m, y), kopf, font(p["kopf_gr"], True), lh=p["lh"],
              fill=WEISS, track=-p["kopf_gr"] * 0.028)
    if p["mit_sub"]:
        text(img, (m, y + p["nach_kopf"]), sub, font(p["sub_gr"]), MATT)
        y += p["nach_kopf"] + round(p["sub_gr"] * 1.4)
    y += p["vor_regel"]
    d.rectangle([m, y, m + breite, y], fill=(120, 122, 126))
    y += 1 + p["nach_regel"]
    text(img, (m, y + round(p["preis_gr"] * 0.22)), "letsdrink-pet.com",
         font(p["fuss_gr"]), MATT, track=0.6)
    text(img, (m + breite, y), PREIS, font(p["preis_gr"], True), WEISS,
         anchor="rs")
    pfad = os.path.join(AUS, name)
    img.convert("RGB" if foto else "RGBA").save(pfad, "PNG")
    s_oben, s_unten = _schutz(W, H)
    print("     %dx%d  Kopf %d px, Band %d px, Film %d px ab %d px%s%s"
          % (W, H, p["kopf_gr"], p["hoehe"], p["film_h"], oben,
             "" if p["mit_sub"] else ", ohne Unterzeile",
             ", Schutzzone %d/%d" % (s_oben, s_unten) if s_unten else ""))
    return pfad, oben, p["film_h"], p["fuellen"]


def _streifen(pfad, W, hoehe):
    """Ausschnitt aus dem Sechs-Farben-Bild - IMMER ueber die volle Breite.

    WARUM NICHT EINFACH FUELLEN

    Erster Versuch nahm denselben Weg wie die Standbilder: Bild auf das
    Format bringen, ueberstehende Seiten wegschneiden. Im Hochformat
    fielen dabei zwei der sechs Flaschen weg - ausgerechnet auf dem
    Bild, das "Sechs Farben" sagt. Deshalb bleibt die Breite hier
    unangetastet und beschnitten wird nur oben und unten, zentriert um
    die Reihe der Flaschen.
    """
    im = Image.open(pfad).convert("RGB")
    band = round(im.width * hoehe / W)
    band = min(band, im.height)
    y = max(0, min(im.height - band, round(HERO_MITTE - band / 2)))
    return im.crop((0, y, im.width, y + band)).resize((W, hoehe), Image.LANCZOS)


def abspann(W, H, name):
    """Schluss: dieselbe Anordnung wie der Film, nur anderes Bild.

    WARUM ER SO AUSSIEHT

    Erste Fassung war Text auf Schwarz - Marke, Ueberschrift, Preis,
    sonst nichts. Nate hat einen Auszug geschickt: "schau das am
    schluss vom video entwas gutes kommt ein bild von den 6 farben und
    so". Er hat recht - der letzte Eindruck ist der, mit dem jemand
    weggeht, und ein leeres schwarzes Feld ist keiner.

    Zweiter Versuch nahm das Bild ganzflaechig auf hellem Grund. Das
    sah gut aus, sprang aber vom dunklen Film hart ins Helle, und
    waehrend der Blende standen zwei verschiedene Textbloecke
    uebereinander - eine Doppelbelichtung.

    Jetzt traegt der Abspann denselben Rahmen wie der Film: gleicher
    Grund, gleiche Bandhoehe, Text an derselben Stelle. Die Blende
    wechselt nur noch das Bild im Fenster und die Zeile darunter. Nichts
    springt, nichts ueberlagert sich.
    """
    pfad = os.path.join(AUS, name)
    img, _, _, _ = rahmen(W, H, name, kopf=KOPF_ENDE, sub=SUB_ENDE,
                          foto=HERO)
    return pfad


def filmlaenge():
    """Laenge der Quelle in Sekunden - fuer den Ausklang gebraucht.

    ffprobe steht in dieser Umgebung nicht zur Verfuegung, deshalb
    ueber ffmpeg: einmal ohne Ausgabe durchlaufen lassen und die
    gemeldete Dauer lesen.
    """
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", QUELLE],
                       capture_output=True, text=True)
    for zeile in r.stderr.splitlines():
        if "Duration:" in zeile:
            h, mi, se = zeile.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(mi) * 60 + float(se)
    raise ValueError("Laenge von %s nicht lesbar" % QUELLE)


def lauf(*teile):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
                   + list(teile), check=True)


def bauen(W, H, kuerzel):
    os.makedirs(AUS, exist_ok=True)
    rp, oben, fh, fuellen = rahmen(W, H, "rahmen-%s.png" % kuerzel)
    ap = abspann(W, H, "abspann-%s.png" % kuerzel)
    ziel = os.path.join(AUS, "letsdrink-video-%s.mp4" % kuerzel)

    dauer = filmlaenge()
    start = dauer - UEBER                    # hier beginnt die Blende
    gesamt = dauer + ENDE - UEBER

    if fuellen:
        skal = "scale=-2:%d,crop=%d:%d" % (fh, W, fh)
    else:
        skal = "scale=%d:%d" % (FILM_B, fh)

    # EIN Durchlauf statt drei. Vorher wurden Haupteil und Abspann
    # einzeln kodiert und mit "-c copy" aneinandergehaengt; eine
    # Ueberblendung geht so nicht, weil sie beide Spuren gleichzeitig
    # braucht. Ausserdem spart es zwei Kodierungen.
    lauf("-i", QUELLE, "-i", rp,
         "-loop", "1", "-framerate", "30", "-t", "%.2f" % ENDE, "-i", ap,
         "-filter_complex",
         "[0:v]%s,fps=30,setsar=1[v];"
         "[v]pad=%d:%d:0:%d:color=0x0B0D0F[pd];"
         "[pd][1:v]overlay=0:0[fr];"
         "[2:v]scale=%d:%d,fps=30,setsar=1[ab];"
         "[fr][ab]xfade=transition=fade:duration=%.2f:offset=%.2f,"
         "format=yuv420p[o];"
         "[0:a]afade=t=out:st=%.2f:d=%.2f,aresample=44100,"
         "apad=whole_dur=%.2f[a]"
         % (skal, W, H, oben, W, H, UEBER, start,
            max(0.0, start - 0.15), UEBER + 0.15, gesamt),
         "-map", "[o]", "-map", "[a]", "-t", "%.2f" % gesamt, "-r", "30",
         "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         *TON, "-movflags", "+faststart", ziel)
    print("  ->", os.path.basename(ziel), "%dx%d, %.1f s mit Ton"
          % (W, H, gesamt))
    return ziel


if __name__ == "__main__":
    for W, H, k in ((1080, 1080, "1x1"),
                    (1080, 1350, "4x5"),
                    (1080, 1920, "9x16")):
        bauen(W, H, k)
