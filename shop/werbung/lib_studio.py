# -*- coding: utf-8 -*-
"""Studio-Renderer fuer Let'sDrink Ad-Creatives.
Monochrome Bildsprache, 8er-Raster, zwei gestapelte Schatten.
Kein erfundener Inhalt: nur echte Freisteller + freigegebene Aussagen.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = "/tmp/claude-0/-home-user-Nate/2d96a9a6-93ca-5da3-99c5-55dbdd35f6e9/scratchpad/amber/hoch"
OUT = "/tmp/claude-0/-home-user-Nate/2d96a9a6-93ca-5da3-99c5-55dbdd35f6e9/scratchpad/werbung"
FDIR = os.path.join(OUT, "_fonts")

# --- Palette -----------------------------------------------------------
WEISS   = (255, 255, 255)
ABSATZ  = (245, 244, 241)   # #F5F4F1
STUDIO  = (241, 239, 235)   # #F1EFEB
TEXT    = (17, 17, 17)      # #111111
MUTED   = (110, 110, 115)   # #6E6E73
HAIRLN  = (225, 223, 218)
GHOST   = (236, 234, 229)   # Typo-Grundschicht

FARBEN = ["tuerkis", "gruen", "rosa", "grau", "schwarz", "weiss"]

_fcache = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fcache:
        name = "a-sans-bold.ttf" if bold else "a-sans.ttf"
        _fcache[key] = ImageFont.truetype(os.path.join(FDIR, name), size)
    return _fcache[key]


def flasche(name="tuerkis"):
    return Image.open(os.path.join(SRC, "a-flasche-%s.webp" % name)).convert("RGBA")


# --- Hintergrund -------------------------------------------------------
def studio_bg(w, h, horizon=None, wand=WEISS, boden=STUDIO, blend=26):
    """Zyklorama: Wandfarbe oben, Bodenflaeche unten, weicher Uebergang."""
    bg = Image.new("RGB", (w, h), wand)
    if horizon is None:
        return bg
    d = ImageDraw.Draw(bg)
    d.rectangle([0, horizon, w, h], fill=boden)
    for i in range(blend):
        t = i / (blend - 1)
        s = t * t * (3 - 2 * t)          # smoothstep
        c = tuple(round(wand[k] + (boden[k] - wand[k]) * s) for k in range(3))
        d.line([(0, horizon - blend + i), (w, horizon - blend + i)], fill=c)
    return bg


# --- Schatten ----------------------------------------------------------
def schatten(base, cx, boden_y, breite, *, kontakt=0.38, ambient=0.125,
             k_w=0.80, k_h=0.020, a_w=1.50, a_h=0.075, k_blur=7, a_blur=46):
    """Zwei gestapelte Schatten: harter Kontaktschatten + weicher Umgebungsschatten."""
    w, h = base.size
    for wf, hf, alpha, blur in ((a_w, a_h, ambient, a_blur), (k_w, k_h, kontakt, k_blur)):
        lay = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(lay)
        bw = breite * wf
        bh = breite * hf * 2.6
        d.ellipse([cx - bw / 2, boden_y - bh / 2, cx + bw / 2, boden_y + bh / 2],
                  fill=int(255 * alpha))
        lay = lay.filter(ImageFilter.GaussianBlur(blur))
        base.paste(Image.new("RGB", (w, h), (24, 24, 26)), (0, 0), lay)
    return base


def stelle(base, bild, *, hoehe, cx, boden_y, winkel=0.0, mit_schatten=True, **sk):
    """Flasche massstabsgetreu platzieren; Standfuss auf boden_y."""
    ratio = bild.width / bild.height
    bw = max(1, round(hoehe * ratio))
    im = bild.resize((bw, round(hoehe)), Image.LANCZOS)
    if winkel:
        im = im.rotate(winkel, resample=Image.BICUBIC, expand=True)
    if mit_schatten:
        schatten(base, cx, boden_y, bw, **sk)
    base.paste(im, (round(cx - im.width / 2), round(boden_y - im.height)), im)
    return base


# --- Typografie --------------------------------------------------------
def _tw(draw, txt, f, track):
    return draw.textlength(txt, font=f) + track * max(0, len(txt) - 1)


def text(base, xy, txt, f, fill=TEXT, track=0.0, anchor="ls"):
    """Text mit echter Laufweite. anchor: l/m/r + s(baseline-frei, top-basiert)."""
    d = ImageDraw.Draw(base)
    x, y = xy
    total = _tw(d, txt, f, track)
    ha = anchor[0]
    if ha == "m":
        x -= total / 2
    elif ha == "r":
        x -= total
    if track == 0:
        d.text((x, y), txt, font=f, fill=fill)
    else:
        for ch in txt:
            d.text((x, y), ch, font=f, fill=fill)
            x += d.textlength(ch, font=f) + track
    return total


def block(base, xy, zeilen, f, *, lh, fill=TEXT, track=0.0, anchor="l"):
    x, y = xy
    for z in zeilen:
        text(base, (x, y), z, f, fill=fill, track=track, anchor=anchor + "s")
        y += lh
    return y


def ink(txt, f, track=0.0):
    """Tatsaechliche Tintenbox relativ zum Zeichen-Ursprung (x, y-top)."""
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    b = f.getbbox(txt)
    return (b[0], b[1], _tw(probe, txt, f, track), b[3] - b[1])


def text_ink(base, x, ink_top, txt, f, fill=TEXT, track=0.0, anchor="l"):
    """Setzt Text so, dass die Oberkante der Tinte exakt auf ink_top liegt."""
    ix, iy, iw, ih = ink(txt, f, track)
    return text(base, (x, ink_top - iy), txt, f, fill=fill, track=track,
                anchor=anchor + "s"), ih


def fit_ink_height(txt, ziel_hoehe, bold=True, track=0.0, max_breite=None):
    """Groesste Groesse, deren Tintenhoehe ziel_hoehe (und ggf. max_breite) haelt."""
    lo, hi = 8, 1600
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f = font(mid, bold)
        _, _, iw, ih = ink(txt, f, track * mid / 100)
        if ih <= ziel_hoehe and (max_breite is None or iw <= max_breite):
            lo = mid
        else:
            hi = mid - 1
    return lo


def fit_font(txt, ziel_breite, bold=True, track=0.0, start=400):
    """Groesste Schriftgroesse, deren Satzbreite ziel_breite nicht ueberschreitet."""
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    lo, hi = 8, 2400
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _tw(probe, txt, font(mid, bold), track * mid / 100) <= ziel_breite:
            lo = mid
        else:
            hi = mid - 1
    return lo


def linie(base, x0, y, x1, farbe=HAIRLN, staerke=1):
    ImageDraw.Draw(base).rectangle([x0, y, x1, y + staerke - 1], fill=farbe)


def speichern(img, name):
    p = os.path.join(OUT, name)
    img.convert("RGB").save(p, "PNG", optimize=True)
    print("  ->", name, img.size)
    return p
