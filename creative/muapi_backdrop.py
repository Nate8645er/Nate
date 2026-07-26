#!/usr/bin/env python3
"""Hintergrundbilder fuer Ad-Creatives via MuAPI (bezahlt) erzeugen.

ARBEITSTEILUNG (so vom KI-Team einstimmig empfohlen, siehe README):
  - MuAPI erzeugt NUR die emotionale Bildflaeche: Atmosphaere, Licht, Textur.
    Etwas, das sich aus Tarifdaten nicht ableiten laesst.
  - ALLE Texte — Tarifname, Preis, "inkl. MwSt", Funktionen — legt die
    bestehende, kostenlose SVG-Pipeline (generate.py) deterministisch
    DARUEBER.

Warum diese Trennung nicht verhandelbar ist: Ein generatives Modell schreibt
Text unzuverlaessig. Ein falsch dargestellter Preis waere in der Schweiz ein
Verstoss gegen die Preisbekanntgabeverordnung — und bei 1000 lokalisierten
Varianten waere jede einzelne neu zu pruefen. Deterministisch gerendeter Text
ist dagegen per Konstruktion korrekt und beliebig oft reproduzierbar.

Deshalb enthaelt JEDER Prompt hier den ausdruecklichen Hinweis, KEINEN Text
zu erzeugen (siehe NO_TEXT_CLAUSE).

Kosten: Jeder Lauf verbraucht echte MuAPI-Credits. Standard ist --dry-run;
ohne --generate wird NICHTS gesendet.

Nutzung:
    python3 creative/muapi_backdrop.py --list                    # Motive zeigen
    python3 creative/muapi_backdrop.py --only pro                # Dry-Run
    python3 creative/muapi_backdrop.py --only pro --generate     # erzeugt wirklich
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.request

BASE_URL = "https://api.muapi.ai/api/v1"
OUT_DIR = pathlib.Path(__file__).resolve().parent / "backdrops"

# Endpunkt aus dem offiziellen MuAPI-ComfyUI-Connector. flux-dev ist der
# guenstige Standard; fuer finale Kampagnenmotive kaeme z.B. "flux-2-pro"
# oder "google-imagen4" in Frage (teurer).
DEFAULT_ENDPOINT = "flux-dev-image"

# Wird an JEDEN Prompt angehaengt. Ohne diese Klausel schreiben Bildmodelle
# gern unleserlichen Pseudo-Text ins Bild — der dann mit dem echten,
# darueber gelegten Preis kollidiert.
NO_TEXT_CLAUSE = (
    "abstract background only, absolutely no text, no letters, no numbers, "
    "no words, no watermark, no logo, no user interface elements, "
    "large empty area on the left half for text overlay"
)

# Ein Motiv pro Tarif — Stimmung passend zur Zielgruppe, Palette passend zum
# dunklen Premium-Design der uebrigen Assets (#0b0d12 / Akzent #6c8cff).
BACKDROPS: dict[str, str] = {
    "free": (
        "minimal dark navy gradient surface, soft indigo light from the upper right, "
        "very subtle grain, calm and understated, plenty of negative space"
    ),
    "starter": (
        "dark blue-black studio backdrop with a single soft light beam, "
        "gentle depth of field, quiet professional mood, generous negative space"
    ),
    "pro": (
        "deep navy abstract environment, faint geometric light structures in the "
        "background, subtle blue accent glow, precise and technical yet calm"
    ),
    "business": (
        "dark architectural space, soft volumetric light, faint reflective surfaces, "
        "restrained corporate elegance, indigo accent lighting"
    ),
    "enterprise": (
        "expansive dark hall with deep perspective, cinematic low-key lighting, "
        "cool indigo rim light, serious and premium atmosphere"
    ),
}

# 4:5 ist das nuetzlichste Ad-Format; die SVG-Pipeline skaliert daraus.
SIZE = {"width": 1080, "height": 1350}


def _post(path: str, payload: dict, key: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}/{path}",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _get(path: str, key: str) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{BASE_URL}/{path}", headers={"x-api-key": key}, method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:  # noqa: BLE001 — Fehlerkoerper darf kaputt sein
            return e.code, {}


def generate_one(code: str, prompt: str, key: str, endpoint: str,
                 timeout_s: int = 300) -> pathlib.Path:
    """Erzeugt EIN Hintergrundbild und speichert es. Wirft bei Fehlschlag."""
    full_prompt = f"{prompt}, {NO_TEXT_CLAUSE}"
    submitted = _post(endpoint, {"prompt": full_prompt, **SIZE}, key)
    rid = submitted.get("request_id")
    if not rid:
        raise RuntimeError(f"Keine request_id erhalten: {submitted}")
    print(f"  {code}: eingereicht ({rid})")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status_code, data = _get(f"predictions/{rid}/result", key)
        state = data.get("status")
        if state == "completed":
            outputs = data.get("outputs") or []
            url = outputs[0] if outputs else (data.get("url") or data.get("output"))
            if not url:
                raise RuntimeError(f"Fertig, aber keine Bild-URL: {data}")
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            dest = OUT_DIR / f"{code}.png"
            with urllib.request.urlopen(url, timeout=120) as src, open(dest, "wb") as f:
                f.write(src.read())
            print(f"  {code}: gespeichert -> {dest} ({dest.stat().st_size // 1024} KB)")
            return dest
        if state == "failed" or status_code == 400:
            raise RuntimeError(f"Fehlgeschlagen: {data.get('error', data)}")
        time.sleep(3)
    raise TimeoutError(f"Zeitueberschreitung nach {timeout_s}s (request_id={rid})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Nur diese Tarife (kommagetrennt), z.B. pro,business")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="MuAPI-Modell-Endpunkt")
    ap.add_argument("--generate", action="store_true",
                    help="WIRKLICH erzeugen (kostet Credits). Ohne dies nur Dry-Run.")
    ap.add_argument("--list", action="store_true", help="Motive anzeigen und beenden")
    args = ap.parse_args()

    if args.list:
        for code, prompt in BACKDROPS.items():
            print(f"\n{code}:\n  {prompt}")
        print(f"\nAn jeden Prompt angehaengt:\n  {NO_TEXT_CLAUSE}")
        return 0

    codes = list(BACKDROPS)
    if args.only:
        wanted = [c.strip() for c in args.only.split(",") if c.strip()]
        unknown = [c for c in wanted if c not in BACKDROPS]
        if unknown:
            print(f"Unbekannte Tarife: {', '.join(unknown)}", file=sys.stderr)
            return 2
        codes = wanted

    if not args.generate:
        print(f"DRY-RUN — es wird NICHTS gesendet, keine Kosten.\n")
        print(f"Wuerde {len(codes)} Bild(er) ueber '{args.endpoint}' erzeugen "
              f"({SIZE['width']}x{SIZE['height']}):")
        for c in codes:
            print(f"  - {c}")
        print("\nJedes Bild verbraucht MuAPI-Credits. Mit --generate wirklich starten.")
        print("Text kommt NICHT aus dem Bildmodell — den legt generate.py darueber.")
        return 0

    key = os.environ.get("MUAPI_API_KEY", "")
    if not key:
        print("MUAPI_API_KEY fehlt (aus .env laden).", file=sys.stderr)
        return 2

    print(f"Erzeuge {len(codes)} Bild(er) ueber '{args.endpoint}' — kostet Credits.\n")
    failed = []
    for code in codes:
        try:
            generate_one(code, BACKDROPS[code], key, args.endpoint)
        except Exception as exc:  # noqa: BLE001 — jeder Fehler soll benannt werden
            print(f"  {code}: FEHLGESCHLAGEN — {exc}", file=sys.stderr)
            failed.append(code)

    print(f"\n{len(codes) - len(failed)}/{len(codes)} erzeugt.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
