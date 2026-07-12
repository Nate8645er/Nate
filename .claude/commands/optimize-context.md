---
description: Findet Möglichkeiten, Tokens/Kontext zu sparen (Graphify Benchmark)
---

Analysiere, wie viel Kontext/Tokens in diesem Projekt über Graphify gespart werden können.

Vorgehen:
1. Führe aus: `graphify benchmark` — misst die Token-Reduktion gegenüber dem naiven Voll-Korpus-Ansatz.
2. Prüfe `graphify-out/` auf Größe von `graph.json` und `GRAPH_REPORT.md`.
3. Prüfe, ob der Graph aktuell ist (`graphify check-update .`); veralteter Graph → `graphify update .`.
4. Gib aus: gemessene bzw. geschätzte Token-Ersparnis, Empfehlungen (z. B. wiki nutzen, Report statt Rohdateien, query-Budget senken mit `--budget`).
