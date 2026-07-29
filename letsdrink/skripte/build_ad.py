#!/usr/bin/env python3
"""
Let'sDrink Werbebild-Generator.
Baut Anzeigen-Creatives aus dem echten Produktfoto.
Formate: 4:5 (Meta Feed) und 9:16 (Stories, Reels, TikTok).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/claude/ad"
OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

# ---------- Palette: "Trail Heat" ----------
SAND      = (239, 231, 218)   # sonnengebleichter Weg
SAND_DEEP = (226, 215, 198)
PINE      = (26, 54, 43)      # tiefes Tannengrün
PINE_SOFT = (38, 74, 60)
WATER     = (46, 150, 168)    # der einzige kühle Ton
BONE      = (250, 247, 241)
INK       = (23, 33, 28)

F_DISPLAY = os.path.join(BASE, "Anton.ttf")
F_TEXT    = os.path.join(BASE, "Inter.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def text_size(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]


def tracked(draw, xy, s, f, fill, track=0):
    """Text mit manueller Laufweite."""
    x, y = xy
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + track
    return x - xy[0]


def tracked_width(draw, s, f, track=0):
    w = sum(draw.textlength(c, font=f) for c in s)
    return w + track * (len(s) - 1)


# ---------- Produkt freistellen ----------
def cutout(path, tol=238, feather=1.2):
    im = Image.open(path).convert("RGB")
    a = np.array(im).astype(np.int16)
    # alles was in allen Kanaelen nahe weiss ist -> transparent
    near_white = (a[:, :, 0] > tol) & (a[:, :, 1] > tol) & (a[:, :, 2] > tol)
    alpha = np.where(near_white, 0, 255).astype(np.uint8)
    mask = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(feather))
    # harte Kanten leicht nachziehen, damit kein weisser Saum bleibt
    mask = mask.point(lambda v: 0 if v < 60 else min(255, int(v * 1.35)))
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out.crop(out.getbbox())


def fit(img, box_w, box_h):
    r = min(box_w / img.width, box_h / img.height)
    return img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))), Image.LANCZOS)


# ---------- Textur ----------
def grain(size, strength=7, seed=4):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, strength, (size[1], size[0], 1))
    n = np.repeat(n, 3, axis=2)
    return n


def paper(size):
    """Warmer Verlauf plus feines Korn plus Raster."""
    w, h = size
    y = np.linspace(0, 1, h)[:, None, None]
    top = np.array(SAND, dtype=float)
    bot = np.array(SAND_DEEP, dtype=float)
    arr = top * (1 - y) + bot * y
    arr = np.repeat(arr, w, axis=1)
    arr = arr + grain(size)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")

    grid = Image.new("RGBA", size, (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    step = 54
    for x in range(0, w, step):
        g.line([(x, 0), (x, h)], fill=(*INK, 8), width=1)
    for yy in range(0, h, step):
        g.line([(0, yy), (w, yy)], fill=(*INK, 8), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), grid)
    return img


# ---------- Massstab-Motiv ----------
def scale_bar(draw, x, y, w, ticks=11, col=INK, alpha=70):
    """Feine technische Skala. Referenz auf 550 ml."""
    draw.line([(x, y), (x + w, y)], fill=(*col, alpha), width=2)
    for i in range(ticks):
        tx = x + w * i / (ticks - 1)
        long = (i % 5 == 0)
        draw.line([(tx, y), (tx, y + (16 if long else 8))],
                  fill=(*col, alpha + (40 if long else 0)), width=2)


# ---------- Creative ----------
def build(size, product, headline, sub, kicker, price, notes, filename):
    W, H = size
    canvas = paper(size)
    d = ImageDraw.Draw(canvas, "RGBA")

    M = int(W * 0.085)          # Aussenrand
    vertical = H / W > 1.5

    # ----- Wasserkreis hinter dem Produkt -----
    cx = W // 2
    circle_r = int(W * (0.40 if vertical else 0.44))
    cy = int(H * (0.545 if vertical else 0.56))
    d.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r],
              fill=(*WATER, 26))
    d.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r],
              outline=(*WATER, 90), width=2)
    inner = int(circle_r * 0.72)
    d.ellipse([cx - inner, cy - inner, cx + inner, cy + inner],
              outline=(*WATER, 45), width=1)

    # ----- Kicker oben -----
    fk = font(F_TEXT, int(W * 0.0225))
    kw = tracked_width(d, kicker, fk, track=W * 0.0042)
    tracked(d, (cx - kw / 2, M), kicker, fk, (*PINE, 235), track=W * 0.0042)
    d_y = M + int(W * 0.055)
    d.line([(cx - kw / 2, d_y), (cx + kw / 2, d_y)], fill=(*PINE, 60), width=1)

    # ----- Headline -----
    hl_size = int(W * (0.118 if vertical else 0.125))
    fh = font(F_DISPLAY, hl_size)
    lines = headline
    y = M + int(W * 0.105)
    line_h = int(hl_size * 0.93)
    for ln in lines:
        w_, _ = text_size(d, ln, fh)
        # Sicherung: nie ueber den Rand
        s = hl_size
        while w_ > W - 2 * M and s > 20:
            s -= 2
            fh = font(F_DISPLAY, s)
            w_, _ = text_size(d, ln, fh)
        d.text((cx - w_ / 2, y), ln, font=fh, fill=PINE)
        y += line_h
    fh = font(F_DISPLAY, hl_size)

    # ----- Subline -----
    fs = font(F_TEXT, int(W * 0.0325))
    y += int(W * 0.012)
    for ln in sub:
        w_, _ = text_size(d, ln, fs)
        d.text((cx - w_ / 2, y), ln, font=fs, fill=(*INK, 205))
        y += int(W * 0.048)

    # ----- Produkt -----
    max_w = int(W * 0.78)
    max_h = int(H * (0.40 if vertical else 0.42))
    p = fit(product, max_w, max_h)
    px = cx - p.width // 2
    py = cy - p.height // 2 + int(H * 0.01)

    # weicher Schatten
    sh = Image.new("RGBA", (p.width + 80, p.height + 80), (0, 0, 0, 0))
    sh.paste(p, (40, 40), p)
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    sh_a = np.array(sh)
    sh_a[:, :, :3] = np.array(PINE)
    sh_a[:, :, 3] = (sh_a[:, :, 3] * 0.30).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(sh_a, "RGBA"), (px - 40, py - 28))
    canvas.alpha_composite(p, (px, py))
    d = ImageDraw.Draw(canvas, "RGBA")

    # ----- Massstab + Volumenlabel -----
    bar_w = int(W * 0.20)
    bar_y = py + p.height + int(H * 0.028)
    if bar_y < H - int(H * 0.30):
        scale_bar(d, cx - bar_w / 2, bar_y, bar_w)
        fv = font(F_TEXT, int(W * 0.0215))
        vw = tracked_width(d, "550 ML", fv, track=W * 0.004)
        tracked(d, (cx - vw / 2, bar_y + int(W * 0.038)), "550 ML", fv,
                (*INK, 150), track=W * 0.004)

    # ----- Fussband -----
    band_h = int(H * (0.175 if vertical else 0.20))
    by = H - band_h
    d.rectangle([0, by, W, H], fill=PINE)
    d.line([(0, by), (W, by)], fill=(*WATER, 150), width=3)

    # Preis
    fp = font(F_DISPLAY, int(W * 0.088))
    pw, ph = text_size(d, price, fp)
    price_y = by + int(band_h * 0.20)
    d.text((M, price_y), price, font=fp, fill=BONE)

    # Preis-Zusatz
    fpn = font(F_TEXT, int(W * 0.021))
    d.text((M + 2, price_y + int(W * 0.098)), "inkl. MwSt", font=fpn,
           fill=(*BONE, 150))

    # Hinweise rechts
    fn = font(F_TEXT, int(W * 0.0235))
    ny = price_y + int(W * 0.004)
    for ln in notes:
        w_, _ = text_size(d, ln, fn)
        d.text((W - M - w_, ny), ln, font=fn, fill=(*BONE, 225))
        # feiner Punkt als Aufzaehlung
        d.ellipse([W - M - w_ - int(W * 0.028), ny + int(W * 0.011),
                   W - M - w_ - int(W * 0.028) + 6, ny + int(W * 0.011) + 6],
                  fill=WATER)
        ny += int(W * 0.042)

    return canvas.convert("RGB")


# ---------- Rendern ----------
product = cutout(os.path.join(BASE, "p1.png"))

variants = [
    dict(
        size=(1080, 1350),
        headline=["EINE HAND.", "ER TRINKT."],
        sub=["Knopf drücken, Wasser läuft in den Napf.",
             "Der Rest läuft zurück in die Flasche."],
        kicker="LET'SDRINK · FÜR UNTERWEGS",
        price="CHF 29.90",
        notes=["Gratisversand Schweiz", "14 Tage Rückgabe", "Auslaufsicher verschlossen"],
        filename="werbebild-feed-4x5.png",
    ),
    dict(
        size=(1080, 1920),
        headline=["SCHLUSS MIT", "DER HOHLEN", "HAND."],
        sub=["Trinkflasche mit Napf, 550 ml.",
             "Einhandbedienung, damit die Leine bleibt."],
        kicker="LET'SDRINK · SCHWEIZ",
        price="CHF 29.90",
        notes=["Gratisversand Schweiz", "14 Tage Rückgabe"],
        filename="werbebild-story-9x16.png",
    ),
]

for v in variants:
    img = build(v["size"], product, v["headline"], v["sub"],
                v["kicker"], v["price"], v["notes"], v["filename"])
    path = os.path.join(OUT, v["filename"])
    img.save(path, "PNG", optimize=True)
    print("gespeichert:", path, img.size)
