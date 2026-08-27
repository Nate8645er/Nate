#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Katzenauto-Video-Anzeige: der Higgsfield-Clip (Studio-Kameraflug ums
Produkt, roh geprueft - kein Text/Logo, exakt das echte Produkt) bekommt
denselben Marken-Rahmen wie die Standbilder aus bauen_ki.py: oben ein
schmaler Streifen mit Wortmarke, unten Headline/Subline/Preis.

Der Clip wird NICHT beschnitten - er wird verkleinert und mittig in ein
Fenster zwischen den beiden Marken-Baendern gesetzt (Letterbox-Prinzip),
damit auch die spaeten, weiter herangezoomten Frames nicht unter dem
unteren Band verschwinden.

Kein Domainname im Bild, aus demselben Grund wie in bauen.py/bauen_ki.py.
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

HIER = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.abspath(os.path.join(HIER, "..", "..",
                                    "marketing", "anzeigen", "quelle"))
QUELLE_VIDEO = os.path.join(HIER, "higgsfield", "video-roh.mp4")
AUSGABE = os.path.join(HIER, "katzenauto_video_720x1280.mp4")

W, H = 720, 1280
TOP_H = round(H * 0.075)     # 96
BOTTOM_H = round(H * 0.205)  # 262
VIDEO_H = H - TOP_H - BOTTOM_H
VIDEO_W = round(720 * (VIDEO_H / 1280))
VIDEO_X = (W - VIDEO_W) // 2

BG = (250, 249, 247)
TUERKIS_ORANGE = (232, 119, 34)
TINTE = (23, 20, 18)
MUTED = (140, 132, 126)
PREIS = "CHF 139.–"

_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        name = "a-sans-bold.ttf" if bold else "a-sans.ttf"
        _fc[key] = ImageFont.truetype(os.path.join(FDIR, name), size)
    return _fc[key]


def text(img, xy, s, f, fill, anchor="la", track=0.0):
    d = ImageDraw.Draw(img)
    if track == 0:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    x, y = xy
    widths = [d.textlength(ch, font=f) for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    if anchor[0] == "r":
        x -= total
    for ch, w in zip(s, widths):
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += w + track


def top_band():
    img = Image.new("RGB", (W, TOP_H), BG)
    m = round(W * 0.07)
    marke_gr = round(W * 0.032)
    text(img, (m, TOP_H // 2), "Katzenauto", font(marke_gr, True), TINTE,
         anchor="lm", track=0.6)
    return img


def bottom_band():
    img = Image.new("RGB", (W, BOTTOM_H), BG)
    m = round(W * 0.07)
    y = round(BOTTOM_H * 0.10)
    bh = max(3, round(W * 0.006))
    ImageDraw.Draw(img).rectangle(
        [m, y, m + round(W * 0.07), y + bh], fill=TUERKIS_ORANGE)
    y += bh + round(BOTTOM_H * 0.09)
    kopf_gr = round(W * 0.068)
    text(img, (m, y), "Ade, Karton.", font(kopf_gr, True), TINTE,
         track=-kopf_gr * 0.02)
    y += round(kopf_gr * 1.22)
    sub_gr = round(W * 0.032)
    text(img, (m, y), "Plüsch-Sportwagenbett für Katze & Hund",
         font(sub_gr), MUTED)
    y += round(sub_gr * 1.7)
    ImageDraw.Draw(img).rectangle([m, y, W - m, y], fill=(215, 210, 204))
    y += round(BOTTOM_H * 0.11)
    text(img, (m, y), PREIS, font(round(W * 0.05), True), TINTE)
    return img


def bauen():
    os.makedirs(os.path.join(HIER, "higgsfield"), exist_ok=True)
    top_pfad = os.path.join(HIER, "higgsfield", "_band_oben.png")
    bottom_pfad = os.path.join(HIER, "higgsfield", "_band_unten.png")
    top_band().save(top_pfad, "PNG")
    bottom_band().save(bottom_pfad, "PNG")

    bg_hex = "0x%02X%02X%02X" % BG

    filt = (
        "[0:v]scale=%d:%d[vid];"
        "[1:v][vid]overlay=%d:%d[stage];"
        "[stage][2:v]overlay=0:0[stage2];"
        "[stage2][3:v]overlay=0:%d[out]"
    ) % (VIDEO_W, VIDEO_H, VIDEO_X, TOP_H, TOP_H + VIDEO_H)

    cmd = [
        "ffmpeg", "-y",
        "-i", QUELLE_VIDEO,
        "-f", "lavfi", "-i", "color=c=%s:s=%dx%d:d=5" % (bg_hex, W, H),
        "-i", top_pfad,
        "-i", bottom_pfad,
        "-filter_complex", filt,
        "-map", "[out]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        AUSGABE,
    ]
    subprocess.run(cmd, check=True)
    print("->", AUSGABE)


if __name__ == "__main__":
    bauen()
