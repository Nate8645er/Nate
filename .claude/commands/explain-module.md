---
description: Erklärt ein Modul/Konzept über den Graphify Knowledge Graph
argument-hint: <modul-oder-konzept>
---

Erkläre das Modul bzw. Konzept `$ARGUMENTS` über den Knowledge Graph.

Vorgehen:
1. Führe aus: `graphify explain "$ARGUMENTS"` — liefert den Knoten plus Nachbarschaft in Klartext.
2. Falls das Ergebnis zu dünn ist: `graphify query "Was macht $ARGUMENTS und womit hängt es zusammen?"`.
3. Fasse zusammen: Zweck, wichtigste Verbindungen (ein-/ausgehend), zugehörige Community.
4. Nur wenn der Graph nicht ausreicht, lies gezielt die vom Graph genannten Dateien — keine weiteren.
