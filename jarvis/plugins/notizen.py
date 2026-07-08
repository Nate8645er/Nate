"""Plugin: Notizen - schnelle Merkzettel, die Neustarts überleben."""

import json
from pathlib import Path

from jarvis.plugins.base import JarvisPlugin
from jarvis.utils.config_loader import PROJECT_ROOT


class NotizenPlugin(JarvisPlugin):
    name = "notizen"
    description = "Notizen anlegen, anzeigen und löschen (dauerhaft gespeichert)"
    commands = {
        "notiz": "Notiz speichern, z.B. /notiz Milch kaufen",
        "notizen": "Alle Notizen anzeigen",
        "notiz-weg": "Notiz löschen: /notiz-weg <nr> (oder: alles)",
    }

    def __init__(self, storage_file: Path | None = None):
        self.storage_file = storage_file or (
            PROJECT_ROOT / "data" / "memory" / "notizen.json"
        )

    def _load(self) -> list[str]:
        if self.storage_file.exists():
            try:
                return json.loads(self.storage_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return []
        return []

    def _save(self, notes: list[str]) -> None:
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.storage_file.write_text(
            json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def execute(self, command: str, args: str) -> str:
        notes = self._load()

        if command == "notiz":
            if not args.strip():
                return "Nutzung: /notiz <text> - z.B. /notiz Milch kaufen"
            notes.append(args.strip())
            self._save(notes)
            return f"Notiz Nr. {len(notes)} gespeichert: {args.strip()}"

        if command == "notizen":
            if not notes:
                return "Keine Notizen vorhanden. Lege eine an mit /notiz <text>"
            lines = [f"  {nr}. {text}" for nr, text in enumerate(notes, start=1)]
            return "Deine Notizen:\n" + "\n".join(lines)

        # /notiz-weg
        args = args.strip().lower()
        if args in {"alles", "alle"}:
            self._save([])
            return f"Alle Notizen gelöscht ({len(notes)} Stück)."
        if not args.isdigit() or not 1 <= int(args) <= len(notes):
            return "Nutzung: /notiz-weg <nr> oder /notiz-weg alles"
        removed = notes.pop(int(args) - 1)
        self._save(notes)
        return f"Gelöscht: {removed}"
