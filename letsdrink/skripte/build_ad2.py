#!/usr/bin/env python3
"""
Let'sDrink Werbebild-Generator, Fassung 2.
Drei-Schrift-System, gemessener Vertikalfluss, technische Annotation.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/claude/ad"
OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

# ---------- Palette "Trail Heat" ----------
SAND      = (241, 235, 225)
SAND_DEEP = (226, 216, 200)
PINE      = (24, 52, 41)
WATER     = (44, 148, 166)
BONE      = (252, 249, 243)
INK       = (22, 32, 27)

F_DISP = os.path.join(BASE, "Anton.ttf")
F_TEXT = os.path.join(BASE, "Inter.ttf")
F_MONO = os.path.join(BASE, "PlexMono.ttf")


def F(path, size):
    return ImageFont.truetype(path, int(size))


# ---------- Textwerkzeuge ----------
def tw(d, s, f, track=0.0):
    return sum(d.textlength(c, font=f) for c in s) + track * max(0, len(s) - 1)


def draw_tracked(d, x, y, s, f, fill, track=0.0):
    for c in s:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + track
    return x


def th(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[3] - b[1]


def fit_font(d, s, path, start, max_w, track=0.0, min_size=18):
    size = start
    f = F(path, size)
    while tw(d, s, f, track) > max_w and size > min_size:
        size -= 2
        f = F(path, size)
    return f


# ---------- Bildwerkzeuge ----------
def cutout(img, tol=238, feather=1.0):
    a = np.array(img.convert("RGB")).astype(np.int16)
    nw = (a[:, :, 0] > tol) & (a[:, :, 1] > tol) & (a[:, :, 2] > tol)
    alpha = np.where(nw, 0, 255).astype(np.uint8)
    m = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(feather))
    m = m.point(lambda v: 0 if v < 70 else min(255, int(v * 1.4)))
    out = img.convert("RGBA")
    out.putalpha(m)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def fit(img, w, h):
    r = min(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)


def shadow(canvas, img, x, y, blur=30, op=0.28, col=PINE, dy=18):
    pad = blur * 2
    s = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    s.paste(img, (pad, pad), img)
    s = s.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(s)
    a[:, :, :3] = np.array(col)
    a[:, :, 3] = (a[:, :, 3] * op).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(a, "RGBA"), (x - pad, y - pad + dy))


# ---------- Hintergrund ----------
def background(size, seed=7):
    w, h = size
    yy = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(SAND, float) * (1 - yy) + np.array(SAND_DEEP, float) * yy
    arr = np.repeat(arr, w, axis=1)
    rng = np.random.default_rng(seed)
    arr += np.repeat(rng.normal(0, 6.0, (h, w, 1)), 3, axis=2)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # Höhenlinien, Verweis auf den Wanderweg
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = 26
    for i in range(lines):
        base = h * (0.06 + 0.92 * i / (lines - 1))
        amp = 26 + 16 * math.sin(i * 0.9)
        freq = 1.6 + 0.35 * math.sin(i * 0.5)
        pts = []
        for x in range(0, w + 8, 8):
            t = x / w
            y = base + amp * math.sin(t * math.pi * freq + i * 0.7) \
                     + amp * 0.35 * math.sin(t * math.pi * freq * 2.3 + i)
            pts.append((x, y))
        d.line(pts, fill=(*INK, 11), width=1, joint="curve")
    return Image.alpha_composite(img, layer)


def reg_marks(d, w, h, m, col=INK, a=55, L=26):
    for (x, y, dx, dy) in [(m, m, 1, 1), (w - m, m, -1, 1),
                           (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
        d.line([(x, y), (x + dx * L, y)], fill=(*col, a), width=2)
        d.line([(x, y), (x, y + dy * L)], fill=(*col, a), width=2)


# ---------- Creative ----------
def build(cfg):
    W, H = cfg["size"]
    M = int(W * 0.088)
    canvas = background((W, H), seed=cfg.get("seed", 7))
    d = ImageDraw.Draw(canvas, "RGBA")
    cx = W // 2

    reg_marks(d, W, H, int(M * 0.55))

    band_h = int(H * cfg["band"])
    band_y = H - band_h
    y = M

    # ---- Kopfzeile ----
    fm = F(F_MONO, W * 0.0195)
    tr = W * 0.0055
    draw_tracked(d, M, y, "LET'SDRINK", fm, (*PINE, 240), tr)
    right = cfg["topright"]
    d_w = tw(d, right, fm, tr)
    draw_tracked(d, W - M - d_w, y, right, fm, (*PINE, 150), tr)
    y += int(W * 0.030)
    d.line([(M, y), (W - M, y)], fill=(*PINE, 55), width=1)
    y += int(W * 0.052)

    # ---- Headline ----
    hl = cfg["headline"]
    size0 = W * cfg["hl_size"]
    fh = F(F_DISP, size0)
    for ln in hl:
        f2 = fit_font(d, ln, F_DISP, size0, W - 2 * M, track=-size0 * 0.012)
        if f2.size < fh.size:
            fh = f2
    lead = int(fh.size * 0.86)
    for ln in hl:
        wln = tw(d, ln, fh, -fh.size * 0.012)
        draw_tracked(d, cx - wln / 2, y, ln, fh, PINE, -fh.size * 0.012)
        y += lead
    y += int(W * 0.024)

    # ---- Subline ----
    fs = F(F_TEXT, W * 0.0300)
    for ln in cfg["sub"]:
        fs = fit_font(d, ln, F_TEXT, fs.size, W - 2 * M, min_size=16)
    for ln in cfg["sub"]:
        wln = tw(d, ln, fs)
        d.text((cx - wln / 2, y), ln, font=fs, fill=(*INK, 200))
        y += int(W * 0.0455)
    y += int(W * 0.030)

    # ---- Produktzone ----
    feat = cfg.get("features")
    sw = cfg.get("swatches", False)
    reserve = 0
    if feat:
        reserve += int(W * 0.115)
    if sw:
        reserve += int(W * 0.135)
    zone_h = band_y - y - reserve - int(W * 0.045)

    hero = fit(cfg["hero"], int(W * 0.50), int(zone_h * 0.97))
    hx = cx - hero.width // 2
    hy = y + (zone_h - hero.height) // 2

    r = int(min(W * 0.40, zone_h * 0.56))
    ccx, ccy = cx, hy + hero.height // 2
    d.ellipse([ccx - r, ccy - r, ccx + r, ccy + r], fill=(*WATER, 24))
    d.ellipse([ccx - r, ccy - r, ccx + r, ccy + r], outline=(*WATER, 95), width=2)
    ri = int(r * 0.74)
    d.ellipse([ccx - ri, ccy - ri, ccx + ri, ccy + ri], outline=(*WATER, 40), width=1)

    shadow(canvas, hero, hx, hy)
    canvas.alpha_composite(hero, (hx, hy))
    d = ImageDraw.Draw(canvas, "RGBA")

    # ---- Annotationen ----
    fa = F(F_MONO, W * 0.0175)
    fan = F(F_MONO, W * 0.0150)
    for i, (side, frac, num, label) in enumerate(cfg["notes"]):
        ay = hy + int(hero.height * frac)
        if side == "l":
            ex = hx - int(W * 0.018)
            sx = M + int(W * 0.005)
            d.line([(sx, ay), (ex, ay)], fill=(*PINE, 105), width=1)
            d.ellipse([ex - 4, ay - 4, ex + 4, ay + 4], fill=WATER)
            draw_tracked(d, sx, ay - int(W * 0.040), num, fan, (*WATER, 235), W * 0.003)
            d.text((sx, ay - int(W * 0.024)), label, font=fa, fill=(*PINE, 215))
        else:
            sx = hx + hero.width + int(W * 0.018)
            ex = W - M - int(W * 0.005)
            d.line([(sx, ay), (ex, ay)], fill=(*PINE, 105), width=1)
            d.ellipse([sx - 4, ay - 4, sx + 4, ay + 4], fill=WATER)
            lw = tw(d, label, fa)
            nw_ = tw(d, num, fan, W * 0.003)
            draw_tracked(d, ex - nw_, ay - int(W * 0.040), num, fan, (*WATER, 235), W * 0.003)
            d.text((ex - lw, ay - int(W * 0.024)), label, font=fa, fill=(*PINE, 215))

    y = hy + hero.height + int(W * 0.045)

    # ---- Merkmalzeile ----
    if feat:
        colw = (W - 2 * M) / len(feat)
        fnum = F(F_MONO, W * 0.0165)
        flab = F(F_TEXT, W * 0.0250)
        for _, lab in feat:
            flab = fit_font(d, lab, F_TEXT, flab.size, colw * 0.90, min_size=14)
        for i, (num, lab) in enumerate(feat):
            colx = M + colw * i
            d.line([(colx, y), (colx + colw * 0.90, y)], fill=(*PINE, 45), width=1)
            draw_tracked(d, colx, y + int(W * 0.014), num, fnum, (*WATER, 240), W * 0.003)
            d.text((colx, y + int(W * 0.042)), lab, font=flab, fill=(*PINE, 225))
        y += int(W * 0.115)

    # ---- Farbreihe ----
    if sw and cfg.get("swatch_img") is not None:
        s_img = fit(cfg["swatch_img"], int(W - 2 * M - W * 0.20), int(W * 0.095))
        sy = y
        canvas.alpha_composite(s_img, (M, sy))
        d = ImageDraw.Draw(canvas, "RGBA")
        fsw = F(F_MONO, W * 0.0160)
        lab = "6 FARBEN"
        lw = tw(d, lab, fsw, W * 0.003)
        draw_tracked(d, W - M - lw, sy + int(W * 0.032), lab, fsw, (*PINE, 165), W * 0.003)
        y += int(W * 0.135)

    # ---- Fussband ----
    d.rectangle([0, band_y, W, H], fill=PINE)
    d.line([(0, band_y), (W, band_y)], fill=(*WATER, 170), width=3)

    fp = F(F_DISP, W * 0.082)
    price = cfg["price"]
    d.text((M, band_y + band_h * 0.20), price, font=fp, fill=BONE)
    fpn = F(F_MONO, W * 0.0165)
    draw_tracked(d, M + 3, band_y + band_h * 0.20 + W * 0.090,
                 "INKL. MWST", fpn, (*BONE, 130), W * 0.003)

    fn = F(F_TEXT, W * 0.0235)
    price_w = tw(d, price, fp)
    avail = W - 2 * M - price_w - int(W * 0.06)
    for ln in cfg["trust"]:
        fn = fit_font(d, ln, F_TEXT, fn.size, avail, min_size=14)
    ny = band_y + band_h * 0.215
    for ln in cfg["trust"]:
        lw = tw(d, ln, fn)
        d.text((W - M - lw, ny), ln, font=fn, fill=(*BONE, 230))
        d.ellipse([W - M - lw - int(W * 0.026), ny + int(W * 0.0105),
                   W - M - lw - int(W * 0.026) + 7, ny + int(W * 0.0105) + 7],
                  fill=WATER)
        ny += int(W * 0.041)

    return canvas.convert("RGB")


# ---------- Quellen ----------
src = Image.open(os.path.join(BASE, "p1.png"))
hero = cutout(src.crop((659, 50, 932, 986)))
swatch = cutout(src.crop((0, 706, 627, 982)))
scene = cutout(src.crop((0, 43, 627, 680)))
hero.save(os.path.join(BASE, "hero.png"))
swatch.save(os.path.join(BASE, "swatch.png"))
scene.save(os.path.join(BASE, "scene.png"))

NOTES = [("l", 0.13, "01", "Napf"),
         ("r", 0.36, "02", "Knopf"),
         ("l", 0.74, "03", "550 ml")]

configs = [
    dict(size=(1080, 1350), band=0.165, hl_size=0.113, seed=7,
         topright="CH · 550 ML",
         headline=["EINE HAND.", "ER TRINKT."],
         sub=["Knopf drücken, Wasser läuft in den Napf.",
              "Der Rest läuft zurück in die Flasche."],
         hero=hero, notes=NOTES,
         features=[("01", "Einhand"), ("02", "Auslaufsicher"), ("03", "Rest zurück")],
         swatches=False, swatch_img=None,
         price="CHF 29.90",
         trust=["Gratisversand Schweiz", "14 Tage Rückgabe"],
         name="werbebild-feed-4x5.png"),

    dict(size=(1080, 1920), band=0.135, hl_size=0.108, seed=13,
         topright="SCHWEIZ · 550 ML",
         headline=["SCHLUSS MIT", "DER HOHLEN", "HAND."],
         sub=["Trinkflasche mit Napf, 550 ml.",
              "Einhandbedienung, damit die Leine bleibt."],
         hero=hero, notes=NOTES,
         features=[("01", "Einhand"), ("02", "Auslaufsicher"), ("03", "Rest zurück")],
         swatches=True, swatch_img=swatch,
         price="CHF 29.90",
         trust=["Gratisversand Schweiz", "14 Tage Rückgabe"],
         name="werbebild-story-9x16.png"),
]

for c in configs:
    img = build(c)
    p = os.path.join(OUT, c["name"])
    img.save(p, "PNG", optimize=True)
    print("gespeichert:", p, img.size)
