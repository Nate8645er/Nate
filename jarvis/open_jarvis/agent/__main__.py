"""CLI fuer den JARVIS-Agenten.

Beispiele:

    # Befehl ausfuehren (Vorschau, nichts wird veraendert):
    python3 -m open_jarvis.agent "baue mir einen Shop fuer Kaffee aus Aethiopien"

    # Echt ausfuehren (Dateien/Shop-Bauplan werden geschrieben):
    python3 -m open_jarvis.agent --execute "baue mir einen Shop fuer Sneaker"

    # Modell waehlen (der Fable-5-Knopf):
    python3 -m open_jarvis.agent --model fable-5 "suche nach guenstigen Fluegen"

    # Verfuegbare Modelle anzeigen:
    python3 -m open_jarvis.agent --list-models
"""

from __future__ import annotations

import argparse
import json
import sys

from open_jarvis.agent.agent import DEFAULT_WORKSPACE, JarvisAgent, render_run
from open_jarvis.agent.claude_provider import ClaudeProvider
from open_jarvis.agent.models import list_models, resolve_model


def _print_models() -> int:
    print("Verfuegbare KI-Motoren fuer den JARVIS-Agenten:\n")
    for model in list_models():
        key_hint = "kein Schluessel noetig" if not model.needs_key else f"braucht {model.env_key}"
        status = ""
        if model.provider == "claude":
            status = " · aktiv" if ClaudeProvider(model_id=model.model_id, env_key=model.env_key).available() else " · Schluessel fehlt"
        marker = "★" if model.key == "fable-5" else " "
        print(f" {marker} {model.key:<10} {model.label:<20} ({key_hint}){status}")
        print(f"     {model.description}")
    print("\nStandard: fable-5 (faellt ohne Schluessel automatisch auf 'local' zurueck).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="open_jarvis.agent", description="JARVIS-Agent — Befehle planen und ausfuehren.")
    parser.add_argument("task", nargs="*", help="Der Befehl/die Aufgabe in natuerlicher Sprache.")
    parser.add_argument("--model", "-m", default=None, help="KI-Motor (z. B. fable-5, opus-4.8, local).")
    parser.add_argument("--execute", "-x", action="store_true", help="Echt ausfuehren statt Vorschau.")
    parser.add_argument("--workspace", "-w", default=None, help="Arbeitsbereich fuer Dateien/Shops.")
    parser.add_argument("--json", action="store_true", help="Ergebnis als JSON ausgeben.")
    parser.add_argument("--list-models", action="store_true", help="Verfuegbare Modelle anzeigen und beenden.")
    args = parser.parse_args(argv)

    if args.list_models:
        return _print_models()

    task = " ".join(args.task).strip()
    if not task:
        parser.print_help()
        return 2

    try:
        model = resolve_model(args.model)
    except ValueError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2

    agent = JarvisAgent(
        model=model,
        workspace=args.workspace or DEFAULT_WORKSPACE,
        execute=args.execute,
    )
    run = agent.run(task)

    if args.json:
        print(json.dumps(run.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_run(run))
    return 0 if run.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
