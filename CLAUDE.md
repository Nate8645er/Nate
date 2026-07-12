## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

# Graphify Token Optimization Rules

- Nutze Graphify zuerst, bevor du große Codebereiche liest.
- Frage den Knowledge Graph ab (`graphify query "<Frage>"`), bevor du Dateien öffnest.
- Öffne nur Dateien, die Graphify als relevant identifiziert.
- Vermeide komplette Repository-Scans (kein wiederholtes grep/find über das ganze Repo).
- Vermeide unnötige Wiederholungen.
- Halte Antworten, Analysen und Kontext klein und effizient.

Arbeitsablauf:
1. Graphify abfragen (`graphify query` / `explain` / `path` / `affected`)
2. Relevante Dateien bestimmen
3. Nur benötigten Code laden
4. Änderungen durchführen
5. Tests ausführen und `graphify update .` laufen lassen

Session-Workflow (jede neue Claude-Code-Session):
- Der SessionStart-Hook installiert Graphify automatisch (falls es fehlt) und prüft, ob der Graph aktuell ist.
- Bei großen Änderungen: `graphify update .` (AST-only, kostenlos) bzw. `graphify . --backend claude-cli` für volle Re-Extraktion.
- Architektur- und Dependency-Fragen laufen über den Graph, nicht über Datei-Scans.

Verfügbare Commands: `/project-map`, `/find-impact <datei>`, `/explain-module <name>`, `/optimize-context`.

# Brain / Projektgedächtnis

Persistentes Gedächtnis liegt in `.claude/brain.md`. Dort stehen Projekt-Historie, getroffene Entscheidungen und Session-Zusammenfassungen. Bei relevanten neuen Arbeiten: kurzen Eintrag ergänzen (Datum + was/warum). Lies es zu Beginn substanzieller Aufgaben.
