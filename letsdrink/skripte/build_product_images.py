#!/usr/bin/env python3
"""
Eigene Produktbilder fuer den Shop.
Sechs Einzelaufnahmen plus ein Reihenbild, neutraler Studiohintergrund,
kein Text, keine fremden Wasserzeichen.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = "/home/claude/ad"
OUT = "/mnt/user-data/outputs/produktbilder"
os.makedirs(OUT, exist_ok=True)

import sys
sys.path.insert(0, BASE)
from build_scene import BOTTLES   # sechs umgefaerbte Flaschen in voller Qualitaet

SIZE = 1600
SS = 2


def studio_bg(w, h, seed=5):
    """Sehr helles, leicht abfallendes Studiograu mit feinem Korn."""
    y = np.linspace(0, 1, h)[:, None, None]
    top = np.array((252, 251, 249), float)
    bot = np.array((232, 230, 226), float)
    arr = np.repeat(top * (1 - y) + bot * y, w, axis=1)
    arr += np.repeat(np.random.default_rng(seed).normal(0, 1.8, (h, w, 1)), 3, axis=2)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # weiche Lichtinsel
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = int(w * 0.46)
    d.ellipse([w / 2 - r, h * 0.40 - r, w / 2 + r, h * 0.40 + r], fill=(255, 255, 255, 120))
    lay = lay.filter(ImageFilter.GaussianBlur(w * 0.06))
    return Image.alpha_composite(img, lay)


def reflection(img, frac=0.30, top_alpha=74):
    h = int(img.height * frac)
    fl = img.transpose(Image.FLIP_TOP_BOTTOM).crop((0, 0, img.width, h))
    a = np.array(fl).astype(float)
    ramp = np.linspace(top_alpha, 0, h)[:, None]
    a[:, :, 3] = np.clip(a[:, :, 3] * (ramp / 255.0), 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(2.0))


def shade(canvas, img, x, y, blur, op, col, dy):
    p = blur * 2
    s = Image.new("RGBA", (img.width + p * 2, img.height + p * 2), (0, 0, 0, 0))
    s.paste(img, (p, p), img)
    s = s.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(s)
    a[:, :, :3] = np.array(col)
    a[:, :, 3] = (a[:, :, 3] * op).astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(a, "RGBA"), (x - p, y - p + dy))


def fit_h(img, h):
    r = h / img.height
    out = img.resize((max(1, int(img.width * r)), h), Image.LANCZOS)
    if r > 1.03:
        out = out.filter(ImageFilter.UnsharpMask(radius=1.3, percent=75, threshold=3))
    return out


def single(bottle, name, idx):
    W = H = SIZE * SS
    c = studio_bg(W, H, seed=20 + idx)
    b = fit_h(bottle, int(H * 0.70))
    x = W // 2 - b.width // 2
    y = int(H * 0.135)
    base = y + b.height
    d = ImageDraw.Draw(c, "RGBA")
    d.line([(int(W * 0.16), base + 2), (int(W * 0.84), base + 2)], fill=(30, 40, 36, 26), width=2)
    c.alpha_composite(reflection(b), (x, base + 3))
    shade(c, b, x, y, int(30 * SS), 0.16, (60, 70, 68), int(16 * SS))
    c.alpha_composite(b, (x, y))
    out = c.resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
    p = os.path.join(OUT, name)
    out.save(p, "JPEG", quality=94, optimize=True, progressive=True)
    return p


def lineup(name):
    W = H = SIZE * SS
    c = studio_bg(W, H, seed=77)
    hh = int(H * 0.56)
    imgs = [fit_h(b, hh) for _, b in BOTTLES]
    gap = int(W * 0.016)
    total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    avail = int(W * 0.86)
    if total > avail:
        k = (avail - gap * (len(imgs) - 1)) / sum(i.width for i in imgs)
        imgs = [i.resize((max(1, int(i.width * k)), max(1, int(i.height * k))), Image.LANCZOS) for i in imgs]
        total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    x = W // 2 - total // 2
    y = int(H * 0.22)
    base = y + max(i.height for i in imgs)
    d = ImageDraw.Draw(c, "RGBA")
    d.line([(int(W * 0.07), base + 2), (int(W * 0.93), base + 2)], fill=(30, 40, 36, 24), width=2)
    for im in imgs:
        yy = base - im.height
        c.alpha_composite(reflection(im, 0.26, 66), (x, base + 3))
        shade(c, im, x, yy, int(22 * SS), 0.15, (60, 70, 68), int(12 * SS))
        c.alpha_composite(im, (x, yy))
        x += im.width + gap
    out = c.resize((SIZE, SIZE), Image.LANCZOS).convert("RGB")
    p = os.path.join(OUT, name)
    out.save(p, "JPEG", quality=94, optimize=True, progressive=True)
    print(f"   Reihe: {len(imgs)} Flaschen, Breite {total} von {avail}")
    return p


paths = [lineup("00-alle-sechs-farben.jpg")]
for i, (nm, b) in enumerate(BOTTLES, start=1):
    slug = nm.lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
    paths.append(single(b, f"{i:02d}-{slug}.jpg", i))

for p in paths:
    print("gespeichert:", os.path.basename(p), os.path.getsize(p) // 1024, "KB")
