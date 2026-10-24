#!/usr/bin/env python3
"""MeowUFO Studio-Produktbilder im Space-Look.

Pipeline: rembg-Freisteller (Fallback: Weiss-Threshold) + PIL-Komposition.
Erzeugt aus creatives/source/:
  studio-luna.png       – Luna (Rosa) auf Galaxy-Bühne
  studio-nova.png       – Nova (Weiss/Khaki) auf Galaxy-Bühne
  studio-set.png        – 2er-Set nebeneinander
  studio-features.png   – Feature-Callouts (Automatik, USB, Feder & Laser)
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1200
NAVY_TOP = (14, 18, 48)
NAVY_BOT = (27, 22, 72)
PINK = (255, 123, 172)
GOLD = (255, 209, 102)
STARLIGHT = (241, 243, 255)


def cutout(path):
    """Freisteller: rembg, sonst Weiss-Threshold (Fotos haben weissen Studio-BG)."""
    src = Image.open(path).convert("RGBA")
    try:
        from rembg import remove
        out = remove(src)
        # Plausibilitäts-Check: genug opake Pixel?
        alpha = out.getchannel("A")
        if alpha.histogram()[-1] > src.width * src.height * 0.03:
            return out
    except Exception:
        pass
    # Fallback: alles nahe Weiss transparent machen (mit weichem Rand)
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if r > 242 and g > 242 and b > 242:
                px[x, y] = (r, g, b, 0)
    return src


def stage(w=W, h=H, glow=PINK):
    """Galaxy-Bühne: vertikaler Verlauf, dezente Sterne, Glow hinter dem Produkt."""
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(NAVY_TOP[i] + (NAVY_BOT[i] - NAVY_TOP[i]) * t) for i in range(3)))
    img = img.convert("RGBA")
    # dezente Sterne (wenige, klein – das Produkt ist der Held)
    import random
    random.seed(7)
    sd = ImageDraw.Draw(img)
    for _ in range(70):
        x, y = random.uniform(0, w), random.uniform(0, h * 0.75)
        r = random.choice([1, 1, 1.5, 2])
        sd.ellipse([x - r, y - r, x + r, y + r], fill=STARLIGHT + (random.randint(60, 160),))
    # Glow-Bühne
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([w * 0.16, h * 0.2, w * 0.84, h * 0.82], fill=glow + (60,))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(w * 0.09)))
    return img


def soft_shadow(img, cx, cy, rx, ry, alpha=120):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(5, 6, 18, alpha))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(rx * 0.18)))


def place(img, cut, target_w, cx, cy_bottom):
    """Produkt proportional skalieren, Schatten setzen, einfügen."""
    f = target_w / cut.width
    p = cut.resize((int(cut.width * f), int(cut.height * f)), Image.LANCZOS)
    px = int(cx - p.width / 2)
    py = int(cy_bottom - p.height)
    soft_shadow(img, cx, cy_bottom - p.height * 0.02, p.width * 0.34, p.height * 0.05)
    img.alpha_composite(p, (px, py))
    return (px, py, p.width, p.height)


def sparkle(img, x, y, size, color=GOLD, alpha=200):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i
        r = size if i % 2 == 0 else size * 0.3
        pts.append((x + math.cos(ang) * r, y + math.sin(ang) * r))
    d.polygon(pts, fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))


def studio_single(cut, out, glow):
    img = stage(glow=glow)
    place(img, cut, 760, W / 2, H * 0.86)
    sparkle(img, W * 0.2, H * 0.24, 14)
    sparkle(img, W * 0.82, H * 0.34, 10, STARLIGHT)
    img.convert("RGB").save(out, quality=93)


def studio_set(cut_a, cut_b, out):
    img = stage(glow=PINK)
    place(img, cut_b, 560, W * 0.68, H * 0.88)
    place(img, cut_a, 600, W * 0.33, H * 0.9)
    sparkle(img, W * 0.5, H * 0.16, 14)
    sparkle(img, W * 0.88, H * 0.3, 10, STARLIGHT)
    img.convert("RGB").save(out, quality=93)


def _font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for base in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/", ""):
        try:
            return ImageFont.truetype(base + name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def studio_features(cut, out):
    """Feature-Bild: Produkt rechts, drei Callouts links mit Linien."""
    img = stage(glow=GOLD)
    x, y, pw, ph = place(img, cut, 680, W * 0.62, H * 0.88)
    d = ImageDraw.Draw(img)
    label_font = _font(34, bold=True)
    sub_font = _font(26)

    features = [
        ("AUTOMATIK-MODUS", "Wedelt mit cleveren Pausen", (x + pw * 0.52, y + ph * 0.16), H * 0.2),
        ("USB-AKKU", "Laden statt Batterien kaufen", (x + pw * 0.16, y + ph * 0.68), H * 0.52),
        ("FEDER & LASER", "Weckt den Jagdinstinkt", (x + pw * 0.4, y + ph * 0.92), H * 0.8),
    ]
    tx = W * 0.06
    for title, sub, (ax, ay), ty in features:
        # Linie vom Text zum Produktpunkt
        d.line([(tx + 8, ty + 46), (tx + 150, ty + 46), (ax, ay)], fill=STARLIGHT + (140,), width=2)
        d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], outline=GOLD, width=3)
        d.text((tx, ty), title, font=label_font, fill=STARLIGHT)
        d.text((tx, ty + 44 + 12), sub, font=sub_font, fill=STARLIGHT + (190,))
    img.convert("RGB").save(out, quality=93)


if __name__ == "__main__":
    import sys
    src_dir = "creatives/source"
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "creatives"
    luna = cutout(f"{src_dir}/produkt-rosa.png")
    nova = cutout(f"{src_dir}/produkt-weiss.png")
    studio_single(luna, f"{out_dir}/studio-luna.png", PINK)
    studio_single(nova, f"{out_dir}/studio-nova.png", GOLD)
    studio_set(luna, nova, f"{out_dir}/studio-set.png")
    studio_features(nova, f"{out_dir}/studio-features.png")
    print("done")
