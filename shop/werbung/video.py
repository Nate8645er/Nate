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

3. DER TON KOMMT WEG. Meta spielt Anzeigen stumm an, und Musik in
   einem fremd produzierten Film ist die haeufigste Urheberrechts-
   falle bei Videoanzeigen. Ohne Ton faellt das Risiko ganz weg und
   die Anzeige verliert nichts.

OFFEN UND NUR VON NATE ZU BEANTWORTEN: woher der Film stammt und ob
er ihn verwenden darf. Lieferanten geben Haendlern solche Filme
haeufig ausdruecklich frei - dann ist alles in Ordnung. Stammt er von
einer fremden Marke, kann Meta die Anzeige sperren. Diese Datei baut
die Fassungen, sie veroeffentlicht nichts.
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

KOPF = ["Für Hund", "und Katze."]
SUB = "550 ml  ·  Sechs Farben"


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
                 min(fit_font(z, breite, True, track=-2.0) for z in KOPF))
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


def rahmen(W, H, name):
    """Rahmen mit durchsichtigem Fenster, in dem spaeter der Film liegt."""
    p = _passt(W, H)
    oben = p["oben"]
    img = Image.new("RGBA", (W, H), GRUND + (255,))
    d = ImageDraw.Draw(img)
    d.rectangle([0, oben, W, oben + p["film_h"]], fill=(0, 0, 0, 0))

    m = round(W * 0.074)
    breite = W - 2 * m
    y = oben + p["film_h"] + p["luft"]
    d.rectangle([m, y, m + round(W * 0.068), y + p["bh"] - 1], fill=TUERKIS)
    y += p["bh"] + p["nach_balken"]
    text(img, (m, y), "Let'sDrink", font(p["marke_gr"], True),
         (236, 236, 238), track=0.6)
    y += round(p["marke_gr"] * 1.35) + p["nach_marke"]
    y = block(img, (m, y), KOPF, font(p["kopf_gr"], True), lh=p["lh"],
              fill=WEISS, track=-p["kopf_gr"] * 0.028)
    if p["mit_sub"]:
        text(img, (m, y + p["nach_kopf"]), SUB, font(p["sub_gr"]), MATT)
        y += p["nach_kopf"] + round(p["sub_gr"] * 1.4)
    y += p["vor_regel"]
    d.rectangle([m, y, m + breite, y], fill=(120, 122, 126))
    y += 1 + p["nach_regel"]
    text(img, (m, y + round(p["preis_gr"] * 0.22)), "letsdrink-pet.com",
         font(p["fuss_gr"]), MATT, track=0.6)
    text(img, (m + breite, y), PREIS, font(p["preis_gr"], True), WEISS,
         anchor="rs")
    pfad = os.path.join(AUS, name)
    img.save(pfad, "PNG")
    s_oben, s_unten = _schutz(W, H)
    print("     %dx%d  Kopf %d px, Band %d px, Film %d px ab %d px%s%s"
          % (W, H, p["kopf_gr"], p["hoehe"], p["film_h"], oben,
             "" if p["mit_sub"] else ", ohne Unterzeile",
             ", Schutzzone %d/%d" % (s_oben, s_unten) if s_unten else ""))
    return pfad, oben, p["film_h"], p["fuellen"]


def abspann(W, H, name):
    """Zwei Sekunden Standbild am Schluss: Marke, Preis, Adresse."""
    img = Image.new("RGB", (W, H), GRUND)
    d = ImageDraw.Draw(img)
    m = round(W * 0.074)
    bh = max(3, round(W * 0.0037))
    kopf_gr = min(round(W * 0.098),
                  min(fit_font(z, W - 2 * m, True, track=-2.0) for z in KOPF))
    lh = round(kopf_gr * 1.04)
    ganz = bh + round(H * 0.030) + round(W * 0.024 * 2.0) + lh * len(KOPF) \
        + round(H * 0.028) + round(W * 0.028)
    y = round((H - ganz) / 2)

    d.rectangle([m, y, m + round(W * 0.068), y + bh - 1], fill=TUERKIS)
    y += bh + round(H * 0.030)
    text(img, (m, y), "Let'sDrink", font(round(W * 0.024), True),
         (236, 236, 238), track=0.6)
    y += round(W * 0.024 * 2.0)
    y = block(img, (m, y), KOPF, font(kopf_gr, True), lh=lh, fill=WEISS,
              track=-kopf_gr * 0.028)
    text(img, (m, y + round(H * 0.028)), SUB, font(round(W * 0.028)), MATT)

    fy = H - round(H * 0.090)
    d.rectangle([m, fy - round(H * 0.040), W - m, fy - round(H * 0.040)],
                fill=(120, 122, 126))
    text(img, (m, fy + round(W * 0.030 * 0.22)), "letsdrink-pet.com",
         font(round(W * 0.022)), MATT, track=0.6)
    text(img, (W - m, fy), PREIS, font(round(W * 0.030), True), WEISS,
         anchor="rs")
    p = os.path.join(AUS, name)
    img.save(p, "PNG")
    return p


def lauf(*teile):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
                   + list(teile), check=True)


def bauen(W, H, kuerzel):
    os.makedirs(AUS, exist_ok=True)
    rp, oben, fh, fuellen = rahmen(W, H, "rahmen-%s.png" % kuerzel)
    ap = abspann(W, H, "abspann-%s.png" % kuerzel)
    haupt = os.path.join(AUS, "_h-%s.mp4" % kuerzel)
    ende = os.path.join(AUS, "_e-%s.mp4" % kuerzel)
    ziel = os.path.join(AUS, "letsdrink-video-%s.mp4" % kuerzel)

    # Film auf volle Breite, in den Rahmen setzen, Rahmen darueber, Ton weg.
    if fuellen:
        skal = "scale=-2:%d,crop=%d:%d,setsar=1[v]" % (fh, W, fh)
    else:
        skal = "scale=%d:%d,setsar=1[v]" % (FILM_B, fh)
    lauf("-i", QUELLE, "-i", rp, "-filter_complex",
         "[0:v]%s;"
         "[v]pad=%d:%d:0:%d:color=0x0B0D0F[p];"
         "[p][1:v]overlay=0:0,format=yuv420p[o]"
         % (skal, W, H, oben),
         "-map", "[o]", "-an", "-r", "30",
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", haupt)

    lauf("-loop", "1", "-t", "2", "-i", ap, "-vf",
         "scale=%d:%d,format=yuv420p" % (W, H),
         "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", "19", ende)

    liste = os.path.join(AUS, "_l-%s.txt" % kuerzel)
    with open(liste, "w") as f:
        for t in (haupt, ende):
            f.write("file '%s'\n" % t)
    lauf("-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", ziel)
    for t in (haupt, ende, liste):
        os.remove(t)
    print("  ->", os.path.basename(ziel), "%dx%d" % (W, H))
    return ziel


if __name__ == "__main__":
    for W, H, k in ((1080, 1080, "1x1"),
                    (1080, 1350, "4x5"),
                    (1080, 1920, "9x16")):
        bauen(W, H, k)
