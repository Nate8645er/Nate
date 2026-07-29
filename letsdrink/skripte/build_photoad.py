#!/usr/bin/env python3
"""
Werbeebene ueber die generierten Fotos.
Kopfzeile, fette Schlagzeile, Beschreibung, Preisleiste mit Knopf.
Doppelt gerendert, dann verkleinert.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/claude/ad"
GEN = f"{BASE}/gen"
OUT = "/mnt/user-data/outputs"
ARCH = f"{BASE}/Archivo.ttf"
INTR = f"{BASE}/Inter.ttf"
SS = 2

INK   = (20, 30, 25)
BONE  = (253, 251, 247)
ACC   = (34, 138, 156)
DARK  = (18, 34, 29)


def F(p, s, inst=None):
    f = ImageFont.truetype(p, int(s))
    if inst:
        try: f.set_variation_by_name(inst)
        except Exception: pass
    return f
def tw(d, s, f, tr=0.0): return sum(d.textlength(ch, font=f) for ch in s) + tr * max(0, len(s) - 1)
def trk(d, x, y, s, f, fill, tr=0.0):
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + tr
    return x
def fitf(d, s, path, start, maxw, inst=None, tr=0.0, mn=18):
    sz = start; f = F(path, sz, inst)
    while tw(d, s, f, tr) > maxw and sz > mn:
        sz -= 2; f = F(path, sz, inst)
    return f
def fitblock(d, lines, path, start, maxw, inst=None, tr=0.0, mn=18):
    f = F(path, start, inst)
    for ln in lines:
        f2 = fitf(d, ln, path, f.size, maxw, inst, tr, mn)
        if f2.size < f.size: f = f2
    return f


def cover(img, W, H):
    r = max(W / img.width, H / img.height)
    im = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = (im.width - W) // 2; y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def scrim(size, height_frac, col, max_alpha):
    """Weicher Verlauf von unten, damit heller Text sicher lesbar bleibt."""
    W, H = size
    h = int(H * height_frac)
    a = np.zeros((h, W, 4), dtype=np.uint8)
    a[:, :, 0], a[:, :, 1], a[:, :, 2] = col
    ramp = (np.linspace(0, max_alpha, h) ** 1.35)
    ramp = ramp / ramp.max() * max_alpha
    a[:, :, 3] = ramp[:, None].astype(np.uint8)
    return Image.fromarray(a, "RGBA"), H - h


def build(cfg):
    W, H = cfg["out"][0] * SS, cfg["out"][1] * SS
    M = int(W * 0.072)
    base = cover(Image.open(cfg["src"]).convert("RGB"), W, H).convert("RGBA")
    c = base
    d = ImageDraw.Draw(c, "RGBA")

    # Sanfte Aufhellung oben, damit dunkler Text sicher sitzt
    top_h = int(H * 0.40)
    lift = np.zeros((top_h, W, 4), dtype=np.uint8)
    lift[:, :, 0], lift[:, :, 1], lift[:, :, 2] = (255, 252, 246)
    ramp = np.linspace(105, 0, top_h) ** 1.2
    lift[:, :, 3] = (ramp / ramp.max() * 105).astype(np.uint8)[:, None]
    c.alpha_composite(Image.fromarray(lift, "RGBA"), (0, 0))
    d = ImageDraw.Draw(c, "RGBA")

    # Kopfzeile
    fk = F(INTR, W * 0.0195, "SemiBold")
    trk(d, M, int(H * 0.042), "LET'SDRINK", fk, (*INK, 225), W * 0.0055)
    kw = tw(d, "LET'SDRINK", fk, W * 0.0055)
    d.line([(M, int(H * 0.042) + int(W * 0.032)), (M + kw, int(H * 0.042) + int(W * 0.032))],
           fill=(*INK, 80), width=2)

    # Schlagzeile, fett und gross
    y = int(H * 0.042) + int(W * 0.062)
    fh = fitblock(d, cfg["head"], ARCH, W * cfg["hs"], W - 2 * M, "ExtraBold", tr=-W * 0.0012)
    for ln in cfg["head"]:
        trk(d, M, y, ln, fh, INK, -fh.size * 0.014)
        y += int(fh.size * 1.02)

    # Beschreibung
    y += int(W * 0.016)
    fs = fitblock(d, cfg["sub"], INTR, W * 0.0300, W * 0.76, "Medium")
    for ln in cfg["sub"]:
        d.text((M, y), ln, font=fs, fill=(*INK, 205))
        y += int(W * 0.046)
    text_bottom = y

    # Preisleiste unten
    sc, sy = scrim((W, H), 0.34, DARK, 232)
    c.alpha_composite(sc, (0, sy))
    d = ImageDraw.Draw(c, "RGBA")

    fp = F(ARCH, W * 0.072, "ExtraBold")
    ptxt = cfg["price"]
    pw = tw(d, ptxt, fp)
    py = H - int(H * 0.150)
    d.text((M, py), ptxt, font=fp, fill=BONE)

    fn = F(INTR, W * 0.0235, "Medium")
    note = cfg["note"]
    fn = fitf(d, note, INTR, fn.size, W * 0.50, "Medium")
    d.text((M + 3, py + int(W * 0.078)), note, font=fn, fill=(*BONE, 190))

    # Knopf
    fb = F(INTR, W * 0.0265, "SemiBold")
    btxt = cfg["cta"]
    bw = tw(d, btxt, fb) + int(W * 0.085)
    bh = int(W * 0.078)
    bx, by = W - M - bw, py + int(W * 0.010)
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=int(bh / 2), fill=ACC)
    d.text((bx + (bw - tw(d, btxt, fb)) / 2, by + (bh - fb.size * 1.30) / 2),
           btxt, font=fb, fill=BONE)

    # Angaben ueber der Leiste
    fi = F(INTR, W * 0.0225, "Medium")
    info = cfg["info"]
    fi = fitf(d, info, INTR, fi.size, W - 2 * M, "Medium")
    d.text((M, py - int(W * 0.052)), info, font=fi, fill=(*BONE, 210))

    print(f"   {cfg['name']:30s} Text bis {text_bottom//SS:4d} | Leiste ab {sy//SS:4d} | "
          f"Knopf x {bx//SS}-{(bx+bw)//SS} | Preis bis {int(M+pw)//SS}")
    return c.resize(cfg["out"], Image.LANCZOS).convert("RGB")


VARIANTS = [
    dict(name="ad-FOTO-1-farben.png", src=f"{GEN}/g1.png", out=(1080, 1350), hs=0.078,
         head=["SECHS FARBEN.", "FÜR HUND", "UND KATZE."],
         sub=["Knopf drücken, der Napf füllt sich, dein Tier trinkt.",
              "Der Rest läuft zurück in die Flasche."],
         info="550 ml  ·  Wasser und Futter  ·  auslaufsicher verschlossen",
         price="CHF 29.90", note="inkl. MwSt, Gratisversand Schweiz", cta="Jetzt kaufen"),

    dict(name="ad-FOTO-2-wasser-futter.png", src=f"{GEN}/g2.png", out=(1080, 1350), hs=0.080,
         head=["WASSER REIN.", "FUTTER REIN.", "FERTIG."],
         sub=["Ein Napf für beides. Auf der Wanderung Wasser,",
              "in der Pause eine Portion Trockenfutter."],
         info="Einhandbedienung  ·  550 ml  ·  sechs Farben",
         price="CHF 29.90", note="2er-Set CHF 49.00", cta="Mehr dazu"),
]

for v in VARIANTS:
    build(v).save(os.path.join(OUT, v["name"]), "PNG", optimize=True)
print("fertig")
