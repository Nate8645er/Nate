#!/usr/bin/env python3
"""Baut das Ergebnis-Video: HTML-Folien via Chromium, Sprache via gTTS,
Montage via ffmpeg."""

import json
import os
import subprocess
import sys

ARBEIT = "/tmp/video"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BREITE, HOEHE = 1920, 1080

os.makedirs(ARBEIT, exist_ok=True)

BG = "#14150F"
FG = "#F2EFE6"
GEDAEMPFT = "#8C8A7E"
AKZENT = "#E08A2B"
ROT = "#C4553D"

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:%dpx; height:%dpx; overflow:hidden; }
body {
  background:%s; color:%s;
  font-family:"Liberation Sans","DejaVu Sans",sans-serif;
  display:flex; flex-direction:column; justify-content:center;
  padding:130px 150px; -webkit-font-smoothing:antialiased;
}
.kicker { font-size:26px; letter-spacing:.22em; text-transform:uppercase;
  color:%s; margin-bottom:44px; font-weight:700; }
h1 { font-size:104px; line-height:1.06; font-weight:700;
  letter-spacing:-.025em; max-width:20ch; }
h2 { font-size:74px; line-height:1.12; font-weight:700;
  letter-spacing:-.02em; max-width:22ch; }
.zahl { font-size:210px; line-height:.92; font-weight:700;
  letter-spacing:-.045em; color:%s; }
.zahl.rot { color:%s; }
p { font-size:38px; line-height:1.45; color:%s; max-width:30ch;
  margin-top:40px; }
.reihe { display:flex; gap:110px; margin-top:26px; }
.pos .k { font-size:23px; letter-spacing:.16em; text-transform:uppercase;
  color:%s; margin-bottom:18px; font-weight:700; }
.pos .v { font-size:104px; font-weight:700; letter-spacing:-.03em;
  line-height:1; }
.strich { width:104px; height:7px; background:%s; margin-bottom:44px; }
.zitat { font-size:60px; line-height:1.3; font-weight:400;
  font-style:italic; max-width:24ch; }
.quelle { font-size:27px; color:%s; margin-top:52px; letter-spacing:.04em; }
.fuss { position:absolute; bottom:74px; left:150px; font-size:24px;
  color:%s; letter-spacing:.14em; text-transform:uppercase; }
""" % (BREITE, HOEHE, BG, FG, AKZENT, AKZENT, ROT, GEDAEMPFT, GEDAEMPFT,
       AKZENT, GEDAEMPFT, GEDAEMPFT)

FOLIEN = [
    {
        "html": """<div class="strich"></div>
<h1>Ein Tag Arbeit.<br>Das Ergebnis.</h1>
<p>Ungeschönt, mit allem was schiefging.</p>""",
        "text": "Ein Tag Arbeit. Hier ist das Ergebnis. Ungeschönt, "
                "mit allem was schiefging.",
    },
    {
        "html": """<div class="kicker">Der Anfang</div>
<h2>Werkzeuge aktiviert</h2>
<div class="reihe">
  <div class="pos"><div class="k">Plugins</div><div class="v">26</div></div>
  <div class="pos"><div class="k">Skills</div><div class="v">93</div></div>
  <div class="pos"><div class="k">Agenten</div><div class="v">73</div></div>
</div>
<p>Dauerhaft im Repo verankert, nicht nur in dieser Sitzung.</p>""",
        "text": "Angefangen hat es mit Werkzeugen. Sechsundzwanzig Plugins "
                "aktiviert, dreiundneunzig Skills, dreiundsiebzig Agenten. "
                "Dauerhaft im Repository verankert. Das war der einfache "
                "Teil.",
    },
    {
        "html": """<div class="kicker">Der Shopify-Befund</div>
<div class="zahl rot">0</div>
<h2 style="margin-top:34px">Bestellungen in 90 Tagen</h2>
<p>Bei 2'539 Besuchen. Vierzehn Menschen standen an der Kasse.
Keiner kam durch.</p>""",
        "text": "Dann der Blick in den Shop. Zweitausendfünfhundert"
                "neununddreissig Besuche in neunzig Tagen. Null Bestellungen. "
                "Vierzehn Menschen standen an der Kasse. Keiner kam durch.",
    },
    {
        "html": """<div class="kicker">Die Ursache</div>
<h2>Es gab nichts zu kaufen.</h2>
<div class="reihe" style="margin-top:56px">
  <div class="pos"><div class="k">Katzenauto</div>
    <div class="v" style="font-size:56px">archiviert</div></div>
  <div class="pos"><div class="k">Trinkflasche</div>
    <div class="v" style="font-size:56px">Entwurf · Bestand 0</div></div>
</div>
<p>Kein Design-Problem. Kein Werbeproblem.</p>""",
        "text": "Der Grund war nicht das Design und nicht die Werbung. Es gab "
                "schlicht nichts zu kaufen. Zwei Produkte im Katalog. Eines "
                "archiviert, eines Entwurf mit Bestand null.",
    },
    {
        "html": """<div class="kicker">Und der Verkehr</div>
<div class="zahl rot">92 %</div>
<h2 style="margin-top:34px">Bots aus den USA</h2>
<p>Echter Schweizer Verkehr: 1,6 Besucher pro Tag.</p>""",
        "text": "Und zweiundneunzig Prozent des Verkehrs kamen direkt aus den "
                "USA. Bei einem deutschsprachigen Schweizer Katzenshop sind "
                "das keine Kunden, sondern Rauschen. Echter Verkehr: eins "
                "Komma sechs Besucher pro Tag.",
    },
    {
        "html": """<div class="kicker">Das neue Vorhaben</div>
<h1>Feierabend</h1>
<p>Arbeitsrapporte für Handwerker, diktiert per Sprachnachricht.
Design, Architektur und Datenschutz durchgearbeitet.</p>""",
        "text": "Also etwas Neues. Feierabend. Arbeitsrapporte für Handwerker, "
                "diktiert per Sprachnachricht. Design geschrieben, "
                "Architektur gebaut, Datenschutz durchdacht.",
    },
    {
        "html": """<div class="kicker">Die Marktanalyse</div>
<h2>Es gibt das schon.</h2>
<div class="reihe" style="margin-top:56px">
  <div class="pos"><div class="k">e-rapport.ch</div>
    <div class="v" style="font-size:74px">CHF 12.50</div></div>
</div>
<p>Pro Mitarbeiter und Monat. Schweizerdeutscher Sprachrapport,
inklusive Rechnungsstellung.</p>
<div class="quelle">An der Quelle geprüft, nicht geglaubt.</div>""",
        "text": "Dann kam die Marktanalyse. Es gibt das schon. E-Rapport "
                "Punkt C H bietet schweizerdeutschen Sprachrapport für zwölf "
                "Franken fünfzig pro Mitarbeiter und Monat. Inklusive "
                "Rechnungsstellung. Ich habe es an der Quelle geprüft, statt "
                "es zu glauben.",
    },
    {
        "html": """<div class="kicker">Der Einwand, der schwerer wiegt</div>
<div class="zitat">„Ein Vorhaben mit vier Monaten Bauzeit liefert vier
Monate legitimen Grund, nicht zu verkaufen."</div>
<p>Dieselbe Falle wie beim Shop. Nur schöner tapeziert.</p>""",
        "text": "Der Einwand, der schwerer wiegt als der Wettbewerb: Ein "
                "Vorhaben mit vier Monaten Bauzeit liefert vier Monate "
                "legitimen Grund, nicht zu verkaufen. Dieselbe Falle wie "
                "beim Shop. Nur schöner tapeziert.",
    },
    {
        "html": """<div class="kicker">Was trotzdem bleibt</div>
<div class="reihe">
  <div class="pos"><div class="k">Tests, grün</div><div class="v">133</div></div>
  <div class="pos"><div class="k">Module, wiederverwendbar</div>
    <div class="v">3</div></div>
</div>
<p>Pseudonymisierung, Webhook-Prüfung, Antwort-Validierung.
Dazu ein behobener Sicherheitsfehler: JAVIER stand ohne Passwort
offen im Netz.</p>""",
        "text": "Geblieben sind hundertdreiunddreissig grüne Tests und drei "
                "Module, die unabhängig vom Produkt taugen. Dazu ein "
                "behobener Sicherheitsfehler: Deine JAVIER-Instanz stand "
                "ohne Passwort offen im Netz.",
    },
    {
        "html": """<div class="kicker">Was jetzt zählt</div>
<div class="reihe">
  <div class="pos"><div class="k">Gespräche</div><div class="v">20</div></div>
  <div class="pos"><div class="k">Vorauszahlungen</div><div class="v">3</div></div>
  <div class="pos"><div class="k">Wochen Frist</div><div class="v">6</div></div>
</div>
<p>Keine Zeile Code. Kommen die drei nicht zusammen,
ist das Projekt beendet.</p>""",
        "text": "Was jetzt zählt, ist keine Zeile Code. Zwanzig Gespräche. "
                "Drei Vorauszahlungen à fünfhundert Franken. Sechs Wochen "
                "Frist. Kommen sie nicht zusammen, ist das Projekt beendet.",
    },
    {
        "html": """<div class="strich"></div>
<h1>06:45 Uhr.<br>Abholmarkt.</h1>
<p>Der einzige Schritt, der sich nicht delegieren lässt.</p>""",
        "text": "Der nächste Schritt lässt sich nicht delegieren. Morgen "
                "früh, viertel vor sieben, am Abholmarkt.",
    },
]


def folie_rendern(i, html):
    pfad_html = os.path.join(ARBEIT, "folie_%02d.html" % i)
    pfad_png = os.path.join(ARBEIT, "folie_%02d.png" % i)
    with open(pfad_html, "w", encoding="utf-8") as f:
        f.write("<!doctype html><html><head><meta charset='utf-8'>"
                "<style>%s</style></head><body>%s"
                "<div class='fuss'>Feierabend · 28.08.2026</div>"
                "</body></html>" % (CSS, html))
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", "--force-device-scale-factor=1",
         "--window-size=%d,%d" % (BREITE, HOEHE),
         "--screenshot=%s" % pfad_png, "file://" + pfad_html],
        check=True, capture_output=True, timeout=90)
    return pfad_png


def sprache_erzeugen(i, text):
    from gtts import gTTS
    pfad = os.path.join(ARBEIT, "ton_%02d.mp3" % i)
    gTTS(text, lang="de", slow=False).save(pfad)
    return pfad


def dauer(pfad):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", pfad], capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def main():
    teile = []
    for i, folie in enumerate(FOLIEN):
        png = folie_rendern(i, folie["html"])
        mp3 = sprache_erzeugen(i, folie["text"])
        d = dauer(mp3) + 0.85  # Atempause am Ende
        teil = os.path.join(ARBEIT, "teil_%02d.mp4" % i)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-loop", "1", "-i", png, "-i", mp3,
             "-f", "lavfi", "-t", "%.3f" % d,
             "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
             "-filter_complex",
             "[1:a]adelay=250|250[sp];[2:a][sp]amix=inputs=2:duration=longest[a]",
             "-map", "0:v", "-map", "[a]",
             "-t", "%.3f" % d, "-r", "25",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-shortest", teil],
            check=True, capture_output=True, timeout=180)
        teile.append(teil)
        print("  Folie %2d fertig (%.1fs)" % (i + 1, d), flush=True)

    liste = os.path.join(ARBEIT, "liste.txt")
    with open(liste, "w") as f:
        for t in teile:
            f.write("file '%s'\n" % t)

    ziel = "/home/user/Nate/ergebnis-28-08-2026.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", liste, "-c", "copy", ziel],
        check=True, capture_output=True, timeout=180)
    print("\nFertig: %s (%.1fs)" % (ziel, dauer(ziel)))
    return ziel


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
