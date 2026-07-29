#!/usr/bin/env python3
"""
Let'sDrink Werbebilder, Serie 2.
Vier eigenstaendige Konzepte, jeweils mit Titel und Beschreibung im Bild.
"""
import os, math
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

WATER_D = (16, 92, 107)
WATER    = (32, 132, 150)
WATER_L  = (96, 190, 202)
BONE     = (252, 250, 246)
CREAM    = (243, 238, 229)
INK      = (20, 30, 26)
PINE     = (24, 52, 41)
CORAL    = (206, 96, 62)


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


def fit(img, w, h, sharpen=True):
    r = min(w / img.width, h / img.height)
    out = img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)
    if sharpen and r > 1.05:
        out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=95, threshold=3))
    return out


def shade(canvas, img, x, y, blur=34, op=0.30, col=(0, 0, 0), dy=20):
    p = blur * 2
    s = Image.new("RGBA", (img.width + p * 2, img.height + p * 2), (0, 0, 0, 0))
    s.paste(img, (p, p), img); s = s.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(s); a[:, :, :3] = np.array(col); a[:, :, 3] = (a[:, :, 3] * op).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(a, "RGBA"), (x - p, y - p + dy))


def grad(size, top, bot, noise=5.0, seed=3):
    w, h = size
    y = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(top, float) * (1 - y) + np.array(bot, float) * y
    arr = np.repeat(arr, w, axis=1)
    arr += np.repeat(np.random.default_rng(seed).normal(0, noise, (h, w, 1)), 3, axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ============ Konzept A: Wasserblau ============
def concept_a(size, hero, name):
    W, H = size
    M = int(W * 0.085)
    c = grad((W, H), WATER, WATER_D, 6.0, 11)
    d = ImageDraw.Draw(c, "RGBA")

    # Wellenringe
    for i in range(5):
        r = int(W * (0.34 + i * 0.16))
        d.ellipse([W * 0.80 - r, H * 0.34 - r, W * 0.80 + r, H * 0.34 + r],
                  outline=(255, 255, 255, 16), width=2)

    fm = F(F_MONO, W * 0.019)
    trk(d, M, M, "LET'SDRINK", fm, (255, 255, 255, 190), W * 0.005)
    lbl = "FÜR HUNDE UNTERWEGS"
    lw = tw(d, lbl, fm, W * 0.005)
    trk(d, W - M - lw, M, lbl, fm, (255, 255, 255, 130), W * 0.005)

    y = M + int(W * 0.085)
    head = ["EINE HAND.", "ER TRINKT.", "FERTIG."]
    fh = fitblock(d, head, F_DISP, W * 0.135, W - 2 * M, tr=-W * 0.0015)
    for ln in head:
        trk(d, M, y, ln, fh, BONE, -fh.size * 0.012)
        y += int(fh.size * 0.87)

    y += int(W * 0.028)
    d.line([(M, y), (M + int(W * 0.13), y)], fill=(*WATER_L, 255), width=4)
    y += int(W * 0.036)

    sub = ["Knopf drücken, Wasser läuft in den angebauten Napf.",
           "Was übrig bleibt, läuft zurück in die Flasche."]
    fs = fitblock(d, sub, F_TEXT, W * 0.0295, W * 0.62)
    for ln in sub:
        d.text((M, y), ln, font=fs, fill=(255, 255, 255, 215)); y += int(W * 0.045)

    hh = int(H * 0.46)
    p = fit(hero, int(W * 0.40), hh)
    px, py = W - M - p.width, H - int(H * 0.135) - p.height
    shade(c, p, px, py, 38, 0.34, (0, 20, 26), 22)
    c.alpha_composite(p, (px, py)); d = ImageDraw.Draw(c, "RGBA")

    # Preisblock
    fp = F(F_DISP, W * 0.088)
    pw = tw(d, "CHF 29.90", fp)
    bx, byy = M, H - int(H * 0.135) - int(W * 0.115)
    d.rounded_rectangle([bx, byy, bx + pw + int(W * 0.075), byy + int(W * 0.115)],
                        radius=int(W * 0.012), fill=BONE)
    d.text((bx + int(W * 0.037), byy + int(W * 0.014)), "CHF 29.90", font=fp, fill=WATER_D)

    print(f"   [A] Produkt links bei {px}, Preisblock endet bei {int(bx + pw + W*0.075)}, Luecke {int(px - (bx + pw + W*0.075))}")
    bh = int(H * 0.075)
    d.rectangle([0, H - bh, W, H], fill=(*WATER_D, 255))
    fb = F(F_TEXT, W * 0.0245)
    line = "550 ml  ·  auslaufsicher  ·  Gratisversand Schweiz  ·  14 Tage Rückgabe"
    fb = fitf(d, line, F_TEXT, fb.size, W - 2 * M)
    lw = tw(d, line, fb)
    d.text((W / 2 - lw / 2, H - bh + (bh - fb.size * 1.25) / 2), line, font=fb, fill=(255, 255, 255, 225))
    return c.convert("RGB"), name


# ============ Konzept B: Studio Rein ============
def concept_b(size, hero, name):
    W, H = size
    M = int(W * 0.095)
    c = grad((W, H), (252, 250, 246), (234, 228, 218), 4.0, 21)
    d = ImageDraw.Draw(c, "RGBA")
    r = int(W * 0.46)
    d.ellipse([W / 2 - r, H * 0.40 - r, W / 2 + r, H * 0.40 + r], fill=(255, 255, 255, 120))

    fm = F(F_MONO, W * 0.0175)
    t = "LET'SDRINK  ·  SCHWEIZ"
    lw = tw(d, t, fm, W * 0.005)
    trk(d, W / 2 - lw / 2, M, t, fm, (*INK, 150), W * 0.005)

    p = fit(hero, int(W * 0.36), int(H * 0.40))
    px, py = W // 2 - p.width // 2, int(H * 0.145)
    shade(c, p, px, py, 40, 0.20, (40, 60, 60), 26)
    c.alpha_composite(p, (px, py)); d = ImageDraw.Draw(c, "RGBA")

    y = py + p.height + int(H * 0.045)
    head = ["Wasser dabei.", "Schüssel überflüssig."]
    fh = fitblock(d, head, F_SERI, W * 0.072, W - 2 * M)
    for ln in head:
        lw = tw(d, ln, fh)
        d.text((W / 2 - lw / 2, y), ln, font=fh, fill=PINE); y += int(fh.size * 1.16)

    y += int(W * 0.018)
    d.line([(W / 2 - int(W * 0.05), y), (W / 2 + int(W * 0.05), y)], fill=(*WATER, 160), width=2)
    y += int(W * 0.032)

    sub = ["Die Trinkflasche mit angebautem Napf. Einhandbedienung,",
           "auslaufsicher verschlossen, 550 ml für die lange Runde."]
    fs = fitblock(d, sub, F_TEXT, W * 0.0270, W - 2 * M)
    for ln in sub:
        lw = tw(d, ln, fs)
        d.text((W / 2 - lw / 2, y), ln, font=fs, fill=(*INK, 195)); y += int(W * 0.042)

    y += int(W * 0.030)
    items = ["550 ml", "Einhandbedienung", "6 Farben"]
    fi = F(F_MONO, W * 0.0180)
    total = sum(tw(d, s, fi, W * 0.004) for s in items) + int(W * 0.085) * (len(items) - 1)
    x = W / 2 - total / 2
    for i, s in enumerate(items):
        x = trk(d, x, y, s, fi, (*PINE, 210), W * 0.004)
        if i < len(items) - 1:
            d.ellipse([x + W * 0.036, y + fi.size * 0.42, x + W * 0.036 + 6, y + fi.size * 0.42 + 6], fill=WATER)
            x += int(W * 0.085)

    bh = int(H * 0.105)
    print(f"   [B] Inhalt endet {int(y + fi.size*1.3)}, Band ab {H-bh}, Abstand {int(H-bh-(y+fi.size*1.3))}")
    d.rectangle([0, H - bh, W, H], fill=PINE)
    fp = F(F_DISP, W * 0.062)
    d.text((M, H - bh + bh * 0.24), "CHF 29.90", font=fp, fill=BONE)
    fn = F(F_TEXT, W * 0.0230)
    t2 = "Gratisversand  ·  14 Tage Rückgabe"
    lw = tw(d, t2, fn)
    d.text((W - M - lw, H - bh + bh * 0.40), t2, font=fn, fill=(*BONE, 210))
    return c.convert("RGB"), name


# ============ Konzept C: Problem / Lösung ============
def concept_c(size, hero, name):
    W, H = size
    M = int(W * 0.075)
    c = grad((W, H), CREAM, (231, 224, 212), 5.0, 33)
    d = ImageDraw.Draw(c, "RGBA")
    split = int(W * 0.50)
    d.rectangle([split, 0, W, H], fill=WATER)
    d.line([(split, 0), (split, H)], fill=(*PINE, 60), width=2)

    # linke Seite: das Problem
    fm = F(F_MONO, W * 0.0170)
    trk(d, M, M, "OHNE", fm, (*CORAL, 255), W * 0.006)
    y = M + int(W * 0.058)
    left = ["Wasser dabei,", "aber keine", "Schüssel."]
    fh = fitblock(d, left, F_DISP, W * 0.088, split - M - int(W * 0.05), tr=-W * 0.001)
    for ln in left:
        trk(d, M, y, ln, fh, PINE, -fh.size * 0.012); y += int(fh.size * 0.90)
    y += int(W * 0.022)
    ls = ["Die hohle Hand hilft ihm nicht.",
          "Die Schüssel macht den Rucksack nass."]
    fs = fitblock(d, ls, F_TEXT, W * 0.0245, split - M - int(W * 0.05))
    for ln in ls:
        d.text((M, y), ln, font=fs, fill=(*INK, 185)); y += int(W * 0.038)

    # rechte Seite: die Lösung
    trk(d, split + M * 0.7, M, "MIT", fm, (*BONE, 255), W * 0.006)
    p = fit(hero, int(W * 0.30), int(H * 0.44))
    px = split + (W - split) // 2 - p.width // 2
    py = int(H * 0.20)
    shade(c, p, px, py, 34, 0.32, (0, 24, 30), 20)
    c.alpha_composite(p, (px, py)); d = ImageDraw.Draw(c, "RGBA")

    y = py + p.height + int(H * 0.035)
    right = ["Eine Hand.", "Er trinkt."]
    fh2 = fitblock(d, right, F_DISP, W * 0.070, W - split - 2 * int(M * 0.7), tr=-W * 0.001)
    for ln in right:
        lw = tw(d, ln, fh2, -fh2.size * 0.012)
        trk(d, split + (W - split) / 2 - lw / 2, y, ln, fh2, BONE, -fh2.size * 0.012)
        y += int(fh2.size * 0.92)
    y += int(W * 0.014)
    rs = ["Napf angebaut, Rest läuft zurück."]
    fs2 = fitblock(d, rs, F_TEXT, W * 0.0235, W - split - 2 * int(M * 0.7))
    for ln in rs:
        lw = tw(d, ln, fs2)
        d.text((split + (W - split) / 2 - lw / 2, y), ln, font=fs2, fill=(255, 255, 255, 215))

    bh = int(H * 0.115)
    print(f"   [C] rechte Spalte endet {int(y + fs2.size*1.4)}, Band ab {H-bh}, Abstand {int(H-bh-(y+fs2.size*1.4))}")
    d.rectangle([0, H - bh, W, H], fill=PINE)
    fp = F(F_DISP, W * 0.066)
    d.text((M, H - bh + bh * 0.22), "CHF 29.90", font=fp, fill=BONE)
    fn = F(F_TEXT, W * 0.0235)
    t2 = "550 ml  ·  Gratisversand Schweiz"
    lw = tw(d, t2, fn)
    d.text((W - M - lw, H - bh + bh * 0.38), t2, font=fn, fill=(*BONE, 215))
    return c.convert("RGB"), name


# ============ Konzept D: Im Einsatz ============
def concept_d(size, scene, name):
    W, H = size
    M = int(W * 0.085)
    c = grad((W, H), (250, 247, 241), (226, 219, 206), 5.0, 42)
    d = ImageDraw.Draw(c, "RGBA")

    band_top = int(H * 0.055)
    d.rectangle([0, band_top, W, int(H * 0.52)], fill=(*WATER, 30))

    s = fit(scene, int(W * 0.98), int(H * 0.42))
    sx, sy = W // 2 - s.width // 2, int(H * 0.10)
    shade(c, s, sx, sy, 36, 0.22, (40, 60, 55), 20)
    c.alpha_composite(s, (sx, sy)); d = ImageDraw.Draw(c, "RGBA")

    fm = F(F_MONO, W * 0.0180)
    t = "LET'SDRINK  ·  IM EINSATZ"
    lw = tw(d, t, fm, W * 0.005)
    trk(d, W / 2 - lw / 2, M * 0.55, t, fm, (*PINE, 175), W * 0.005)

    y = sy + s.height + int(H * 0.045)
    head = ["ER TRINKT,", "WO IHR GERADE", "SEID."]
    fh = fitblock(d, head, F_DISP, W * 0.115, W - 2 * M, tr=-W * 0.0015)
    for ln in head:
        lw = tw(d, ln, fh, -fh.size * 0.012)
        trk(d, W / 2 - lw / 2, y, ln, fh, PINE, -fh.size * 0.012)
        y += int(fh.size * 0.87)

    y += int(W * 0.026)
    sub = ["Trinkflasche mit angebautem Napf, 550 ml.",
           "Eine Hand genügt, die Leine bleibt in der anderen."]
    fs = fitblock(d, sub, F_TEXT, W * 0.0290, W - 2 * M)
    for ln in sub:
        lw = tw(d, ln, fs)
        d.text((W / 2 - lw / 2, y), ln, font=fs, fill=(*INK, 200)); y += int(W * 0.044)

    bh = int(H * 0.125)
    print(f"   [D] Inhalt endet {int(y)}, Band ab {H-bh}, Abstand {int(H-bh-y)}")
    d.rectangle([0, H - bh, W, H], fill=WATER_D)
    fp = F(F_DISP, W * 0.072)
    d.text((M, H - bh + bh * 0.22), "CHF 29.90", font=fp, fill=BONE)
    fn = F(F_TEXT, W * 0.0240)
    for i, ln in enumerate(["Gratisversand Schweiz", "14 Tage Rückgabe"]):
        lw = tw(d, ln, fn)
        d.text((W - M - lw, H - bh + bh * 0.24 + i * int(W * 0.042)), ln, font=fn, fill=(*BONE, 225))
    return c.convert("RGB"), name


# ---------- Quellen ----------
src = Image.open(f"{BASE}/p1.png")
hero = cutout(src.crop((659, 50, 932, 986)))
scene = cutout(src.crop((0, 43, 627, 680)))

jobs = [
    concept_a((1080, 1350), hero, "ad-A-wasserblau-4x5.png"),
    concept_a((1080, 1920), hero, "ad-A-wasserblau-9x16.png"),
    concept_b((1080, 1350), hero, "ad-B-studio-4x5.png"),
    concept_c((1080, 1350), hero, "ad-C-problem-loesung-4x5.png"),
    concept_d((1080, 1920), scene, "ad-D-im-einsatz-9x16.png"),
]

for img, name in jobs:
    p = os.path.join(OUT, name)
    img.save(p, "PNG", optimize=True)
    print("gespeichert:", name, img.size)
