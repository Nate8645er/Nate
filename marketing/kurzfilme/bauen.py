#!/usr/bin/env python3
"""Baut drei kurze Fassungen des Napf-Films fuer TikTok und Reels.

DIE QUELLE IST DIESELBE. Neu ist nur, WOMIT die Fassung anfaengt -
und genau das ist die einzige Stellschraube, die auf TikTok in den
ersten anderthalb Sekunden ueber Bleiben oder Weiterwischen
entscheidet. Deshalb drei Anfaenge statt drei Filme: das kostet keine
Credits und laesst sich sauber gegeneinander messen.

DIE VIER TEILE IM ORIGINAL (per Kontaktbogen ausgemessen, 1 Bild/s):
  A  0.0 - 3.0  Flasche auf der Bank, Pfote, Leine
  B  3.0 - 6.0  Hand haelt die Flasche, Daumen am Knopf
  C  6.0 - 12.0 Hund trinkt aus dem Napf, ganz nah
  D 12.0 - 15.0 Flasche am Rucksack, Weg, Hund

TEXT ALS BILD, NICHT ALS drawtext. Das mitgelieferte ffmpeg ist ohne
freetype gebaut - drawtext gibt es darin nicht (gemessen: "No such
filter"). Die Textkarten entstehen deshalb hier mit PIL und werden
als PNG mit Transparenz ueberblendet. Das ist ohnehin der bessere
Weg: Zeilenumbruch, Kastenform und Rand lassen sich genau setzen.

WO DER TEXT SITZT: oberes Drittel. Unten liegt die Bedienleiste der
App, rechts die Knopfspalte - beides verdeckt Text zuverlaessig.

WAS NICHT IM TEXT STEHT: keine Bewertungen, keine Zahlen ausser
550 ml und sechs Farben, keine Dringlichkeit, keine Zusage zur
Dichtigkeit. Und die Flasche steht nie auf dem Kopf.
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
QUELLE = "/home/user/Nate/shop/theme-nova/assets/a-film-napf.mp4"
ZIEL = "/tmp/claude-0/-home-user-Nate/2d96a9a6-93ca-5da3-99c5-55dbdd35f6e9/scratchpad/kurz"
SCHRIFT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BREITE, HOEHE = 720, 1280

FASSUNGEN = [
    {
        "datei": "kurz-1-hund.mp4",
        "name": "Der Hund zuerst",
        "teile": [(6.2, 11.2), (3.2, 6.0), (12.2, 15.0)],
        "text": [(0.3, 3.2, "Er trinkt aus der\nFlasche selbst."),
                 (5.4, 7.6, "Ein Knopf füllt\nden Napf."),
                 (8.4, 10.6, "550 ml · sechs Farben")],
    },
    {
        "datei": "kurz-2-knopf.mp4",
        "name": "Der Knopf zuerst",
        "teile": [(3.2, 6.0), (6.2, 11.2), (12.2, 15.0)],
        "text": [(0.2, 2.5, "Knopf drücken."),
                 (3.0, 5.6, "Der Napf füllt sich."),
                 (8.4, 10.6, "Öse für Band\noder Karabiner.")],
    },
    {
        "datei": "kurz-3-frage.mp4",
        "name": "Die Frage zuerst",
        "teile": [(0.6, 2.6), (3.2, 6.0), (6.2, 10.2), (12.2, 15.0)],
        "text": [(0.2, 2.0, "Wo trinkt dein Hund\nunterwegs?"),
                 (2.5, 4.8, "Der Napf ist\nschon dran."),
                 (5.4, 8.4, "Ein Knopfdruck, und\ner füllt sich."),
                 (9.4, 11.6, "550 ml · sechs Farben")],
    },
]


def karte(text, pfad, groesse=52):
    """Eine Textkarte als PNG mit Transparenz, so breit wie das Bild."""
    f = ImageFont.truetype(SCHRIFT, groesse)
    zeilen = text.split("\n")
    rand, luft, zeilenluft = 26, 18, 12

    # Erst messen, dann malen - der Kasten legt sich um den echten Satz.
    messer = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    masse = [messer.textbbox((0, 0), z, font=f) for z in zeilen]
    breiten = [m[2] - m[0] for m in masse]
    hoehen = [m[3] - m[1] for m in masse]
    kb = max(breiten) + 2 * luft
    kh = sum(hoehen) + zeilenluft * (len(zeilen) - 1) + 2 * luft

    bild = Image.new("RGBA", (BREITE, kh + 2 * rand), (0, 0, 0, 0))
    d = ImageDraw.Draw(bild)
    kx = (BREITE - kb) // 2
    d.rounded_rectangle([kx, rand, kx + kb, rand + kh],
                        radius=18, fill=(12, 16, 15, 190))

    y = rand + luft
    for z, m, h in zip(zeilen, masse, hoehen):
        d.text(((BREITE - (m[2] - m[0])) // 2 - m[0], y - m[1]), z,
               font=f, fill=(255, 255, 255, 255))
        y += h + zeilenluft

    bild.save(pfad)
    return bild.size


def bauen(f):
    n = len(f["teile"])
    ketten = []
    for i, (a, b) in enumerate(f["teile"]):
        ketten.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[t{i}]")
    ketten.append("".join(f"[t{i}]" for i in range(n))
                  + f"concat=n={n}:v=1:a=0[roh]")

    eingaben = ["-i", QUELLE]
    vor = "roh"
    for j, (von, bis, txt) in enumerate(f["text"]):
        png = os.path.join(ZIEL, f"_karte-{f['datei'][:-4]}-{j}.png")
        karte(txt, png)
        eingaben += ["-i", png]
        nummer = j + 1                      # 0 ist der Film
        aus = f"tx{j}"
        ketten.append(
            f"[{vor}][{nummer}:v]overlay=x=0:y=H*0.11"
            f":enable='between(t,{von},{bis})'[{aus}]"
        )
        vor = aus
    ketten.append(f"[{vor}]format=yuv420p[v]")

    ziel = os.path.join(ZIEL, f["datei"])
    stille = len(f["text"]) + 1             # Index der Stille-Eingabe
    befehl = [FF, "-y", "-loglevel", "error"] + eingaben + [
        "-f", "lavfi", "-t", "30", "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex", ";".join(ketten),
        "-map", "[v]", "-map", f"{stille}:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "20",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "64k", "-shortest",
        ziel,
    ]
    r = subprocess.run(befehl, capture_output=True, text=True)
    if r.returncode != 0:
        print("FEHLER bei", f["datei"])
        print(r.stderr[-1500:])
        return None
    return ziel


os.makedirs(ZIEL, exist_ok=True)
for f in FASSUNGEN:
    z = bauen(f)
    if not z:
        continue
    aus = subprocess.run([FF, "-i", z], capture_output=True, text=True).stderr
    d = [l.strip().split(",")[0] for l in aus.split("\n") if "Duration" in l]
    print(f"{f['datei']:22s} {os.path.getsize(z)//1024:5d} KB   "
          f"{d[0] if d else '?'}   {f['name']}")
