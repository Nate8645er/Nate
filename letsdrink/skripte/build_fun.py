#!/usr/bin/env python3
"""
Let'sDrink, verspielte Serie "Sonntagsrunde".
Hund gross, Sprechblase, lebendige Hintergruende, runde Schrift.
"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = "/home/claude/ad"
OUT = "/mnt/user-data/outputs"
os.makedirs(OUT, exist_ok=True)

FRED = f"{BASE}/Fredoka.ttf"
BALO = f"{BASE}/Baloo.ttf"


def F(path, size, inst=None):
    f = ImageFont.truetype(path, int(size))
    if inst:
        try: f.set_variation_by_name(inst)
        except Exception: pass
    return f


def tw(d, s, f): return d.textlength(s, font=f)

def fitf(d, s, path, start, maxw, inst=None, mn=14):
    sz = start
    f = F(path, sz, inst)
    while tw(d, s, f) > maxw and sz > mn:
        sz -= 2; f = F(path, sz, inst)
    return f

def fitblock(d, lines, path, start, maxw, inst=None, mn=14):
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
    if r > 1.05:
        out = out.filter(ImageFilter.UnsharpMask(radius=1.5, percent=85, threshold=3))
    return out


def soft_shadow(canvas, img, x, y, blur=34, op=0.22, col=(60, 50, 40), dy=22):
    p = blur * 2
    s = Image.new("RGBA", (img.width + p * 2, img.height + p * 2), (0, 0, 0, 0))
    s.paste(img, (p, p), img); s = s.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(s); a[:, :, :3] = np.array(col); a[:, :, 3] = (a[:, :, 3] * op).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(a, "RGBA"), (x - p, y - p + dy))


# ---------- Spielerische Formen ----------
def paw(d, x, y, s, col, rot=0):
    """Pfotenabdruck aus fünf Ellipsen."""
    lay = Image.new("RGBA", (int(s * 2.4), int(s * 2.4)), (0, 0, 0, 0))
    dd = ImageDraw.Draw(lay)
    cx, cy = s * 1.2, s * 1.35
    dd.ellipse([cx - s * 0.62, cy - s * 0.50, cx + s * 0.62, cy + s * 0.62], fill=col)
    for a in (-58, -20, 20, 58):
        ax = cx + math.cos(math.radians(a - 90)) * s * 0.95
        ay = cy + math.sin(math.radians(a - 90)) * s * 0.95
        dd.ellipse([ax - s * 0.27, ay - s * 0.33, ax + s * 0.27, ay + s * 0.33], fill=col)
    if rot: lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    return lay, (int(x - lay.width / 2), int(y - lay.height / 2))


def droplet(d, x, y, s, col):
    d.ellipse([x - s * 0.5, y - s * 0.25, x + s * 0.5, y + s * 0.75], fill=col)
    d.polygon([(x, y - s * 0.95), (x - s * 0.42, y + s * 0.10), (x + s * 0.42, y + s * 0.10)], fill=col)


def dashed_arc(d, cx, cy, rx, ry, a0, a1, col, width=6, dash=16, gap=14):
    n = 420
    seg, on, acc = [], True, 0
    prev = None
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        p = (cx + rx * math.cos(math.radians(t)), cy + ry * math.sin(math.radians(t)))
        if prev:
            dist = math.dist(prev, p); acc += dist
            if on: seg.append((prev, p))
            if on and acc >= dash: on, acc = False, 0
            elif not on and acc >= gap: on, acc = True, 0
        prev = p
    for a, b in seg:
        d.line([a, b], fill=col, width=width)


def bubble(d, x, y, w, h, col, tail_dx=0.30, radius=None, outline=None):
    r = radius or int(h * 0.42)
    d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=col,
                        outline=outline, width=4 if outline else 0)
    tx = x + w * tail_dx
    d.polygon([(tx, y + h - 4), (tx + w * 0.10, y + h - 4), (tx + w * 0.02, y + h + h * 0.30)], fill=col)


def confetti(d, W, H, cols, n=26, seed=5, avoid=None):
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.randint(int(W * 0.04), int(W * 0.96)), rng.randint(int(H * 0.05), int(H * 0.92))
        if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
            continue
        s = rng.randint(int(W * 0.006), int(W * 0.013))
        c = rng.choice(cols)
        if rng.random() < 0.5:
            d.ellipse([x, y, x + s, y + s], fill=c)
        else:
            lay = Image.new("RGBA", (s * 3, s * 3), (0, 0, 0, 0))
            ImageDraw.Draw(lay).rectangle([s, s * 1.2, s * 2, s * 1.6], fill=c)


def grad(size, top, bot, noise=3.0, seed=3):
    w, h = size
    y = np.linspace(0, 1, h)[:, None, None]
    arr = np.repeat(np.array(top, float) * (1 - y) + np.array(bot, float) * y, w, axis=1)
    arr += np.repeat(np.random.default_rng(seed).normal(0, noise, (h, w, 1)), 3, axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ---------- Aufbau ----------
def build(cfg, scene, hero):
    W, H = cfg["size"]
    M = int(W * 0.075)
    P = cfg["palette"]
    c = grad((W, H), P["bg_top"], P["bg_bot"], 3.0, cfg["seed"])
    d = ImageDraw.Draw(c, "RGBA")

    # Grosse Formen
    if cfg["shape"] == "sun":
        r = int(W * 0.30)
        d.ellipse([W - r * 0.75, -r * 0.35, W + r * 1.05, r * 1.65], fill=P["blob"])
        for i in range(9):
            a = -18 + i * 13
            x0 = W * 0.86 + math.cos(math.radians(a)) * r * 1.15
            y0 = H * 0.055 + math.sin(math.radians(a)) * r * 1.15
            x1 = W * 0.86 + math.cos(math.radians(a)) * r * 1.42
            y1 = H * 0.055 + math.sin(math.radians(a)) * r * 1.42
            d.line([(x0, y0), (x1, y1)], fill=P["blob"], width=7)
    elif cfg["shape"] == "blobs":
        d.ellipse([-W * 0.22, H * 0.10, W * 0.42, H * 0.58], fill=P["blob"])
        d.ellipse([W * 0.62, -H * 0.05, W * 1.28, H * 0.34], fill=P["blob2"])
    else:  # stripes
        sh = int(H * 0.030)
        for i in range(int(H * 0.30 / sh)):
            yy = int(H * 0.055) + i * sh * 2
            d.rectangle([0, yy, W, yy + sh], fill=P["blob"])

    # Weg mit Pfoten
    dashed_arc(d, W * 0.50, H * 1.05, W * 0.62, H * 0.34, 200, 340, P["path"], 7, 20, 18)
    for i, (fx, fy, rot, sc) in enumerate(cfg["paws"]):
        lay, pos = paw(d, W * fx, H * fy, W * sc, P["paw"], rot)
        c.alpha_composite(lay, pos)
    d = ImageDraw.Draw(c, "RGBA")

    if cfg.get("drops"):
        for (dx, dy, ds) in cfg["drops"]:
            droplet(d, W * dx, H * dy, W * ds, P["drop"])

    # Marke
    fb = F(FRED, W * 0.026, "SemiBold")
    d.text((M, M * 0.72), "Let'sDrink", font=fb, fill=P["ink"])

    # Schlagzeile
    y = M * 0.72 + int(W * 0.055)
    fh = fitblock(d, cfg["head"], BALO, W * cfg["head_size"], W - 2 * M, "ExtraBold")
    for ln in cfg["head"]:
        d.text((M, y), ln, font=fh, fill=P["ink"])
        y += int(fh.size * 0.94)

    y += int(W * 0.010)
    fs = fitblock(d, cfg["sub"], FRED, W * 0.0290, W * 0.72, "Medium")
    for ln in cfg["sub"]:
        d.text((M, y), ln, font=fs, fill=P["ink2"])
        y += int(W * 0.042)

    text_bottom = y
    # Szene mit Hund
    s = fit(scene, int(W * cfg["scene_w"]), int(H * cfg["scene_h"]))
    sx = int(W * cfg["scene_x"]) - s.width // 2
    sy = H - int(H * cfg["band_h"]) - s.height - int(H * 0.012)
    soft_shadow(c, s, sx, sy, 36, 0.20, P["shadow"], 20)
    c.alpha_composite(s, (sx, sy))
    d = ImageDraw.Draw(c, "RGBA")

    # Flasche extra
    if cfg.get("show_hero"):
        hb = fit(hero, int(W * 0.155), int(H * 0.235))
        lay = Image.new("RGBA", (hb.width + 60, hb.height + 60), (0, 0, 0, 0))
        lay.paste(hb, (30, 30), hb)
        lay = lay.rotate(-11, resample=Image.BICUBIC, expand=True)
        hx = int(W * cfg["hero_x"]) - lay.width // 2
        hy = sy + int(s.height * 0.06)
        soft_shadow(c, lay, hx, hy, 26, 0.24, P["shadow"], 16)
        c.alpha_composite(lay, (hx, hy))
        d = ImageDraw.Draw(c, "RGBA")

    # Sprechblase
    ft = F(BALO, W * 0.036, "Bold")
    txt = cfg["bubble"]
    ft = fitf(d, txt, BALO, ft.size, W * 0.34, "Bold")
    bw = tw(d, txt, ft) + int(W * 0.075)
    bh = int(ft.size * 1.85)
    bx = int(W * cfg["bubble_x"]) - bw // 2
    by = sy - bh - int(H * 0.030)
    bx = max(M, min(bx, W - M - bw))
    bubble(d, bx, by, bw, bh, P["bubble"], cfg.get("tail", 0.30))
    d.text((bx + (bw - tw(d, txt, ft)) / 2, by + bh * 0.20), txt, font=ft, fill=P["bubble_ink"])

    # Preisplakette
    fp = F(BALO, W * 0.052, "ExtraBold")
    ptxt = "CHF 29.90"
    pw_ = tw(d, ptxt, fp)
    padx, pady = int(W * 0.036), int(W * 0.022)
    lay = Image.new("RGBA", (int(pw_ + padx * 2) + 40, int(fp.size * 1.5 + pady * 2) + 40), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle([20, 20, lay.width - 20, lay.height - 20],
                         radius=int(W * 0.020), fill=P["price_bg"])
    dl.text(((lay.width - pw_) / 2, 20 + pady * 0.55), ptxt, font=fp, fill=P["price_ink"])
    lay = lay.rotate(cfg.get("price_rot", -6), resample=Image.BICUBIC, expand=True)
    ppos = (int(W * cfg["price_x"]) - lay.width // 2, int(H * cfg["price_y"]) - lay.height // 2)
    soft_shadow(c, lay, ppos[0], ppos[1], 22, 0.22, P["shadow"], 12)
    c.alpha_composite(lay, ppos)
    d = ImageDraw.Draw(c, "RGBA")

    # Fussstreifen
    bhh = int(H * cfg["band_h"])
    d.rectangle([0, H - bhh, W, H], fill=P["band"])
    fbt = F(FRED, W * 0.0250, "Medium")
    line = cfg["footer"]
    fbt = fitf(d, line, FRED, fbt.size, W - 2 * M, "Medium")
    lw = tw(d, line, fbt)
    d.text((W / 2 - lw / 2, H - bhh + (bhh - fbt.size * 1.35) / 2), line, font=fbt, fill=P["band_ink"])

    gap = by - text_bottom
    flag = "OK" if gap > H*0.02 else ">>> ENG"
    print(f"   {cfg['name']:26s} Text endet {int(text_bottom):4d}  Blase ab {int(by):4d}  Abstand {int(gap):4d}  {flag}")
    return c.convert("RGB")


# ---------- Paletten ----------
SONNE = dict(bg_top=(255, 238, 199), bg_bot=(255, 213, 160), blob=(255, 199, 92),
             blob2=(255, 223, 140), path=(226, 160, 74), paw=(233, 175, 96),
             drop=(120, 200, 214), ink=(58, 40, 24), ink2=(104, 76, 48),
             bubble=(255, 255, 255), bubble_ink=(58, 40, 24), shadow=(120, 82, 40),
             price_bg=(43, 60, 48), price_ink=(255, 250, 236),
             band=(43, 60, 48), band_ink=(255, 247, 230))

WASSER = dict(bg_top=(214, 245, 246), bg_bot=(160, 224, 231), blob=(126, 209, 219),
              blob2=(178, 232, 236), path=(86, 175, 190), paw=(120, 200, 212),
              drop=(255, 255, 255), ink=(16, 62, 71), ink2=(34, 94, 104),
              bubble=(255, 255, 255), bubble_ink=(16, 62, 71), shadow=(30, 90, 100),
              price_bg=(255, 176, 79), price_ink=(46, 34, 14),
              band=(16, 82, 94), band_ink=(226, 246, 248))

PICKNICK = dict(bg_top=(255, 232, 219), bg_bot=(255, 205, 184), blob=(255, 186, 160),
                blob2=(255, 214, 196), path=(224, 137, 106), paw=(240, 168, 140),
                drop=(126, 196, 208), ink=(74, 34, 24), ink2=(122, 66, 50),
                bubble=(255, 255, 255), bubble_ink=(74, 34, 24), shadow=(140, 70, 50),
                price_bg=(38, 92, 84), price_ink=(255, 248, 240),
                band=(38, 92, 84), band_ink=(255, 240, 232))

src = Image.open(f"{BASE}/p1.png")
hero = cutout(src.crop((659, 50, 932, 986)))
scene = cutout(src.crop((0, 43, 627, 680)))

VARIANTS = [
    dict(name="ad-F1-sonnentag.png", size=(1080, 1350), palette=SONNE, seed=101,
         shape="sun", head_size=0.088,
         head=["Endlich Wasser,", "wo er es braucht."],
         sub=["Knopf drücken, Napf füllt sich, er trinkt.",
              "Der Rest läuft zurück in die Flasche."],
         bubble="Endlich!", bubble_x=0.30, tail=0.35,
         scene_w=0.80, scene_h=0.40, scene_x=0.52, band_h=0.075,
         show_hero=True, hero_x=0.86,
         price_x=0.845, price_y=0.325, price_rot=-7,
         paws=[(0.09, 0.615, 18, 0.030), (0.20, 0.665, -8, 0.026), (0.87, 0.585, 24, 0.028)],
         drops=[(0.62, 0.20, 0.022), (0.70, 0.15, 0.016)],
         footer="550 ml  ·  Wasser und Futter  ·  Gratisversand Schweiz"),

    dict(name="ad-F2-wassertag.png", size=(1080, 1350), palette=WASSER, seed=112,
         shape="blobs", head_size=0.086,
         head=["Für den Durst", "zwischendurch."],
         sub=["Eine Hand für die Leine, eine für die Flasche.",
              "Napf für Wasser, Napf für Futter."],
         bubble="Nochmal!", bubble_x=0.32, tail=0.32,
         scene_w=0.82, scene_h=0.41, scene_x=0.50, band_h=0.075,
         show_hero=True, hero_x=0.855,
         price_x=0.845, price_y=0.315, price_rot=6,
         paws=[(0.11, 0.585, -14, 0.029), (0.22, 0.640, 10, 0.025), (0.90, 0.630, -20, 0.027)],
         drops=[(0.30, 0.175, 0.024), (0.38, 0.135, 0.017), (0.80, 0.480, 0.019)],
         footer="550 ml  ·  auslaufsicher  ·  14 Tage Rückgabe"),

    dict(name="ad-F3-picknick.png", size=(1080, 1350), palette=PICKNICK, seed=123,
         shape="stripes", head_size=0.084,
         head=["Pause machen,", "ohne Gepäck."],
         sub=["Eine Flasche statt Schüssel, Wasser und Futter.",
              "Passt in jeden Seitenhalter am Rucksack."],
         bubble="Meins!", bubble_x=0.28, tail=0.34,
         scene_w=0.80, scene_h=0.40, scene_x=0.52, band_h=0.075,
         show_hero=True, hero_x=0.86,
         price_x=0.840, price_y=0.330, price_rot=-9,
         paws=[(0.10, 0.600, 12, 0.030), (0.21, 0.655, -16, 0.025), (0.88, 0.600, 20, 0.027)],
         drops=None,
         footer="550 ml  ·  Wasser und Futter  ·  Versand aus der Schweiz"),
]

if __name__ == "__main__":
    for v in VARIANTS:
        build(v, scene, hero).save(os.path.join(OUT, v["name"]), "PNG", optimize=True)
    print("fertig")
