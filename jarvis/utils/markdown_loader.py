"""Liest Markdown-Dateien mit YAML-Frontmatter (Skills und Agenten).

Format:
    ---
    name: mein-name
    description: Kurzbeschreibung
    ---
    Text/Prompt der Datei ...
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger("jarvis.markdown")


def parse_markdown_with_frontmatter(path: Path) -> tuple[dict, str] | None:
    """Gibt (frontmatter, body) zurück oder None bei ungültigem Format."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("Datei %s konnte nicht gelesen werden: %s", path, e)
        return None

    if not text.startswith("---"):
        # Kein Frontmatter: Dateiname als Name, ganzer Text als Body
        return {"name": path.stem}, text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        logger.error("Ungültiges Frontmatter in %s", path)
        return None

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        logger.error("YAML-Fehler in %s: %s", path, e)
        return None

    if "name" not in frontmatter:
        frontmatter["name"] = path.stem
    return frontmatter, parts[2].strip()


def load_directory(directory: Path) -> dict[str, tuple[dict, str]]:
    """Lädt alle .md-Dateien eines Ordners. Ergebnis: {name: (meta, body)}."""
    result: dict[str, tuple[dict, str]] = {}
    if not directory.is_dir():
        logger.warning("Ordner nicht gefunden: %s", directory)
        return result
    for path in sorted(directory.glob("*.md")):
        parsed = parse_markdown_with_frontmatter(path)
        if parsed is None:
            continue
        meta, body = parsed
        result[str(meta["name"])] = (meta, body)
    return result
