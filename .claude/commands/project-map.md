---
description: Zeigt die Projektarchitektur über den Graphify Knowledge Graph
---

Zeige die Projektarchitektur über Graphify, ohne das Repository komplett zu durchsuchen.

Vorgehen:
1. Prüfe, ob `graphify-out/graph.json` existiert. Falls nicht: `graphify . --backend claude-cli` ausführen (oder `graphify update .` wenn nur Code geändert wurde).
2. Lies `graphify-out/GRAPH_REPORT.md` für die Community-/Architekturübersicht.
3. Ergänze bei Bedarf mit `graphify query "Projektarchitektur und Hauptmodule"`.
4. Fasse zusammen: Hauptbereiche (Communities), God Nodes (zentrale Dateien/Konzepte), wichtigste Abhängigkeiten.

Lies KEINE ganzen Quelldateien für diese Übersicht — nur Graph-Ausgaben.
