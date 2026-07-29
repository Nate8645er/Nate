#!/usr/bin/env python3
"""
Let'sDrink, Serie H.
Hochwertige Flaschen durch Umfaerbung der grossen Aufnahme.
Gezeichnete Hunde im Hintergrund, stehende und liegende Flaschen,
auslaufendes Wasser und Futter. Alles doppelt gerendert und verkleinert.
"""
import os, math, colorsys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/claude/ad"
OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)
FRED = f"{BASE}/Fredoka.ttf"
BALO = f"{BASE}/Baloo.ttf"
SS = 2  # Ueberabtastung


def F(p, s, inst=None):
    f = ImageFont.truetype(p, int(s))
    if inst:
        try: f.set_variation_by_name(inst)
        except Exception: pass
    return f
def tw(d, s, f): return d.textlength(s, font=f)
def fitf(d, s, path, start, maxw, inst=None, mn=16):
    sz = start; f = F(path, sz, inst)
    while tw(d, s, f) > maxw and sz > mn:
        sz -= 2; f = F(path, sz, inst)
    return f
def fitblock(d, lines, path, start, maxw, inst=None, mn=16):
    f = F(path, start, inst)
    for ln in lines:
        f2 = fitf(d, ln, path, f.size, maxw, inst, mn)
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
    if r > 1.03:
        out = out.filter(ImageFilter.UnsharpMask(radius=1.4, percent=80, threshold=3))
    return out


# ---------- Umfaerbung ----------
def recolor(img, mode, hue=None, sat=1.0, val=1.0):
    """Faerbt nur die gesaettigten Flaechen um, Glas und Weiss bleiben."""
    a = np.array(img.convert("RGBA")).astype(np.float32) / 255.0
    rgb, al = a[:, :, :3], a[:, :, 3]
    mx = rgb.max(axis=2); mn = rgb.min(axis=2)
    v = mx
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    sel = (s > 0.18) & (al > 0.2)
    if not sel.any():
        return img
    h = np.zeros_like(v)
    d_ = mx - mn
    idx = (mx == rgb[:, :, 0]) & (d_ > 0); h[idx] = ((rgb[:, :, 1] - rgb[:, :, 2])[idx] / d_[idx]) % 6
    idx = (mx == rgb[:, :, 1]) & (d_ > 0); h[idx] = ((rgb[:, :, 2] - rgb[:, :, 0])[idx] / d_[idx]) + 2
    idx = (mx == rgb[:, :, 2]) & (d_ > 0); h[idx] = ((rgb[:, :, 0] - rgb[:, :, 1])[idx] / d_[idx]) + 4
    h = h / 6.0
    if mode == "hue":
        h[sel] = hue
        s[sel] = np.clip(s[sel] * sat, 0, 1)
        v[sel] = np.clip(v[sel] * val, 0, 1)
    else:  # neutral
        s[sel] = s[sel] * 0.06
        v[sel] = np.clip(v[sel] * val, 0, 1)
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    out = np.zeros_like(rgb)
    for k, (r_, g_, b_) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        m = i == k
        out[:, :, 0][m] = r_[m]; out[:, :, 1][m] = g_[m]; out[:, :, 2][m] = b_[m]
    res = np.dstack([np.where(sel[..., None], out, rgb), al])
    return Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8), "RGBA")


COLORWAYS = [
    ("Türkis",  dict(mode="hue", hue=0.495, sat=1.00, val=1.00)),
    ("Mint",    dict(mode="hue", hue=0.395, sat=0.62, val=1.10)),
    ("Rosa",    dict(mode="hue", hue=0.955, sat=0.60, val=1.08)),
    ("Grau",    dict(mode="neutral", val=0.78)),
    ("Schwarz", dict(mode="neutral", val=0.30)),
    ("Weiss",   dict(mode="neutral", val=1.14)),
]


# ---------- Gezeichneter Hund ----------
def dog(size, col, stride=0):
    """Schlichte Seitenansicht, flaechig. stride variiert die Beinstellung."""
    W = size; H = int(size * 0.78)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = W / 100.0
    body = [12 * u, 30 * u, 66 * u, 58 * u]
    d.rounded_rectangle(body, radius=13 * u, fill=col)
    d.ellipse([60 * u, 18 * u, 88 * u, 46 * u], fill=col)              # Kopf
    d.rounded_rectangle([78 * u, 30 * u, 96 * u, 42 * u], radius=5 * u, fill=col)  # Schnauze
    d.polygon([(64 * u, 22 * u), (60 * u, 6 * u), (75 * u, 18 * u)], fill=col)     # Ohr
    s = stride
    for (lx, sw) in [(18, s), (30, -s), (50, -s), (60, s)]:
        d.rounded_rectangle([(lx + sw) * u, 52 * u, (lx + 9 + sw) * u, 76 * u],
                            radius=4 * u, fill=col)
    tail = [(12 * u, 34 * u), (4 * u, 24 * u), (2 * u, 12 * u)]
    d.line(tail, fill=col, width=int(6 * u), joint="curve")
    d.ellipse([1 * u, 8 * u, 7 * u, 14 * u], fill=col)
    return im


def cat(size, col, stride=0):
    """Schlichte Seitenansicht einer Katze, flaechig."""
    W = size; H = int(size * 0.78)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = W / 100.0
    d.rounded_rectangle([16 * u, 36 * u, 68 * u, 60 * u], radius=12 * u, fill=col)   # Koerper
    d.ellipse([62 * u, 24 * u, 86 * u, 48 * u], fill=col)                            # Kopf
    d.polygon([(65 * u, 27 * u), (63 * u, 11 * u), (75 * u, 22 * u)], fill=col)      # Ohr hinten
    d.polygon([(76 * u, 24 * u), (80 * u, 9 * u), (86 * u, 26 * u)], fill=col)       # Ohr vorne
    d.rounded_rectangle([80 * u, 34 * u, 92 * u, 43 * u], radius=4 * u, fill=col)    # Schnauze
    s = stride
    for (lx, sw) in [(22, s), (33, -s), (52, -s), (61, s)]:
        d.rounded_rectangle([(lx + sw) * u, 55 * u, (lx + 7 + sw) * u, 76 * u],
                            radius=3 * u, fill=col)
    d.line([(17 * u, 40 * u), (6 * u, 30 * u), (5 * u, 14 * u), (14 * u, 7 * u)],
           fill=col, width=int(5 * u), joint="curve")                                # Schwanz
    return im


# ---------- Verschuettetes ----------
def rot_point(px, py, w, h, ang, W2, H2):
    """Wo landet ein Punkt nach img.rotate(ang, expand=True)?"""
    t = math.radians(ang)
    dx, dy = px - w / 2.0, py - h / 2.0
    return (dx * math.cos(t) + dy * math.sin(t) + W2 / 2.0,
            -dx * math.sin(t) + dy * math.cos(t) + H2 / 2.0)


def _ell(d, x0, y0, x1, y1, fill):
    d.ellipse([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], fill=fill)


def water_spill(d, ox, oy, w, sgn, col_dark, col_main, col_light):
    """Wasser laeuft aus der Oeffnung bei (ox,oy) in Richtung sgn und sammelt sich."""
    h = w * 0.26
    _ell(d, ox - sgn * w * 0.05, oy - h * 0.22, ox + sgn * w * 0.30, oy + h * 0.34, col_main)
    _ell(d, ox + sgn * w * 0.12, oy + h * 0.04, ox + sgn * w * 1.00, oy + h * 1.00, col_dark)
    _ell(d, ox + sgn * w * 0.18, oy + h * 0.02, ox + sgn * w * 0.94, oy + h * 0.86, col_main)
    _ell(d, ox + sgn * w * 0.40, oy + h * 0.20, ox + sgn * w * 0.66, oy + h * 0.46, col_light)
    for (dx, dy, r) in [(1.16, 0.30, 0.050), (1.30, 0.58, 0.034), (1.40, 0.26, 0.026)]:
        cx = ox + sgn * w * dx
        _ell(d, cx - w * r, oy + h * dy, cx + w * r, oy + h * dy + w * r * 2, col_main)


def kibble_spill(d, ox, oy, w, sgn, cols, hi, seed=3):
    """Trockenfutter faellt aus der Oeffnung und liegt in Richtung sgn."""
    rng = random.Random(seed)
    for i in range(12):
        t = rng.uniform(0.05, 1.05)
        px = ox + sgn * w * t
        py = oy + w * 0.10 + rng.uniform(-w * 0.03, w * 0.10) + w * 0.13 * (t ** 1.6)
        sz = w * rng.uniform(0.032, 0.055)
        c = rng.choice(cols)
        d.polygon([(px, py - sz), (px + sz * 0.95, py + sz * 0.58), (px - sz * 0.95, py + sz * 0.58)], fill=c)
        d.ellipse([px - sz * 0.34, py - sz * 0.24, px + sz * 0.34, py + sz * 0.42], fill=c)
        d.ellipse([px - sz * 0.30, py - sz * 0.52, px - sz * 0.04, py - sz * 0.24], fill=hi)


def grad(size, top, bot, noise=2.4, seed=3):
    w, h = size
    y = np.linspace(0, 1, h)[:, None, None]
    arr = np.repeat(np.array(top, float) * (1 - y) + np.array(bot, float) * y, w, axis=1)
    arr += np.repeat(np.random.default_rng(seed).normal(0, noise, (h, w, 1)), 3, axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def soft_shadow(canvas, img, x, y, blur, op, col, dy):
    p = blur * 2
    s = Image.new("RGBA", (img.width + p * 2, img.height + p * 2), (0, 0, 0, 0))
    s.paste(img, (p, p), img); s = s.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(s); a[:, :, :3] = np.array(col); a[:, :, 3] = (a[:, :, 3] * op).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(a, "RGBA"), (x - p, y - p + dy))


# ---------- Quelle ----------
src = Image.open(f"{BASE}/p1.png")
hero_raw = cutout(src.crop((659, 50, 932, 986)))
BOTTLES = [(n, recolor(hero_raw, **kw)) for n, kw in COLORWAYS]


def build(cfg):
    W, H = cfg["size"][0] * SS, cfg["size"][1] * SS
    M = int(W * 0.072)
    P = cfg["palette"]
    c = grad((W, H), P["bg_top"], P["bg_bot"], 2.2, cfg["seed"])
    d = ImageDraw.Draw(c, "RGBA")

    # Grossform
    r = int(W * 0.30)
    d.ellipse([W - r * 0.70, -r * 0.40, W + r * 1.10, r * 1.60], fill=P["blob"])

    # Bodenlinie
    ground = int(H * cfg["ground"])
    d.ellipse([-W * 0.20, ground - int(H * 0.055), W * 1.20, ground + int(H * 0.30)],
              fill=P["ground"])

    # Gezeichnete Hunde im Hintergrund
    for entry in cfg["dogs"]:
        fx, fy, fs, op, stride = entry[:5]
        kind = entry[5] if len(entry) > 5 else "dog"
        fig = (cat if kind == "cat" else dog)(int(W * fs), (*P["dog"], op), stride)
        c.alpha_composite(fig, (int(W * fx - fig.width / 2), int(H * fy - fig.height)))
    d = ImageDraw.Draw(c, "RGBA")

    # Marke
    d.text((M, int(H * 0.038)), "Let'sDrink", font=F(FRED, W * 0.026, "SemiBold"), fill=P["ink"])

    text_max_w = W - 2 * M

    # Titel
    y = int(H * 0.038) + int(W * 0.052)
    fh = fitblock(d, cfg["head"], BALO, W * cfg["head_size"], text_max_w, "ExtraBold")
    for ln in cfg["head"]:
        d.text((M, y), ln, font=fh, fill=P["ink"]); y += int(fh.size * 0.95)
    y += int(W * 0.012)
    fs_ = fitblock(d, cfg["sub"], FRED, W * 0.0275, text_max_w, "Medium")
    for ln in cfg["sub"]:
        d.text((M, y), ln, font=fs_, fill=P["ink2"]); y += int(W * 0.040)
    text_bottom = y

    band_h = int(H * 0.092)
    band_y = H - band_h

    # ---- Liegende Flaschen mit Inhalt ----
    lay_h = int(W * 0.115)
    ly = ground - int(lay_h * 0.35)
    for spec in cfg["lying"]:
        name, bimg = BOTTLES[spec["i"]]
        b = fit(bimg, int(W * 0.42), lay_h)
        rot = b.rotate(spec["rot"], resample=Image.BICUBIC, expand=True)
        bx = int(W * spec["x"]) - rot.width // 2
        by = ly - rot.height // 2
        # Die Oeffnung sitzt im aufrechten Bild oben in der Mitte
        ox_r, oy_r = rot_point(b.width * 0.5, b.height * 0.06, b.width, b.height,
                               spec["rot"], rot.width, rot.height)
        ox, oy = bx + ox_r, by + oy_r
        # Richtung: von der Flaschenmitte zur Oeffnung
        sgn = 1.0 if ox_r >= rot.width / 2 else -1.0
        oy = max(oy, ly - lay_h * 0.10)
        if spec["type"] == "water":
            water_spill(d, ox, oy, W * 0.105, sgn, P["water_d"], P["water"], P["water_l"])
        else:
            kibble_spill(d, ox, oy, W * 0.115, sgn, P["kibble"], P["kibble_hi"], seed=spec["i"] + 4)
        soft_shadow(c, rot, bx, by, int(14 * SS), 0.20, P["shadow"], int(8 * SS))
        c.alpha_composite(rot, (bx, by))
        d = ImageDraw.Draw(c, "RGBA")

    # ---- Stehende Flaschen ----
    stand_zone_top = text_bottom + int(H * 0.020)
    stand_h = min(int(H * 0.315), ly - int(lay_h * 0.55) - stand_zone_top)
    n = len(cfg["standing"])
    gap = int(W * 0.013)
    imgs = [fit(BOTTLES[i][1], int(W * 0.155), stand_h) for i in cfg["standing"]]
    avail = W - 2 * M
    total = sum(i.width for i in imgs) + gap * (n - 1)
    if total > avail:
        k = (avail - gap * (n - 1)) / max(1, sum(i.width for i in imgs))
        imgs = [i.resize((max(1, int(i.width * k)), max(1, int(i.height * k))), Image.LANCZOS) for i in imgs]
        total = sum(i.width for i in imgs) + gap * (n - 1)
    print(f"      Reihe {n} Flaschen, Breite {total} von {avail} verfuegbar")
    x = W / 2 - total / 2
    for k, im in enumerate(imgs):
        rot = -4 if k % 2 == 0 else 4
        lay = Image.new("RGBA", (im.width + 60, im.height + 60), (0, 0, 0, 0))
        lay.paste(im, (30, 30), im)
        lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
        yy = ly - int(lay_h * 0.55) - lay.height + int(30)
        soft_shadow(c, lay, int(x) - 30, yy, int(15 * SS), 0.22, P["shadow"], int(10 * SS))
        c.alpha_composite(lay, (int(x) - 30, yy))
        x += im.width + gap
    d = ImageDraw.Draw(c, "RGBA")

    # ---- Fuss: Preis links, Angaben rechts ----
    d.rectangle([0, band_y, W, H], fill=P["band"])
    fp = F(BALO, W * 0.046, "ExtraBold")
    ptxt = "CHF 29.90"
    pw_ = tw(d, ptxt, fp)
    d.text((M, band_y + (band_h - fp.size * 1.32) / 2), ptxt, font=fp, fill=P["band_ink"])
    avail_f = W - 2 * M - pw_ - int(W * 0.045)
    fbt = fitf(d, cfg["footer"], FRED, W * 0.0235, avail_f, "Medium")
    lw = tw(d, cfg["footer"], fbt)
    d.text((W - M - lw, band_y + (band_h - fbt.size * 1.35) / 2), cfg["footer"],
           font=fbt, fill=P["band_ink"])
    print(f"      Fuss: Preis {int(pw_)//SS}px, Text {int(lw)//SS}px, Luecke "
          f"{int(W - 2*M - pw_ - lw)//SS}px")

    print(f"   {cfg['name']:26s} Text {text_bottom//SS:4d} | stehend ab {(ly - int(lay_h*0.55) - stand_h)//SS:4d} | Boden {ground//SS:4d}")
    return c.resize(cfg["size"], Image.LANCZOS).convert("RGB")


SONNE = dict(bg_top=(255, 240, 206), bg_bot=(255, 218, 168), blob=(255, 201, 100),
             ground=(250, 205, 140), dog=(226, 160, 78), ink=(58, 40, 24), ink2=(108, 78, 50),
             water_d=(58, 150, 178), water=(104, 194, 216), water_l=(206, 240, 248),
             kibble=[(158, 102, 54), (134, 84, 44), (178, 121, 68)], kibble_hi=(206, 158, 106),
             shadow=(130, 90, 46), price_bg=(43, 60, 48), price_ink=(255, 250, 236),
             band=(43, 60, 48), band_ink=(255, 247, 230))

WASSER = dict(bg_top=(219, 246, 248), bg_bot=(166, 226, 233), blob=(130, 211, 221),
              ground=(150, 218, 226), dog=(92, 180, 194), ink=(16, 62, 71), ink2=(38, 98, 108),
              water_d=(40, 126, 152), water=(86, 178, 202), water_l=(198, 236, 246),
              kibble=[(158, 102, 54), (134, 84, 44), (178, 121, 68)], kibble_hi=(206, 158, 106),
              shadow=(34, 96, 106), price_bg=(255, 176, 79), price_ink=(46, 34, 14),
              band=(16, 82, 94), band_ink=(226, 246, 248))

PICKNICK = dict(bg_top=(255, 235, 223), bg_bot=(255, 208, 188), blob=(255, 190, 164),
                ground=(252, 205, 182), dog=(226, 142, 110), ink=(74, 34, 24), ink2=(124, 68, 52),
                water_d=(62, 152, 176), water=(110, 196, 214), water_l=(208, 240, 248),
                kibble=[(158, 102, 54), (134, 84, 44), (178, 121, 68)], kibble_hi=(206, 158, 106),
                shadow=(146, 76, 54), price_bg=(38, 92, 84), price_ink=(255, 248, 240),
                band=(38, 92, 84), band_ink=(255, 240, 232))

VARIANTS = [
    dict(name="ad-H1-sonnentag.png", size=(1080, 1350), palette=SONNE, seed=301,
         head_size=0.082, ground=0.795,
         head=["Für Hund", "und Katze."],
         sub=["Knopf drücken, der Napf füllt sich, dein Tier trinkt.",
              "Für die Pause gibst du eine Portion Trockenfutter hinein."],
         standing=[0, 1, 2, 3, 4, 5], lying=[dict(i=4, x=0.20, rot=76, type="water"),
                                       dict(i=5, x=0.79, rot=-72, type="food")],
         dogs=[(0.13, 0.775, 0.20, 60, 3, "dog"), (0.49, 0.766, 0.14, 44, -3, "cat"), (0.87, 0.780, 0.21, 52, 2, "dog")],
         price_x=0.845, price_y=0.300, price_rot=-7,
         footer="550 ml  ·  für Hund und Katze  ·  Gratisversand Schweiz"),

    dict(name="ad-H2-wassertag.png", size=(1080, 1350), palette=WASSER, seed=312,
         head_size=0.080, ground=0.795,
         head=["Eine Flasche", "für beide."],
         sub=["Wasser für unterwegs, Futter für die Pause.",
              "Für Hund und Katze, in sechs Farben."],
         standing=[3, 0, 5, 1, 4, 2], lying=[dict(i=2, x=0.19, rot=72, type="food"),
                                       dict(i=5, x=0.80, rot=-78, type="water")],
         dogs=[(0.12, 0.780, 0.21, 55, -3, "dog"), (0.47, 0.768, 0.15, 42, 3, "cat"), (0.88, 0.774, 0.17, 58, 2, "cat")],
         price_x=0.840, price_y=0.295, price_rot=6,
         footer="6 Farben  ·  für Hund und Katze  ·  14 Tage Rückgabe"),

    dict(name="ad-H3-picknick.png", size=(1080, 1350), palette=PICKNICK, seed=323,
         head_size=0.078, ground=0.795,
         head=["Trinken und", "fressen, überall."],
         sub=["Der angebaute Napf nimmt Wasser und Trockenfutter.",
              "Für Hund und Katze, eine Hand genügt."],
         standing=[5, 2, 0, 1, 3, 4], lying=[dict(i=3, x=0.20, rot=80, type="water"),
                                       dict(i=4, x=0.79, rot=-70, type="food")],
         dogs=[(0.15, 0.778, 0.15, 58, 2, "cat"), (0.51, 0.764, 0.19, 42, -3, "dog"), (0.87, 0.782, 0.21, 50, 3, "dog")],
         price_x=0.845, price_y=0.305, price_rot=-9,
         footer="Für Hund und Katze  ·  Wasser und Futter  ·  Versand aus der Schweiz"),
]

for v in VARIANTS:
    build(v).save(os.path.join(OUT, v["name"]), "PNG", optimize=True)
print("fertig")
