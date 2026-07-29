#!/usr/bin/env python3
"""
Let'sDrink, Konzept B in fuenf Fassungen.
Studio-Look: heller Verlauf, Produkt zentriert, Spiegelung, Serifen-Schlagzeile.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/claude/ad"
OUT = "/mnt/user-data/outputs"
GF = "/usr/share/fonts/truetype/google-fonts"
os.makedirs(OUT, exist_ok=True)

F_DISP = f"{BASE}/Anton.ttf"
F_TEXT = f"{BASE}/Inter.ttf"
F_MONO = f"{BASE}/PlexMono.ttf"
F_SERI = f"{GF}/Lora-Variable.ttf"

INK   = (20, 30, 26)
PINE  = (24, 52, 41)
BONE  = (252, 250, 246)

ACCENTS = {
    "teal":   (32, 132, 150),
    "deep":   (16, 92, 107),
    "pine":   (34, 78, 60),
    "coral":  (198, 92, 58),
    "sky":    (86, 158, 176),
}


def F(p, s): return ImageFont.truetype(p, int(s))
def tw(d, s, f, tr=0.0): return sum(d.textlength(c, font=f) for c in s) + tr * max(0, len(s) - 1)
def trk(d, x, y, s, f, fill, tr=0.0):
    for c in s:
        d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + tr
    return x
def fitf(d, s, path, start, maxw, tr=0.0, mn=14):
    sz = start; f = F(path, sz)
    while tw(d, s, f, tr) > maxw and sz > mn:
        sz -= 2; f = F(path, sz)
    return f
def fitblock(d, lines, path, start, maxw, tr=0.0, mn=14):
    f = F(path, start)
    for ln in lines:
        f2 = fitf(d, ln, path, f.size, maxw, tr, mn)
        if f2.size < f.size: f = f2
    return f


def cutout(img, tol=238, feather=1.0):
    a = np.array(img.convert("RGB")).astype(np.int16)
    nw = (a[:, :, 0] > tol) & (a[:, :, 1] > tol) & (a[:, :, 2] > tol)
    m = Image.fromarray(np.where(nw, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(feather))
    m = m.point(lambda v: 0 if v < 70 else min(255, int(v * 1.4)))
    o = img.convert("RGBA"); o.putalpha(m)
    bb = o.getbbox()
    return o.crop(bb) if bb else o


def fit(img, w, h):
    r = min(w / img.width, h / img.height)
    out = img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)
    if r > 1.05:
        out = out.filter(ImageFilter.UnsharpMask(radius=1.5, percent=90, threshold=3))
    return out


def reflection(img, height_frac=0.34, top_alpha=90):
    """Gespiegeltes Produkt mit weichem Ausblenden. Der Studio-Trick."""
    h = int(img.height * height_frac)
    fl = img.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, img.width, h))
    a = np.array(fl).astype(float)
    ramp = np.linspace(top_alpha, 0, h)[:, None]
    a[:, :, 3] = np.clip(a[:, :, 3] * (ramp / 255.0), 0, 255)
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    return out.filter(ImageFilter.GaussianBlur(1.6))


def shade(canvas, img, x, y, blur=40, op=0.20, col=(40, 60, 60), dy=24):
    p = blur * 2
    s = Image.new("RGBA", (img.width + p * 2, img.height + p * 2), (0, 0, 0, 0))
    s.paste(img, (p, p), img); s = s.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(s); a[:, :, :3] = np.array(col); a[:, :, 3] = (a[:, :, 3] * op).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(a, "RGBA"), (x - p, y - p + dy))


def studio_bg(size, seed):
    w, h = size
    y = np.linspace(0, 1, h)[:, None, None]
    top = np.array((253, 251, 248), float)
    bot = np.array((231, 224, 213), float)
    arr = np.repeat(top * (1 - y) + bot * y, w, axis=1)
    arr += np.repeat(np.random.default_rng(seed).normal(0, 3.6, (h, w, 1)), 3, axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def build(cfg, hero):
    W, H = cfg["size"]
    M = int(W * 0.095)
    acc = ACCENTS[cfg["accent"]]
    c = studio_bg((W, H), cfg["seed"])
    d = ImageDraw.Draw(c, "RGBA")

    # Lichtinsel
    r = int(W * 0.50)
    d.ellipse([W / 2 - r, H * 0.36 - r, W / 2 + r, H * 0.36 + r], fill=(255, 255, 255, 135))

    # Kopfzeile
    fm = F(F_MONO, W * 0.0170)
    t = cfg["kicker"]
    lw = tw(d, t, fm, W * 0.005)
    trk(d, W / 2 - lw / 2, M * 0.82, t, fm, (*INK, 150), W * 0.005)

    # Produkt mit Standlinie und Spiegelung
    p = fit(hero, int(W * cfg["hero_w"]), int(H * cfg["hero_h"]))
    px, py = W // 2 - p.width // 2, int(H * cfg["hero_y"])
    base = py + p.height

    d.line([(M, base + 2), (W - M, base + 2)], fill=(*INK, 34), width=1)
    refl = reflection(p, 0.32, 82)
    c.alpha_composite(refl, (px, base + 3))
    shade(c, p, px, py, 42, 0.17, (50, 66, 64), 20)
    c.alpha_composite(p, (px, py))
    d = ImageDraw.Draw(c, "RGBA")

    y = base + int(H * 0.062)

    # Schlagzeile
    fh = fitblock(d, cfg["head"], F_SERI, W * cfg["head_size"], W - 2 * M)
    for ln in cfg["head"]:
        lw = tw(d, ln, fh)
        d.text((W / 2 - lw / 2, y), ln, font=fh, fill=PINE)
        y += int(fh.size * 1.15)

    y += int(W * 0.014)
    d.line([(W / 2 - int(W * 0.045), y), (W / 2 + int(W * 0.045), y)], fill=(*acc, 175), width=2)
    y += int(W * 0.030)

    # Beschreibung
    fs = fitblock(d, cfg["sub"], F_TEXT, W * 0.0265, W - 2 * M)
    for ln in cfg["sub"]:
        lw = tw(d, ln, fs)
        d.text((W / 2 - lw / 2, y), ln, font=fs, fill=(*INK, 195))
        y += int(W * 0.0415)

    # Merkmale
    y += int(W * 0.026)
    chips = cfg["chips"]
    fi = F(F_MONO, W * 0.0172)
    total = sum(tw(d, s, fi, W * 0.004) for s in chips) + int(W * 0.078) * (len(chips) - 1)
    while total > W - 2 * M and fi.size > 12:
        fi = F(F_MONO, fi.size - 1)
        total = sum(tw(d, s, fi, W * 0.004) for s in chips) + int(W * 0.078) * (len(chips) - 1)
    x = W / 2 - total / 2
    for i, s in enumerate(chips):
        x = trk(d, x, y, s, fi, (*PINE, 215), W * 0.004)
        if i < len(chips) - 1:
            d.ellipse([x + W * 0.033, y + fi.size * 0.42, x + W * 0.033 + 6, y + fi.size * 0.42 + 6], fill=acc)
            x += int(W * 0.078)
    content_bottom = y + fi.size * 1.4

    # Fussband
    bh = int(H * 0.100)
    band_y = H - bh
    print(f"   {cfg['name']:34s} Inhalt endet {int(content_bottom):4d}  Band ab {band_y:4d}  Abstand {int(band_y - content_bottom):4d}")
    d.rectangle([0, band_y, W, H], fill=cfg.get("band", PINE))
    d.line([(0, band_y), (W, band_y)], fill=(*acc, 190), width=3)

    fp = F(F_DISP, W * 0.058)
    d.text((M, band_y + bh * 0.26), "CHF 29.90", font=fp, fill=BONE)
    fn = F(F_TEXT, W * 0.0225)
    t2 = cfg["footer"]
    fn = fitf(d, t2, F_TEXT, fn.size, W * 0.52)
    lw = tw(d, t2, fn)
    d.text((W - M - lw, band_y + bh * 0.41), t2, font=fn, fill=(*BONE, 215))
    return c.convert("RGB")


src = Image.open(f"{BASE}/p1.png")
hero = cutout(src.crop((659, 50, 932, 986)))

VARIANTS = [
    dict(name="ad-B1-schuessel.png", accent="teal", seed=21,
         size=(1080, 1350), hero_w=0.34, hero_h=0.38, hero_y=0.135,
         head_size=0.068, kicker="LET'SDRINK  ·  SCHWEIZ",
         head=["Wasser dabei.", "Schüssel überflüssig."],
         sub=["Die Trinkflasche mit angebautem Napf. Einhandbedienung,",
              "auslaufsicher verschlossen, 550 ml für die lange Runde."],
         chips=["550 ml", "Einhandbedienung", "6 Farben"],
         footer="Gratisversand  ·  14 Tage Rückgabe"),

    dict(name="ad-B2-rueckfluss.png", accent="deep", seed=34,
         size=(1080, 1350), hero_w=0.36, hero_h=0.40, hero_y=0.125,
         head_size=0.070, kicker="DER UNTERSCHIED",
         head=["Der Rest", "läuft zurück."],
         sub=["Bei den meisten Flaschen kippst du weg, was übrig bleibt.",
              "Hier richtest du sie auf und das Wasser fliesst zurück."],
         chips=["Nichts wird weggekippt", "550 ml"],
         footer="Gratisversand Schweiz"),

    dict(name="ad-B3-einehand.png", accent="pine", seed=47,
         size=(1080, 1350), hero_w=0.33, hero_h=0.37, hero_y=0.140,
         head_size=0.074, kicker="FÜR UNTERWEGS",
         head=["Eine Hand reicht."],
         sub=["Knopf drücken, Wasser läuft in den Napf, dein Hund trinkt.",
              "Die Leine bleibt die ganze Zeit in der anderen Hand."],
         chips=["Einhandbedienung", "550 ml", "6 Farben"],
         footer="Gratisversand  ·  14 Tage Rückgabe"),

    dict(name="ad-B4-dicht.png", accent="coral", seed=58,
         size=(1080, 1350), hero_w=0.35, hero_h=0.39, hero_y=0.130,
         head_size=0.068, kicker="DIE HÄUFIGSTE FRAGE",
         head=["Bleibt dicht.", "Auch quer im Rucksack."],
         sub=["Verschlossen läuft nichts aus. Falls doch, bekommst du",
              "dein Geld zurück, ohne dass wir diskutieren."],
         chips=["Auslaufsicher", "14 Tage Rückgabe"],
         footer="Versand aus der Schweiz"),

    dict(name="ad-B5-langerunde.png", accent="sky", seed=63,
         size=(1080, 1350), hero_w=0.34, hero_h=0.38, hero_y=0.135,
         head_size=0.072, kicker="SOMMER MIT HUND",
         head=["Für die lange", "Runde."],
         sub=["550 ml reichen mehrfach, weil du den Rest nicht wegkippst.",
              "Passt in jeden Seitenhalter am Rucksack."],
         chips=["550 ml", "Wandern", "Auto"],
         footer="Gratisversand  ·  14 Tage Rückgabe"),
]

if __name__ == "__main__":
    for v in VARIANTS:
        img = build(v, hero)
        img.save(os.path.join(OUT, v["name"]), "PNG", optimize=True)
    print("fertig")
