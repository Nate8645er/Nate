# JARVIS Enterprise Plugins

Dieses Verzeichnis enthält **alle 128 Plugins** aus dem zentralen Katalog
(`open_jarvis/enterprise/catalog.py`, 16 Kategorien à 8 Plugins) als echte,
ladbare Open.Jarvis-Plugins. JARVIS hat damit **sämtliche Katalog-Plugins
installiert** — dieselben 128 Plugins, die auch jeder der 1.000.000.000.000
virtuellen Mitarbeiter (und jedes Mitarbeiter-Unternehmen samt Developer-Team)
im Enterprise Live-Ticker besitzt.

Zusätzlich liegt hier das echte Funktions-Plugin **`agent_jarvis_agent`**
(JARVIS-Agent) — es meldet die Befehle des agentischen Modus (Befehle ausführen,
Shop bauen, Modell wählen inkl. Fable 5). Die Registry lädt also **129 Plugins**
(128 Katalog-Plugins + JARVIS-Agent), alle mit 0 Issues. Siehe
[`../docs/JARVIS_AGENT.md`](../docs/JARVIS_AGENT.md).

## Aufbau

Jedes Plugin ist ein eigener Ordner `plugins/<plugin_id>/` mit genau zwei Dateien:

- `plugin.json` — Manifest mit `id`, `name`, `version`, `entrypoint`,
  deutscher `description` und den beiden risikoarmen Berechtigungen
  `commands.register` und `ui.notify`.
- `main.py` — sicherer Entrypoint (nur Standardbibliothek, kein Netzwerk,
  kein Dateisystemzugriff). Beim direkten Ausführen gibt er ein JSON mit
  `plugin_id`, `kategorie` und 3–5 deutschen Sprachbefehlen aus, z. B.:

```bash
python3 plugins/medien_unterhaltung_spotify_steuerung/main.py
# {"plugin_id": "medien_unterhaltung_spotify_steuerung", "kategorie": "Medien & Unterhaltung",
#  "befehle": ["musik abspielen", "musik pausieren", "nächster titel", ...]}
```

Die `plugin_id` wird deterministisch aus Kategorie und Plugin-Name gebildet
(klein geschrieben, nur `a-z`, `0-9` und `_`), z. B. wird aus der Kategorie
„Medien & Unterhaltung" und dem Plugin „Spotify-Steuerung" die ID
`medien_unterhaltung_spotify_steuerung`.

## Wie die Registry lädt

Die Plugin-Registry entdeckt und validiert alle Plugins, **ohne Plugin-Code
auszuführen**:

```python
from open_jarvis.plugins.registry import build_plugin_registry

registry = build_plugin_registry("plugins")
print(registry["summary"])  # {'total': 128, 'blocked': 0, ...}
```

`build_plugin_registry` durchsucht `plugins/*/plugin.json`, prüft jedes
Manifest gegen das Schema (`open_jarvis/plugins/manifest.py`) sowie die
Berechtigungs-Richtlinien (`open_jarvis/plugins/permissions.py`) und liefert
für alle 128 Plugins **0 Issues**. Diese Datei (`README.md`) wird von der
Registry ignoriert, da sie kein `plugin.json` in einem Unterordner ist.

## Hervorgehoben: Enterprise-Live-Ticker

Das Plugin **`enterprise_enterprise_live_ticker`** (Kategorie „Enterprise")
ist das Flaggschiff dieses Verzeichnisses: Es verbindet die Plugin-Ebene mit
der Enterprise-Engine (`open_jarvis/enterprise/`) und dem Dashboard
(`dashboard/jarvis_live_ticker.html`). Seine Sprachbefehle:

- `live-ticker starten`
- `live-ticker stoppen`
- `belegschaft anzeigen`
- `mitarbeiter nachschlagen`
- `ticker-bericht erstellen`

## Tests

Der zugehörige Test `tests/test_enterprise_plugins.py` stellt sicher, dass
genau 128 Plugins existieren, alle Manifeste gültig sind (0 Issues,
eindeutige IDs, korrekte Berechtigungen), ein Beispiel-Entrypoint gültiges
JSON liefert und die Plugin-Namen exakt der Menge aus
`open_jarvis.enterprise.catalog.all_plugins()` entsprechen:

```bash
python3 -m pytest tests/test_enterprise_plugins.py -q
```
