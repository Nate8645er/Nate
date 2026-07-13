"""Deterministischer Shop-Bauplan-Generator fuer den JARVIS-Agenten.

Erzeugt aus einer kurzen Beschreibung einen kompletten, verkaufsfertigen
Shop-Bauplan: Markenname, Slogan, Farbwelt, Kollektionen, konkrete Produkte
mit Preisen (CHF) und Beschreibungen, sowie eine Umsetzungs-Checkliste.

Ehrlich: Das ist ein vollstaendiger *Bauplan/Spezifikation* — kein live auf
Shopify erstellter Shop. Den Bauplan kannst du 1:1 in Shopify (oder woanders)
umsetzen. Deterministisch: gleiche Eingabe -> gleicher Plan.
"""

from __future__ import annotations

import re

_MASK = (1 << 64) - 1


def _mix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & _MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
    return (z ^ (z >> 31)) & _MASK


def _seed_from_text(text: str) -> int:
    seed = 0
    for ch in text:
        seed = _mix64(seed ^ ord(ch))
    return seed or 1


def slugify(text: str) -> str:
    lowered = (text or "").strip().lower()
    lowered = (lowered.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug[:48] or "mein-shop"


def _sku_prefix(name: str) -> str:
    """Alphanumerisches SKU-Praefix aus dem Shop-Namen (max 6 Zeichen)."""

    alnum = re.sub(r"[^a-z0-9]", "", slugify(name))
    return (alnum[:6] or "shop").upper()


_ADJECTIVES = ["Premium", "Handgemacht", "Nachhaltig", "Limitiert", "Klassisch",
               "Modern", "Exklusiv", "Bio", "Robust", "Elegant", "Kompakt", "Deluxe"]
_PALETTES = [
    ("Mitternacht", "#0b1020", "#22d3ee"),
    ("Sandstein", "#f5efe6", "#b6795a"),
    ("Waldgruen", "#0f1f17", "#4ade80"),
    ("Rosé", "#fdf2f5", "#e0698a"),
    ("Graphit", "#141414", "#f5c542"),
    ("Ozean", "#08243a", "#38bdf8"),
]
_SLOGANS = [
    "Qualitaet, die man spuert.",
    "Fuer alle, die mehr wollen.",
    "Handverlesen. Fair. Echt.",
    "Dein Stil, dein Statement.",
    "Weniger, aber besser.",
    "Gemacht, um zu bleiben.",
]


def build_shop_blueprint(
    *,
    name: str,
    sells: str,
    audience: str = "",
    style: str = "",
    product_count: int = 8,
) -> dict:
    """Erzeuge einen kompletten Shop-Bauplan als JSON-faehiges dict."""

    name = (name or "Mein Shop").strip()
    sells = (sells or "Produkte").strip()
    audience = (audience or "alle, die guten Wert schaetzen").strip()
    style = (style or "modern, klar").strip()
    product_count = max(3, min(24, int(product_count)))

    seed = _seed_from_text(f"{name}|{sells}|{audience}|{style}")
    palette_name, bg, accent = _PALETTES[seed % len(_PALETTES)]
    slogan = _SLOGANS[_mix64(seed) % len(_SLOGANS)]

    base = sells.split(",")[0].strip() or sells or "Produkt"
    singular = base.rstrip("s") if len(base) > 3 else base

    collections = [
        {"title": "Neuheiten", "description": f"Die neuesten {base} frisch im Sortiment."},
        {"title": "Bestseller", "description": f"Beliebteste {base} bei {audience}."},
        {"title": "Angebote", "description": f"Reduzierte {base} — solange Vorrat reicht."},
    ]

    products = []
    for i in range(product_count):
        h = _mix64(seed ^ _mix64(i + 1))
        adjective = _ADJECTIVES[h % len(_ADJECTIVES)]
        # Preis 19–199 CHF, auf .90 gerundet fuer typische Shop-Optik
        price = 19 + (h >> 8) % 181
        price_str = f"{price - 0.10:.2f}"
        col = collections[(h >> 16) % len(collections)]["title"]
        products.append({
            "title": f"{adjective} {singular} {i + 1}",
            "price_chf": price_str,
            "sku": f"{_sku_prefix(name)}-{i + 1:03d}",
            "collection": col,
            "description": f"{adjective} {singular} fuer {audience}. Stil: {style}. "
                           f"Sorgfaeltig ausgewaehlt und bereit zum Versand.",
        })

    slug = slugify(name)
    blueprint = {
        "name": name,
        "slug": slug,
        "slogan": slogan,
        "sells": sells,
        "audience": audience,
        "style": style,
        "palette": {"name": palette_name, "background": bg, "accent": accent},
        "collections": collections,
        "products": products,
        "checklist": [
            "Shopify-Konto anlegen / einloggen",
            f"Store-Namen '{name}' und Domain '{slug}.myshopify.com' sichern",
            f"Farbwelt '{palette_name}' im Theme setzen ({bg} / {accent})",
            f"{len(collections)} Kollektionen anlegen",
            f"{len(products)} Produkte mit Preisen (CHF) einpflegen",
            "Zahlungs- und Versandarten aktivieren",
            "Impressum, AGB und Datenschutz ergaenzen",
            "Testbestellung durchfuehren und Shop veroeffentlichen",
        ],
    }
    blueprint["markdown"] = _render_markdown(blueprint)
    return blueprint


def _render_markdown(bp: dict) -> str:
    lines = [
        f"# {bp['name']}",
        f"> *{bp['slogan']}*",
        "",
        f"- **Verkauft:** {bp['sells']}",
        f"- **Zielgruppe:** {bp['audience']}",
        f"- **Stil:** {bp['style']}",
        f"- **Farbwelt:** {bp['palette']['name']} "
        f"(Hintergrund `{bp['palette']['background']}`, Akzent `{bp['palette']['accent']}`)",
        f"- **Domain-Vorschlag:** `{bp['slug']}.myshopify.com`",
        "",
        "## Kollektionen",
    ]
    for col in bp["collections"]:
        lines.append(f"- **{col['title']}** — {col['description']}")
    lines += ["", "## Produkte", "", "| Produkt | Preis (CHF) | SKU | Kollektion |", "|---|---|---|---|"]
    for p in bp["products"]:
        lines.append(f"| {p['title']} | {p['price_chf']} | {p['sku']} | {p['collection']} |")
    lines += ["", "## Umsetzungs-Checkliste"]
    for step in bp["checklist"]:
        lines.append(f"- [ ] {step}")
    lines += [
        "",
        "---",
        "_Erzeugt vom JARVIS-Agenten (Werkzeug `shop_bauen`). Vollstaendiger Bauplan — "
        "in Shopify umsetzbar. Tipp: JARVIS kann dir helfen, die Produkte real anzulegen._",
    ]
    return "\n".join(lines)
