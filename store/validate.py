#!/usr/bin/env python3
"""Strukturelle Validierung der Liquid-/JSON-Dateien im Store-Theme.

Kein Shopify-CLI in der CI/Entwicklungsumgebung verfuegbar -> ersetzt keine
echte Theme-Check-Pruefung, faengt aber die haeufigsten Fehler ab:
unbalancierte Liquid-Tags/Variablen, ungueltiges Schema-JSON, {% schema %}
ausserhalb von sections/ (nur dort gueltig).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
TAG_PAIRS = ["if", "for", "comment", "schema", "capture", "unless"]


def check_file(path: pathlib.Path) -> list[str]:
    errors = []
    s = path.read_text(encoding="utf-8")

    for tag in TAG_PAIRS:
        opens = len(re.findall(rf"\{{%-?\s*{tag}\b", s))
        closes = len(re.findall(rf"\{{%-?\s*end{tag}\b", s))
        if opens != closes:
            errors.append(f"{tag}: {opens} geoeffnet, {closes} geschlossen")

    if s.count("{{") != s.count("}}"):
        errors.append(f"Variablen unbalanciert: {{{{={s.count('{{')}, }}}}={s.count('}}')}")

    schema_match = re.search(r"\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}", s, re.S)
    if schema_match:
        if "sections" not in path.parts:
            errors.append("{% schema %} ausserhalb von sections/ — nur dort gueltig")
        try:
            schema = json.loads(schema_match.group(1))
        except json.JSONDecodeError as e:
            errors.append(f"schema-JSON ungueltig: {e}")
        else:
            errors.extend(_check_empty_defaults(schema))

    return errors


def _check_empty_defaults(schema: dict) -> list[str]:
    """Shopify lehnt bei der Theme-Datei-Upload-API ein `"default": ""` auf
    Text-artigen Einstellungen ab ("default darf nicht leer sein") -- ein
    struktureller JSON-Check allein sieht das nicht, hat aber schon einmal
    einen Datei-Upload live scheitern lassen (features.liquid, 27.07.),
    ohne dass diese Validierung hier das vorher bemerkt haette."""
    errors = []

    def scan(settings, where: str):
        for entry in settings or []:
            if isinstance(entry, dict) and entry.get("default") == "":
                errors.append(
                    f"{where}: setting '{entry.get('id')}' (type={entry.get('type')}) "
                    "hat \"default\": \"\" -- Shopify lehnt das beim Upload ab, "
                    "Feld ohne default lassen oder echten Wert setzen"
                )

    scan(schema.get("settings"), "settings")
    for block in schema.get("blocks") or []:
        scan(block.get("settings"), f"blocks[{block.get('type')}]")

    return errors


def main() -> int:
    liquid_files = sorted(ROOT.rglob("*.liquid"))
    json_files = sorted(ROOT.rglob("*.json"))

    ok = True
    for f in liquid_files:
        errs = check_file(f)
        rel = f.relative_to(ROOT)
        if errs:
            ok = False
            print(f"FEHLER {rel}:")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"OK      {rel}")

    for f in json_files:
        rel = f.relative_to(ROOT)
        try:
            json.loads(f.read_text(encoding="utf-8"))
            print(f"OK      {rel}")
        except json.JSONDecodeError as e:
            ok = False
            print(f"FEHLER {rel}: {e}")

    if not liquid_files:
        print("Keine .liquid-Dateien gefunden.")
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
