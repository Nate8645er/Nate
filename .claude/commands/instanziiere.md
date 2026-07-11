---
description: Materialisiert einen der 10 Milliarden Agents/Skills/Commands als echte Datei
argument-hint: [agent|skill|command] [holding/<division>/<company>/<department>/<team>/<agent>] [skill-name]
---

Materialisiere aus dem 10-Milliarden-Adressraum: $ARGUMENTS

1. Fuehre den Generator des Plugins aus:
   `python3 <plugin-pfad>/tools/generator.py <typ> <adresse> [skill-name] --out <ziel>`
   - Agents  -> Ziel `.claude/agents/`
   - Skills  -> Ziel `.claude/skills/`
   - Commands -> Ziel `.claude/commands/`
2. Zeige die erzeugte Datei kurz und nenne die Adresse.
3. Hinweis an Nate: Die Datei laedt beim naechsten Sessionstart automatisch.
   Nur dauerhaft Bewaehrtes behalten (Befoerderungs-Regel der
   milliarden-unternehmen-Skill) — der Adressraum bleibt immer vollstaendig
   abrufbar, auch ohne materialisierte Datei.

Ohne Argumente: `python3 tools/generator.py zaehle` ausfuehren und die
Kapazitaet der drei 10-Milliarden-Raeume zeigen.
