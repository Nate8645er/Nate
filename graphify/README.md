# Graphify

**Wissensgraph für deine Codebase.** Läuft einmal, liest die komplette Code-Base
und baut einen vollständigen Wissensgraphen — jede Beziehung, jede Verbindung,
jede architektonische Entscheidung. Danach navigiert Claude einfach durch den
Graphen, statt Dateien neu zu lesen: **~70 % weniger Token-Verbrauch.**

Keine Abhängigkeiten — reine Python-Standardbibliothek (Python ≥ 3.10).

## Installation

```bash
pip install ./graphify
# oder ohne Installation direkt aus dem Repo:
PYTHONPATH=graphify python3 -m graphify --help
```

## Benutzung

### 1. Einmal scannen

```bash
$ graphify scan .
Scanned 7 files in 0.0s
65 nodes, 289 edges, 2 communities
Graph saved to .graphify/graph.json
```

### 2. Graph abfragen statt Dateien lesen

```bash
$ graphify explain "APIRouter"
Node: APIRouter
  Source:    routing.py L2210
  Community: 2
  Degree:    47

Connections (47):
  --> RequestValidationError [uses] [INFERRED]
  --> Dependant [uses] [INFERRED]
  --> .get() [method] [EXTRACTED]
  <-- __init__.py [imports] [EXTRACTED]
  ...
```

```bash
$ graphify path "FastAPI" "ModelField"
Shortest path (3 hops):
FastAPI
  --uses--> DefaultPlaceholder
  <--references-- get_request_handler()
  --references--> ModelField

3 hops. Zero files opened.
```

Weitere Befehle:

| Befehl | Zweck |
|---|---|
| `graphify scan [pfad]` | Codebase scannen, Graph nach `.graphify/graph.json` schreiben |
| `graphify explain "<Name>"` | Knoten erklären: Quelle, Community, Grad, alle Verbindungen |
| `graphify path "<A>" "<B>"` | Kürzesten Beziehungspfad zwischen zwei Symbolen finden |
| `graphify search "<Query>"` | Knoten per Name suchen |
| `graphify stats` | Überblick: Knoten, Kanten, Communities, Top-Hubs |
| `graphify mcp` | MCP-Server (stdio) für Claude Code starten |

## Integration mit Claude Code

Graphify bringt einen eingebauten MCP-Server mit (keine Abhängigkeiten):

```bash
graphify scan .                                   # einmalig
claude mcp add graphify -- python3 -m graphify mcp
```

Danach stehen Claude die Tools `graphify_explain`, `graphify_path`,
`graphify_search` und `graphify_stats` zur Verfügung — Claude beantwortet
Architekturfragen über den Graphen, ohne Dateien zu öffnen. Dein
Zwanzig-Dollar-Plan wird quasi kostenlos zum Hundert-Dollar-Plan.

## Wie der Graph gebaut wird

- **Knoten:** Dateien, Klassen, Funktionen, Methoden
- **Kanten:** `defines`, `method`, `imports`, `inherits`, `calls`, `uses`, `references`
- **`[EXTRACTED]`** — direkt aus dem Python-AST bzw. expliziten Imports abgeleitet
- **`[INFERRED]`** — über globale Namensauflösung über Dateigrenzen hinweg erschlossen
- **Communities** — architektonische Cluster per Label-Propagation
- Python wird vollständig per AST analysiert; JavaScript/TypeScript heuristisch

## Tests

```bash
python3 -m pytest graphify/tests/ -q
```
