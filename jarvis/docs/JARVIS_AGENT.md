# JARVIS-Agent — Befehle wirklich ausführen (wie Claude Code)

Der **JARVIS-Agent** gibt Jarvis die Fähigkeit, gesprochene oder getippte Befehle
tatsächlich auszuführen — nach demselben Prinzip wie Claude Code:

```
Befehl  →  Planen (KI-Modell oder lokal)  →  Werkzeuge ausführen  →  Ergebnis berichten
```

Du sagst z. B. *„baue mir einen Shop für Kaffee namens Bergbohne"*, und der Agent
plant die Schritte, ruft das passende Werkzeug auf und liefert dir einen fertigen
Shop-Bauplan.

---

## Der Modell-Auswahlknopf (inkl. Fable 5)

Der Agent kann mit verschiedenen KI-Motoren planen. **Fable 5 ist das Standardmodell.**

| Modell | ID | Motor | Schlüssel |
|---|---|---|---|
| **Fable 5** ★ | `claude-fable-5` | Claude | `ANTHROPIC_API_KEY` |
| Claude Opus 4.8 | `claude-opus-4-8` | Claude | `ANTHROPIC_API_KEY` |
| Claude Sonnet 5 | `claude-sonnet-5` | Claude | `ANTHROPIC_API_KEY` |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Claude | `ANTHROPIC_API_KEY` |
| Groq (Llama) | `llama-3.1-8b-instant` | Groq | `GROQ_API_KEY` |
| **Lokal** | – | keyless | keiner |

```bash
python3 -m open_jarvis.agent --list-models      # alle Motoren anzeigen
python3 -m open_jarvis.agent --model fable-5 "..."   # mit Fable 5 planen
```

> **Ehrlich:** Damit der Agent wirklich mit Fable 5 / Claude plant, brauchst du einen
> Anthropic-API-Schlüssel in der Umgebungsvariable `ANTHROPIC_API_KEY`.
> **Ohne Schlüssel** fällt der Agent automatisch auf den **lokalen, kostenlosen Planer**
> zurück — Jarvis bleibt also immer bedienbar.

Schlüssel setzen:

```bash
export ANTHROPIC_API_KEY="dein-schluessel"     # Linux/macOS
setx ANTHROPIC_API_KEY "dein-schluessel"        # Windows
```

---

## Benutzung

```bash
# Vorschau (nichts wird verändert — zeigt nur den Plan):
python3 -m open_jarvis.agent "baue mir einen Shop für handgemachte Kerzen namens Wachswerk"

# Echt ausführen (schreibt Dateien / Shop-Bauplan):
python3 -m open_jarvis.agent --execute "baue mir einen Shop für Sneaker"

# Anderes Modell:
python3 -m open_jarvis.agent --model opus-4.8 --execute "..."

# Eigener Arbeitsbereich + JSON-Ausgabe:
python3 -m open_jarvis.agent --execute --workspace ./mein_ordner --json "..."
```

Standard-Arbeitsbereich: `~/.jarvis/agent_workspace`.

**Vorschau vs. Ausführen:** Ohne `--execute` läuft ein gefahrloser Trockenlauf
(du siehst, *was* passieren würde). Erst mit `--execute` werden Dateien/Shop-Baupläne
wirklich geschrieben.

---

## Werkzeuge des Agenten

| Werkzeug | Was es tut |
|---|---|
| `shop_bauen` | Erzeugt einen kompletten, verkaufsfertigen **Shop-Bauplan** (Name, Slogan, Farbwelt, Kollektionen, Produkte mit CHF-Preisen, Checkliste) als `.md` + `.json` |
| `web_suche` | Bereitet eine sichere Google-Suche vor |
| `webseite` | Öffnet eine Webseite (nach URL-Sicherheitsprüfung) |
| `app_starten` | Startet eine Desktop-Anwendung |
| `datei_schreiben` / `datei_lesen` | Dateien im Arbeitsbereich (streng pfadsicher) |
| `notiz` | Legt eine Notiz/Erinnerung ab |
| `plugins` | Listet die 128 verfügbaren Jarvis-Plugins auf |

**Sicherheit:** Datei-Werkzeuge bleiben strikt im Arbeitsbereich (`path_safety`), es gibt
**keine** beliebige Shell-Ausführung, und URLs werden geprüft. Vom KI-Modell
vorgeschlagene, unbekannte Werkzeuge werden verworfen.

---

## Shops & Unternehmen bauen

Das Werkzeug `shop_bauen` erzeugt einen **vollständigen Bauplan** — kein live auf
Shopify erstellter Shop. Den Bauplan (Produkte, Preise, Kollektionen, Farbwelt,
Umsetzungs-Checkliste) kannst du 1:1 in Shopify umsetzen.

```bash
python3 -m open_jarvis.agent --execute "baue einen Shop für Bio-Tee namens Blattgold"
# → ~/.jarvis/agent_workspace/shops/blattgold/shop_plan.md  (+ .json)
```

> **Ehrliche Einordnung:** Ein automatisch erzeugter Leer-Shop hat noch keinen
> Marktwert. Wert entsteht durch echte Produkte, Umsatz und Kundschaft. Der Bauplan
> ist dein Startpunkt — nicht das fertige, verkaufsfähige Unternehmen.

---

## Python-API

```python
from open_jarvis.agent import JarvisAgent

agent = JarvisAgent(model="fable-5", execute=True)
run = agent.run("baue mir einen Shop für Kaffee namens Bergbohne")

print(run.plan.final)          # Abschlussnachricht
for outcome in run.outcomes:   # einzelne Schritte
    print(outcome.tool, outcome.result.summary)
print(run.to_dict())           # alles als JSON-fähiges dict
```

---

## Architektur

```
open_jarvis/agent/
├── models.py          Modell-Registry (Fable 5, Opus, Sonnet, Haiku, Groq, lokal)
├── claude_provider.py Anthropic-Messages-API-Client (Fable 5 / Claude), keyless-sicher
├── planner.py         LocalPlanner (keyless) + ClaudePlanner (mit Fallback)
├── tools.py           Werkzeug-Registry (sicher, pfadgeschützt)
├── shop_builder.py    deterministischer Shop-Bauplan-Generator
├── agent.py           Agenten-Schleife: Plan → Werkzeuge → Bericht
└── __main__.py        CLI
```

Der lokale Planer ist **deterministisch** und **offline** — dieselbe Aufgabe ergibt
denselben Plan. Der Claude-/Fable-Planer nutzt bei vorhandenem Schlüssel das Modell
und fällt bei jedem Problem sauber auf den lokalen Planer zurück.
