#!/usr/bin/env python3
"""Creative-Pipeline (Produkt C) — selbst gebaut, ohne Fremd-Credits.

Erzeugt aus tariffs.json Ad-Creatives als SVG (Code, deterministisch, kein
Browser, keine Credits) in mehreren Formaten fuer Meta/TikTok/Google.
Ein Befehl rendert alles neu, wenn sich Preise/Funktionen aendern (DoD C):

    python generate.py

Ergebnis: out/<tarif>_<format>.svg + out/index.html (Galerie).
SVG laesst sich bei Bedarf verlustfrei zu PNG rastern (z.B. rsvg/inkscape/
resvg) — ohne laufende Kosten.
"""
from __future__ import annotations

import json
import os
import pathlib

# Generierte Hintergrundbilder (optional, siehe muapi_backdrop.py).
BACKDROP_DIR = pathlib.Path(__file__).resolve().parent / "backdrops"

# Werbe-Formate (Breite x Hoehe): 1:1, 4:5, 9:16.
FORMATS: dict[str, tuple[int, int]] = {
    "1x1": (1080, 1080),
    "4x5": (1080, 1350),
    "9x16": (1080, 1920),
}

# Palette (dunkel/Premium, konsistent mit dem Plattform-UI).
BG = "#0b0d12"
PANEL = "#12151d"
ACCENT = "#6c8cff"
TEXT = "#e7ebf3"
MUTED = "#8b93a7"
BORDER = "#232838"


def esc(s: str) -> str:
    """XML-escaping fuer Textinhalte."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def card_svg(tariff: dict, brand: str, vat_note: str, w: int, h: int,
             backdrop_href: str | None = None) -> str:
    """Ein Tarif-Creative als vollstaendiges SVG-Dokument.

    `backdrop_href`: optionaler Pfad zu einem generierten Hintergrundbild
    (siehe muapi_backdrop.py). Das Bild liefert NUR die Atmosphaere — alle
    Texte werden hier deterministisch darueber gelegt, damit Preise und
    Pflichtangaben garantiert korrekt und lesbar sind (Schweizer PBV).
    Ueber dem Bild liegt ein Abdunkelungs-Verlauf ("Scrim"), damit der Text
    unabhaengig vom Bildinhalt lesbar bleibt.
    """
    pad = round(w * 0.08)
    cx = pad
    # Vertikale Startpunkte proportional zur Hoehe.
    y_brand = round(h * 0.11)
    y_name = round(h * 0.24)
    y_price = round(h * 0.33)
    y_aud = round(h * 0.385)
    y_div = round(h * 0.44)
    y_feat = round(h * 0.52)
    feat_step = round(h * 0.072)
    name_size = round(w * 0.11)
    price_size = round(w * 0.058)

    feats = tariff.get("features", [])
    feat_els = []
    for i, f in enumerate(feats):
        y = y_feat + i * feat_step
        if y > h - pad * 1.4:
            break
        feat_els.append(
            f'<circle cx="{cx + 10}" cy="{y - 12}" r="7" fill="{ACCENT}"/>'
            f'<text x="{cx + 34}" y="{y}" class="feat">{esc(f)}</text>'
        )
    feats_svg = "\n    ".join(feat_els)

    # Hintergrundbild (falls vorhanden) + Abdunkelung fuer Textlesbarkeit.
    backdrop_svg = ""
    if backdrop_href:
        backdrop_svg = (
            f'<image href="{esc(backdrop_href)}" x="0" y="0" '
            f'width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/>\n'
            f'  <rect width="{w}" height="{h}" fill="url(#scrim)"/>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{PANEL}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
    <linearGradient id="scrim" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{BG}" stop-opacity="0.92"/>
      <stop offset="0.55" stop-color="{BG}" stop-opacity="0.72"/>
      <stop offset="1" stop-color="{BG}" stop-opacity="0.45"/>
    </linearGradient>
    <style>
      text {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; fill: {TEXT}; }}
      .brand {{ font-size: {round(w*0.032)}px; fill: {MUTED}; letter-spacing: 3px; }}
      .name  {{ font-size: {name_size}px; font-weight: 700; }}
      .price {{ font-size: {price_size}px; font-weight: 700; fill: {ACCENT}; }}
      .aud   {{ font-size: {round(w*0.034)}px; fill: {MUTED}; }}
      .feat  {{ font-size: {round(w*0.036)}px; }}
      .foot  {{ font-size: {round(w*0.026)}px; fill: {MUTED}; }}
    </style>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  {backdrop_svg}
  <rect x="0" y="0" width="{w}" height="{round(h*0.014)}" fill="{ACCENT}"/>
  <text x="{cx}" y="{y_brand}" class="brand">{esc(brand.upper())}</text>
  <text x="{cx}" y="{y_name}" class="name">{esc(tariff.get("name",""))}</text>
  <text x="{cx}" y="{y_price}" class="price">{esc(tariff.get("price_display",""))}</text>
  <text x="{cx}" y="{y_aud}" class="aud">{esc(tariff.get("audience",""))}</text>
  <line x1="{cx}" y1="{y_div}" x2="{w-pad}" y2="{y_div}" stroke="{BORDER}" stroke-width="2"/>
    {feats_svg}
  <text x="{cx}" y="{h-pad}" class="foot">Preise {esc(brand)} · {esc(vat_note)}</text>
</svg>'''


def find_backdrop(code: str, outdir: pathlib.Path) -> str | None:
    """Sucht ein generiertes Hintergrundbild fuer diesen Tarif.

    Gibt einen RELATIVEN Pfad zurueck (kein base64): SVG und PNG reisen
    gemeinsam, das haelt das Repository klein. Beim Rastern nach PNG/JPG —
    was Werbeplattformen ohnehin brauchen — wird daraus eine eigenstaendige
    Datei.
    """
    png = BACKDROP_DIR / f"{code}.png"
    if not png.is_file():
        return None
    return os.path.relpath(png, outdir)


def build_all(data: dict, outdir: pathlib.Path, use_backdrops: bool = True) -> list[pathlib.Path]:
    """Rendert alle Tarife in allen Formaten. Gibt die geschriebenen Pfade zurueck.

    Liegt zu einem Tarif ein Hintergrundbild in backdrops/ vor, wird es
    automatisch verwendet — sonst der reine Farbverlauf. Die Pipeline
    funktioniert also mit und ohne bezahlte Bildgenerierung.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    brand = data.get("brand", "")
    vat = data.get("vat_note", "")
    written: list[pathlib.Path] = []
    for t in data["tariffs"]:
        href = find_backdrop(t["code"], outdir) if use_backdrops else None
        for fmt, (w, h) in FORMATS.items():
            svg = card_svg(t, brand, vat, w, h, backdrop_href=href)
            p = outdir / f"{t['code']}_{fmt}.svg"
            p.write_text(svg, encoding="utf-8")
            written.append(p)
    _write_index(data, outdir, written)
    return written


def _write_index(data: dict, outdir: pathlib.Path, written: list[pathlib.Path]) -> None:
    cards = "\n".join(
        f'<figure><img src="{p.name}" alt="{esc(p.stem)}"/><figcaption>{esc(p.stem)}</figcaption></figure>'
        for p in written
    )
    html = f'''<!doctype html><meta charset="utf-8"><title>Creatives — {esc(data.get("brand",""))}</title>
<style>body{{background:{BG};color:{TEXT};font-family:system-ui,sans-serif;margin:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px}}
figure{{margin:0}}img{{width:100%;border:1px solid {BORDER};border-radius:10px;background:{PANEL}}}
figcaption{{color:{MUTED};font-size:13px;margin-top:6px}}</style>
<h1>Ad-Creatives (SVG, generiert)</h1>
<div class="grid">{cards}</div>'''
    (outdir / "index.html").write_text(html, encoding="utf-8")


def load_tariffs(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    here = pathlib.Path(__file__).resolve().parent
    data = load_tariffs(here / "tariffs.json")
    written = build_all(data, here / "out")
    print(f"{len(written)} Creatives in {here / 'out'} erzeugt (+ index.html).")


if __name__ == "__main__":
    main()
