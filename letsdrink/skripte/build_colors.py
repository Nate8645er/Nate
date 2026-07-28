#!/usr/bin/env python3
"""Let'sDrink, verspielt ohne Hund: grosse Flasche plus alle sechs Farben."""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from build_fun import (F, tw, fitf, fitblock, cutout, fit, soft_shadow, paw,
                       droplet, dashed_arc, bubble, grad, FRED, BALO,
                       SONNE, WASSER, PICKNICK, OUT, BASE)

src = Image.open(f"{BASE}/p1.png")
hero = cutout(src.crop((659, 50, 932, 986)))

# Sechs Farbvarianten einzeln
SPANS = [(52,133),(145,226),(238,319),(346,417),(432,503),(526,595)]
strip = src.crop((0, 700, 640, 990))
bottles = []
for (x0, x1) in SPANS:
    b = cutout(strip.crop((x0 - 3, 0, x1 + 3, 290)))
    bottles.append(b)
maxh = max(b.height for b in bottles)
bottles = [b.resize((max(1, int(b.width * maxh / b.height)), maxh), Image.LANCZOS) for b in bottles]


def build(cfg):
    W, H = cfg["size"]
    M = int(W * 0.075)
    P = cfg["palette"]
    c = grad((W, H), P["bg_top"], P["bg_bot"], 3.0, cfg["seed"])
    d = ImageDraw.Draw(c, "RGBA")

    # Grossform
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
        d.ellipse([-W * 0.24, H * 0.08, W * 0.40, H * 0.54], fill=P["blob"])
        d.ellipse([W * 0.64, -H * 0.06, W * 1.30, H * 0.32], fill=P["blob2"])
    else:
        sh = int(H * 0.030)
        for i in range(int(H * 0.28 / sh)):
            yy = int(H * 0.050) + i * sh * 2
            d.rectangle([0, yy, W, yy + sh], fill=P["blob"])

    dashed_arc(d, W * 0.50, H * 1.06, W * 0.62, H * 0.30, 200, 340, P["path"], 7, 20, 18)
    for (fx, fy, rot, sc) in cfg["paws"]:
        lay, pos = paw(d, W * fx, H * fy, W * sc, P["paw"], rot)
        c.alpha_composite(lay, pos)
    d = ImageDraw.Draw(c, "RGBA")
    for (dx, dy, ds) in cfg.get("drops") or []:
        droplet(d, W * dx, H * dy, W * ds, P["drop"])

    # Marke
    d.text((M, M * 0.72), "Let'sDrink", font=F(FRED, W * 0.026, "SemiBold"), fill=P["ink"])

    # Schlagzeile
    y = M * 0.72 + int(W * 0.055)
    fh = fitblock(d, cfg["head"], BALO, W * cfg["head_size"], W - 2 * M, "ExtraBold")
    for ln in cfg["head"]:
        d.text((M, y), ln, font=fh, fill=P["ink"]); y += int(fh.size * 0.94)
    y += int(W * 0.010)
    fs = fitblock(d, cfg["sub"], FRED, W * 0.0290, W * 0.74, "Medium")
    for ln in cfg["sub"]:
        d.text((M, y), ln, font=fs, fill=P["ink2"]); y += int(W * 0.042)
    text_bottom = y

    band_h = int(H * 0.075)
    band_y = H - band_h

    # ---- Farbreihe unten ----
    row_h = int(H * 0.150)
    row_y = band_y - row_h - int(H * 0.045)
    gap = int(W * 0.014)
    scaled = [fit(b, int(W * 0.14), row_h) for b in bottles]
    total = sum(b.width for b in scaled) + gap * (len(scaled) - 1)
    x = W / 2 - total / 2
    for i, b in enumerate(scaled):
        rot = -6 if i % 2 == 0 else 6
        lay = Image.new("RGBA", (b.width + 50, b.height + 50), (0, 0, 0, 0))
        lay.paste(b, (25, 25), b)
        lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
        yy = int(row_y + (row_h - lay.height) / 2)
        soft_shadow(c, lay, int(x) - 25, yy, 18, 0.20, P["shadow"], 10)
        c.alpha_composite(lay, (int(x) - 25, yy))
        x += b.width + gap
    d = ImageDraw.Draw(c, "RGBA")

    # ---- Grosse Flasche ----
    hz = row_y - text_bottom - int(H * 0.030)
    hb = fit(hero, int(W * 0.28), int(hz * 0.90))
    lay = Image.new("RGBA", (hb.width + 70, hb.height + 70), (0, 0, 0, 0))
    lay.paste(hb, (35, 35), hb)
    lay = lay.rotate(cfg.get("hero_rot", -9), resample=Image.BICUBIC, expand=True)
    hx = int(W * cfg["hero_x"]) - lay.width // 2
    hy = int(text_bottom + (hz - lay.height) / 2) + int(H * 0.012)
    # Sicherung: sichtbarer Inhalt darf den Textblock nicht beruehren
    bb = lay.getbbox() or (0, 0, lay.width, lay.height)
    min_gap = int(H * 0.028)
    if hy + bb[1] < text_bottom + min_gap:
        hy = text_bottom + min_gap - bb[1]
    max_bottom = row_y - int(H * 0.020)
    if hy + bb[3] > max_bottom:
        hy = max_bottom - bb[3]
    r2 = int(min(W * 0.24, hz * 0.52))
    d.ellipse([W * cfg["hero_x"] - r2, hy + lay.height / 2 - r2,
               W * cfg["hero_x"] + r2, hy + lay.height / 2 + r2], fill=P["blob2"])
    soft_shadow(c, lay, hx, hy, 30, 0.24, P["shadow"], 16)
    c.alpha_composite(lay, (hx, hy))
    d = ImageDraw.Draw(c, "RGBA")

    # ---- Farb-Blase ----
    ft = F(BALO, W * 0.034, "Bold")
    txt = cfg["bubble"]
    bw = tw(d, txt, ft) + int(W * 0.070)
    bh = int(ft.size * 1.80)
    bx = int(W * cfg["bubble_x"]) - bw // 2
    by = row_y - bh - int(H * 0.022)
    bx = max(M, min(bx, W - M - bw))
    bubble(d, bx, by, bw, bh, P["bubble"], 0.32)
    d.text((bx + (bw - tw(d, txt, ft)) / 2, by + bh * 0.18), txt, font=ft, fill=P["bubble_ink"])

    # ---- Preis ----
    fp = F(BALO, W * 0.050, "ExtraBold")
    ptxt = "CHF 29.90"
    pw_ = tw(d, ptxt, fp)
    padx, pady = int(W * 0.034), int(W * 0.020)
    lay = Image.new("RGBA", (int(pw_ + padx * 2) + 40, int(fp.size * 1.5 + pady * 2) + 40), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle([20, 20, lay.width - 20, lay.height - 20], radius=int(W * 0.020), fill=P["price_bg"])
    dl.text(((lay.width - pw_) / 2, 20 + pady * 0.50), ptxt, font=fp, fill=P["price_ink"])
    lay = lay.rotate(cfg.get("price_rot", -7), resample=Image.BICUBIC, expand=True)
    ppos = (int(W * cfg["price_x"]) - lay.width // 2, int(H * cfg["price_y"]) - lay.height // 2)
    soft_shadow(c, lay, ppos[0], ppos[1], 20, 0.22, P["shadow"], 12)
    c.alpha_composite(lay, ppos)
    d = ImageDraw.Draw(c, "RGBA")

    # ---- Fussstreifen ----
    d.rectangle([0, band_y, W, H], fill=P["band"])
    fbt = fitf(d, cfg["footer"], FRED, W * 0.0250, W - 2 * M, "Medium")
    lw = tw(d, cfg["footer"], fbt)
    d.text((W / 2 - lw / 2, band_y + (band_h - fbt.size * 1.35) / 2), cfg["footer"],
           font=fbt, fill=P["band_ink"])

    print(f"   {cfg['name']:28s} Text {int(text_bottom):4d} | Flasche {hy:4d} | Reihe {row_y:4d} | Band {band_y:4d}")
    return c.convert("RGB")


VARIANTS = [
    dict(name="ad-G1-sonnentag.png", size=(1080, 1350), palette=SONNE, seed=201,
         shape="sun", head_size=0.086,
         head=["Sechs Farben,", "ein Handgriff."],
         sub=["Knopf drücken, Napf füllt sich, er trinkt.",
              "Napf für Wasser, Napf für Futter."],
         bubble="6 Farben!", bubble_x=0.22,
         hero_x=0.50, hero_rot=-9,
         price_x=0.845, price_y=0.335, price_rot=-7,
         paws=[(0.10, 0.470, 16, 0.028), (0.90, 0.455, -18, 0.026)],
         drops=[(0.63, 0.185, 0.021), (0.71, 0.140, 0.015)],
         footer="550 ml  ·  Wasser und Futter  ·  Gratisversand Schweiz"),

    dict(name="ad-G2-wassertag.png", size=(1080, 1350), palette=WASSER, seed=212,
         shape="blobs", head_size=0.084,
         head=["Such dir eine", "aus."],
         sub=["Trinkflasche mit angebautem Napf, 550 ml.",
              "Eine Hand genügt, die Leine bleibt in der anderen."],
         bubble="Alle 6 da!", bubble_x=0.24,
         hero_x=0.50, hero_rot=8,
         price_x=0.840, price_y=0.325, price_rot=6,
         paws=[(0.11, 0.455, -14, 0.027), (0.89, 0.480, 20, 0.025)],
         drops=[(0.31, 0.170, 0.023), (0.39, 0.130, 0.016)],
         footer="550 ml  ·  auslaufsicher  ·  14 Tage Rückgabe"),

    dict(name="ad-G3-picknick.png", size=(1080, 1350), palette=PICKNICK, seed=223,
         shape="stripes", head_size=0.082,
         head=["Eine für jeden", "Rucksack."],
         sub=["Sechs Farben, ein Prinzip: Wasser rein, Napf raus,",
              "und was übrig bleibt, läuft zurück."],
         bubble="6 Farben!", bubble_x=0.23,
         hero_x=0.50, hero_rot=-7,
         price_x=0.845, price_y=0.340, price_rot=-9,
         paws=[(0.10, 0.465, 12, 0.028), (0.90, 0.470, -16, 0.026)],
         drops=None,
         footer="550 ml  ·  Wasser und Futter  ·  Versand aus der Schweiz"),
]

for v in VARIANTS:
    build(v).save(os.path.join(OUT, v["name"]), "PNG", optimize=True)
print("fertig")
