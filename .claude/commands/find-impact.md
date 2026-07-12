---
description: Zeigt die Auswirkungen einer Änderung an einer Datei/Funktion (Graphify)
argument-hint: <datei-oder-symbol>
---

Ermittle über den Graphify Knowledge Graph, was von einer Änderung an `$ARGUMENTS` betroffen wäre.

Vorgehen:
1. Führe aus: `graphify affected "$ARGUMENTS"` (Reverse-Traversal, Standard-Tiefe 2).
2. Bei Bedarf zusätzlich: `graphify path "$ARGUMENTS" "<vermutetes Ziel>"` für konkrete Abhängigkeitspfade.
3. Liste die betroffenen Knoten gruppiert nach Community auf und erkläre kurz, warum sie betroffen sind.
4. Öffne höchstens die 2–3 relevantesten Dateien, falls Detailprüfung nötig ist.

Kein grep/find über das ganze Repo — der Graph ist die primäre Quelle.
