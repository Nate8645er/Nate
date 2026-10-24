#!/usr/bin/env python3
"""MeowUFO Galaxy-Creatives: Cartoon-UFO, Mond, Erde, Sterne, Katzen.

Erzeugt:
  ufo-khaki.png / ufo-rosa.png   – transparente UFO-Sprites (Theme-Animation)
  galaxy-hero.png                – 16:9 Szene: UFO fliegt vom Mond zur Erde
  product-galaxy-khaki.png       – 1:1 Produkt-Cartoon khaki
  product-galaxy-rosa.png        – 1:1 Produkt-Cartoon rosa
  cats-play-galaxy.png           – 1:1 Katzen spielen unter dem UFO-Beam
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

random.seed(42)

# ---------- Palette ----------
SPACE_TOP = (11, 16, 38)
SPACE_MID = (27, 20, 67)
SPACE_BOT = (42, 30, 92)
STAR = (255, 247, 214)
GOLD = (255, 209, 102)
PINK = (247, 168, 196)
KHAKI = (154, 158, 100)
CREAM = (247, 243, 236)
DOME = (168, 216, 255)
BEAM = (255, 244, 170)
EARTH_BLUE = (91, 172, 235)
EARTH_GREEN = (127, 176, 105)
MOON = (237, 231, 217)
INK = (26, 21, 48)
FEATHER_A = (62, 193, 176)   # Teal
FEATHER_B = (240, 138, 60)   # Orange


def space_bg(w, h):
    """Vertikaler Weltraum-Verlauf mit Nebel und Sternen."""
    img = Image.new("RGB", (w, h))
    for y in range(h):
        t = y / h
        if t < 0.5:
            f = t / 0.5
            c = tuple(int(SPACE_TOP[i] + (SPACE_MID[i] - SPACE_TOP[i]) * f) for i in range(3))
        else:
            f = (t - 0.5) / 0.5
            c = tuple(int(SPACE_MID[i] + (SPACE_BOT[i] - SPACE_MID[i]) * f) for i in range(3))
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=c)

    # Nebel: weiche Farbwolken
    neb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neb)
    for cx, cy, r, col in [
        (w * 0.2, h * 0.35, w * 0.28, (255, 123, 172, 26)),
        (w * 0.75, h * 0.25, w * 0.24, (120, 90, 220, 30)),
        (w * 0.55, h * 0.75, w * 0.3, (62, 193, 176, 18)),
    ]:
        nd.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], fill=col)
    neb = neb.filter(ImageFilter.GaussianBlur(int(w * 0.07)))
    img = Image.alpha_composite(img.convert("RGBA"), neb)

    # Sterne
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h / 6000)):
        x, y = random.uniform(0, w), random.uniform(0, h)
        r = random.choice([1, 1, 1, 2, 2, 3])
        alpha = random.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=STAR + (alpha,))
    # Funkel-Sterne (4-Strahler mit Glow)
    for _ in range(int(w / 90)):
        x, y = random.uniform(0, w), random.uniform(0, h * 0.9)
        sparkle(img, x, y, random.uniform(7, 16), GOLD if random.random() < 0.5 else STAR)
    return img


def sparkle(img, x, y, size, color):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i
        r = size if i % 2 == 0 else size * 0.28
        pts.append((x + math.cos(ang) * r, y + math.sin(ang) * r))
    d.polygon(pts, fill=color + (230,))
    glow = layer.filter(ImageFilter.GaussianBlur(size * 0.6))
    img.alpha_composite(glow)
    img.alpha_composite(layer)


def glow_circle(img, cx, cy, r, color, glow_mult=1.9, glow_alpha=90):
    """Leuchtender Kreis: erst Halo (geblurt), dann Kern."""
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hr = r * glow_mult
    hd.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], fill=color + (glow_alpha,))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(r * 0.5)))


def draw_moon(img, cx, cy, r):
    glow_circle(img, cx, cy, r, MOON, 1.8, 110)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOON)
    # Krater
    for fx, fy, fr in [(-0.35, -0.2, 0.16), (0.25, 0.1, 0.22), (-0.05, 0.45, 0.12), (0.4, -0.4, 0.1)]:
        kx, ky, kr = cx + fx * r, cy + fy * r, fr * r
        d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=(214, 206, 188))
        d.ellipse([kx - kr, ky - kr, kx + kr * 0.75, ky + kr * 0.75], fill=(226, 219, 203))


def draw_earth(img, cx, cy, r):
    glow_circle(img, cx, cy, r, (130, 200, 255), 1.7, 110)
    base = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=EARTH_BLUE)
    # Kontinente: weiche Blobs, per Maske auf den Kreis beschnitten
    cont = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(cont)
    for fx, fy, fw, fh, rot in [(-0.35, -0.3, 0.5, 0.32, 20), (0.32, 0.2, 0.42, 0.34, -15),
                                (-0.4, 0.4, 0.3, 0.2, 0), (0.1, -0.15, 0.26, 0.18, 40)]:
        bw, bh = fw * r, fh * r
        blob = Image.new("RGBA", (int(bw * 2), int(bh * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(blob).ellipse([0, 0, bw * 2 - 1, bh * 2 - 1], fill=EARTH_GREEN)
        blob = blob.rotate(rot, expand=True)
        cont.alpha_composite(blob, (int(cx + fx * r - blob.width / 2), int(cy + fy * r - blob.height / 2)))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    base.paste(cont, (0, 0), Image.composite(cont.getchannel("A"), Image.new("L", img.size, 0), mask))
    # Atmosphären-Highlight
    d2 = ImageDraw.Draw(base)
    d2.arc([cx - r, cy - r, cx + r, cy + r], 210, 300, fill=(255, 255, 255, 70), width=max(2, int(r * 0.03)))
    img.alpha_composite(base)


def draw_feather(layer, x, y, size, angle=0):
    """Stilisierte Feder: weiche zweifarbige Fahne, kurzer Kiel."""
    f = Image.new("RGBA", (int(size * 1.3), int(size * 2.1)), (0, 0, 0, 0))
    fd = ImageDraw.Draw(f)
    w, h = f.size
    cx = w / 2
    top, bot = h * 0.06, h * 0.8
    left = [(cx, top)]
    right = [(cx, top)]
    for i in range(1, 10):
        t = i / 10
        spread = (math.sin(t * math.pi) ** 0.8) * size * 0.4
        yy = top + t * (bot - top)
        left.append((cx - spread, yy))
        right.append((cx + spread, yy))
    left.append((cx, bot))
    right.append((cx, bot))
    fd.polygon(left, fill=FEATHER_A + (255,))
    fd.polygon(right, fill=FEATHER_B + (255,))
    # kurzer Kiel unterhalb der Fahne
    fd.line([(cx, bot - size * 0.05), (cx, bot + size * 0.22)],
            fill=CREAM + (255,), width=max(2, int(size * 0.06)))
    # Mittelrippe innerhalb der Fahne
    fd.line([(cx, top + size * 0.05), (cx, bot)], fill=(255, 255, 255, 160),
            width=max(1, int(size * 0.025)))
    f = f.rotate(angle, expand=True, resample=Image.BICUBIC)
    layer.alpha_composite(f, (int(x - f.width / 2), int(y - f.height / 2)))


def draw_ufo(size=800, accent=KHAKI, with_beam=False, beam_len=1.0):
    """Cartoon-UFO-Sprite (transparent). Saucer + aufsitzender Dome + Lichter (+ Beam & Feder)."""
    H = int(size * (1.9 if with_beam else 0.85))
    img = Image.new("RGBA", (size, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = size / 2
    body_w, body_h = size * 0.92, size * 0.34
    body_y = size * 0.42  # Oberkante Saucer

    # Beam zuerst (liegt hinter dem Saucer): hell und klar leuchtend
    if with_beam:
        beam = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam)
        top_w = body_w * 0.2
        bot_w = body_w * 0.85
        by0 = body_y + body_h * 0.55
        by1 = min(H - 4, by0 + size * beam_len)
        steps = 70
        for i in range(steps):
            t = i / steps
            yy0 = by0 + (by1 - by0) * t
            yy1 = by0 + (by1 - by0) * (t + 1.2 / steps)
            ww = top_w + (bot_w - top_w) * t
            alpha = int(195 * (1 - t) ** 1.3 + 28)
            bd.polygon([(cx - ww / 2, yy0), (cx + ww / 2, yy0),
                        (cx + ww / 2 + (bot_w - top_w) / steps / 2, yy1),
                        (cx - ww / 2 - (bot_w - top_w) / steps / 2, yy1)],
                       fill=(255, 252, 215, alpha))
        img.alpha_composite(beam.filter(ImageFilter.GaussianBlur(size * 0.02)))
        # Feder schwebt im Beam
        draw_feather(img, cx, by0 + (by1 - by0) * 0.6, size * 0.22, angle=-14)

    # Dome: sitzt IN den Saucer (flache Basis liegt unter der Saucer-Oberkante)
    dome_w, dome_h = size * 0.54, size * 0.34
    dome_cy = body_y + body_h * 0.3          # flache Basis des Halbkreises
    dome_box = [cx - dome_w / 2, dome_cy - dome_h, cx + dome_w / 2, dome_cy + dome_h]
    d.pieslice(dome_box, 180, 360, fill=DOME + (240,))
    # Glanzlicht im Dome (oben links, innerhalb)
    d.arc([dome_box[0] + size * 0.045, dome_box[1] + dome_h * 0.42,
           dome_box[2] - size * 0.2, dome_box[3] - dome_h * 0.35], 205, 275,
          fill=(255, 255, 255, 230), width=max(3, int(size * 0.02)))

    # Saucer-Körper (überdeckt die Dome-Basis)
    d.ellipse([cx - body_w / 2, body_y, cx + body_w / 2, body_y + body_h], fill=CREAM)
    # Akzent-Ring (Produktfarbe), dezent schmaler als der Körper
    ring_h = body_h * 0.4
    d.ellipse([cx - body_w * 0.47, body_y + body_h * 0.3,
               cx + body_w * 0.47, body_y + body_h * 0.3 + ring_h], fill=accent)
    # Unterseite: klein, bleibt innerhalb der Silhouette
    d.ellipse([cx - body_w * 0.24, body_y + body_h * 0.66,
               cx + body_w * 0.24, body_y + body_h * 0.98],
              fill=tuple(int(c * 0.86) for c in CREAM))

    # Bullaugen-Lichter: weisser Kern, goldener Rand, sanfter Schein
    for fx in (-0.33, -0.11, 0.11, 0.33):
        lx = cx + fx * body_w
        ly = body_y + body_h * 0.5
        lr = size * 0.03
        glow_circle(img, lx, ly, lr, GOLD, 1.9, 80)
        d.ellipse([lx - lr, ly - lr, lx + lr, ly + lr], fill=GOLD)
        d.ellipse([lx - lr * 0.55, ly - lr * 0.55, lx + lr * 0.55, ly + lr * 0.55], fill=(255, 255, 240))
    return img


def draw_cat(size=300, pose="sit", look_up=True):
    """Cartoon-Katzen-Silhouette mit leuchtenden Augen."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 300
    if pose in ("sit", "reach"):
        # Schwanz
        d.arc([28 * s, 165 * s, 148 * s, 288 * s], 60, 210, fill=INK, width=int(15 * s))
        # Koerper
        d.ellipse([95 * s, 135 * s, 225 * s, 292 * s], fill=INK)
        # erhobene Pfote (greift nach oben)
        if pose == "reach":
            arm = Image.new("RGBA", (int(40 * s), int(120 * s)), (0, 0, 0, 0))
            ImageDraw.Draw(arm).rounded_rectangle([0, 0, 38 * s, 118 * s], radius=int(19 * s), fill=INK)
            arm = arm.rotate(-20, expand=True, resample=Image.BICUBIC)
            img.alpha_composite(arm, (int(188 * s), int(46 * s)))
        # Kopf
        hx, hy, hr = 160 * s, 96 * s, 52 * s
        d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=INK)
        # Ohren
        d.polygon([(hx - hr * 0.78, hy - hr * 0.45), (hx - hr * 0.5, hy - hr * 1.25), (hx - hr * 0.12, hy - hr * 0.85)], fill=INK)
        d.polygon([(hx + hr * 0.78, hy - hr * 0.45), (hx + hr * 0.5, hy - hr * 1.25), (hx + hr * 0.12, hy - hr * 0.85)], fill=INK)
        # Augen (nach oben schauend)
        ey = hy - (13 * s if look_up else 0)
        for ex in (hx - 20 * s, hx + 20 * s):
            glow_circle(img, ex, ey, 8 * s, GOLD, 1.8, 100)
            d.ellipse([ex - 8 * s, ey - 8 * s, ex + 8 * s, ey + 8 * s], fill=GOLD)
            d.ellipse([ex - 3 * s, ey - 6 * s, ex + 3 * s, ey + 6 * s], fill=INK)
    else:  # "jump": nach oben gestreckter Sprung
        base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        bd = ImageDraw.Draw(base)
        # gestreckter Koerper diagonal nach oben rechts
        body = Image.new("RGBA", (int(210 * s), int(90 * s)), (0, 0, 0, 0))
        ImageDraw.Draw(body).ellipse([0, 0, 209 * s, 89 * s], fill=INK)
        body = body.rotate(38, expand=True, resample=Image.BICUBIC)
        base.alpha_composite(body, (int(40 * s), int(80 * s)))
        # Vorderpfoten nach oben (vor dem Kopf, damit der Kopf sie ueberdeckt)
        for ax in (244, 274):
            arm = Image.new("RGBA", (int(30 * s), int(95 * s)), (0, 0, 0, 0))
            ImageDraw.Draw(arm).rounded_rectangle([0, 0, 28 * s, 93 * s], radius=int(14 * s), fill=INK)
            arm = arm.rotate(-32, expand=True, resample=Image.BICUBIC)
            base.alpha_composite(arm, (int((ax - 20) * s), int(22 * s)))
        # Kopf oben rechts
        hx, hy, hr = 215 * s, 78 * s, 42 * s
        bd.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=INK)
        bd.polygon([(hx - hr * 0.75, hy - hr * 0.5), (hx - hr * 0.45, hy - hr * 1.25), (hx - hr * 0.1, hy - hr * 0.85)], fill=INK)
        bd.polygon([(hx + hr * 0.75, hy - hr * 0.5), (hx + hr * 0.45, hy - hr * 1.2), (hx + hr * 0.1, hy - hr * 0.85)], fill=INK)
        # Schwanz unten links
        bd.arc([5 * s, 170 * s, 115 * s, 285 * s], 300, 120, fill=INK, width=int(14 * s))
        # Augen
        ey = hy - 8 * s
        for ex in (hx - 15 * s, hx + 15 * s):
            glow_circle(base, ex, ey, 7 * s, GOLD, 1.8, 100)
            bd.ellipse([ex - 7 * s, ey - 7 * s, ex + 7 * s, ey + 7 * s], fill=GOLD)
            bd.ellipse([ex - 2.5 * s, ey - 5 * s, ex + 2.5 * s, ey + 5 * s], fill=INK)
        img = base
    return img


def trail(img, points, color=GOLD):
    """Gepunktete Flugbahn mit ausblendender Deckkraft."""
    n = len(points)
    d = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(points):
        t = i / max(n - 1, 1)
        r = 3 + 6 * t
        alpha = int(40 + 160 * t)
        d.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))


def bezier(p0, p1, p2, n=24):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def make_hero(path):
    W, H = 1600, 900
    img = space_bg(W, H)
    draw_moon(img, 210, 190, 130)
    draw_earth(img, 1330, 760, 240)
    # Flugbahn Mond -> Erde
    pts = bezier((300, 240), (820, 60), (1150, 560), 26)
    trail(img, pts[:-6])
    # UFO auf der Bahn (leicht Richtung Erde geneigt)
    ufo = draw_ufo(360, KHAKI, with_beam=False).rotate(-14, expand=True, resample=Image.BICUBIC)
    ux, uy = pts[-6]
    img.alpha_composite(ufo, (int(ux - ufo.width / 2), int(uy - ufo.height / 2)))
    # Katzen auf der Erde schauen hoch
    cat1 = draw_cat(175, "sit")
    cat2 = draw_cat(165, "reach")
    img.alpha_composite(cat1, (1165, 500))
    img.alpha_composite(cat2, (1330, 452))
    img.convert("RGB").save(path, quality=92)


def make_product(path, accent):
    W = H = 1200
    img = space_bg(W, H)
    draw_moon(img, 160, 150, 80)
    sparkle(img, 1020, 180, 22, GOLD)
    # Glow-Bühne hinter dem Produkt
    glow_circle(img, W / 2, H * 0.42, 320, (255, 255, 255), 1.5, 40)
    ufo = draw_ufo(760, accent, with_beam=True, beam_len=0.75)
    img.alpha_composite(ufo, (int(W / 2 - ufo.width / 2), int(H * 0.1)))
    img.convert("RGB").save(path, quality=92)


def make_cats_scene(path):
    W = H = 1200
    img = space_bg(W, H)
    draw_moon(img, 1050, 140, 90)
    # Erdboden als grüner Hügel unten
    d = ImageDraw.Draw(img)
    d.ellipse([-300, H * 0.78, W + 300, H * 1.6], fill=EARTH_GREEN)
    d.ellipse([-300, H * 0.82, W + 300, H * 1.7], fill=tuple(int(c * 0.85) for c in EARTH_GREEN))
    # UFO mit Beam über dem Hügel
    ufo = draw_ufo(640, PINK, with_beam=True, beam_len=1.05)
    img.alpha_composite(ufo, (int(W / 2 - ufo.width / 2), int(H * 0.04)))
    # Katzen springen nach der Feder
    cat_a = draw_cat(300, "jump")
    cat_b = draw_cat(240, "sit")
    img.alpha_composite(cat_a, (int(W * 0.28), int(H * 0.52)))
    img.alpha_composite(cat_b, (int(W * 0.62), int(H * 0.62)))
    img.convert("RGB").save(path, quality=92)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    draw_ufo(800, KHAKI).save(f"{out}/ufo-khaki.png")
    draw_ufo(800, PINK).save(f"{out}/ufo-rosa.png")
    make_hero(f"{out}/galaxy-hero.png")
    make_product(f"{out}/product-galaxy-khaki.png", KHAKI)
    make_product(f"{out}/product-galaxy-rosa.png", PINK)
    make_cats_scene(f"{out}/cats-play-galaxy.png")
    print("done")
