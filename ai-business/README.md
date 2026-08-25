# ai-business — Claude-Capability-Export fuer OpenCode

Portable Sammlung der Claude-Code-Faehigkeiten aus dieser Umgebung, damit du sie spaeter mit **OpenCode** auf deinem PC nutzen oder anpassen kannst.

**Stand:** 2026-08-25 · **Konto:** `Nate8645er` · **Quelle:** Repo `Nate8645er/Nate`

> Liegt als Ordner im Repo `Nate8645er/Nate` (ein eigenes GitHub-Repo `ai-business` war aus der Sitzung nicht anlegbar — App-Recht fehlt). Vorteil: alle Marktplaetze liegen als Geschwister direkt daneben. Fuer ein separates Repo: leeres `ai-business` auf GitHub anlegen, dann laesst sich der Ordner verschieben.

## Einstieg
1. **`ai-team/EXPORT-MANIFEST.md`** — Master-Tabelle: was gefunden, was exportiert, Portierbarkeit, Auth, Status.
2. **`ai-team/OPENCODE-INTEGRATION.md`** — wie OpenCode alles einbindet (DIRECT / ADAPTABLE / CLAUDE_ONLY / AUTH_REQUIRED / NOT_TESTED).
3. **`ai-team/CAPABILITIES.md`** — Gesamtueberblick nach Wirkung.

## Struktur
```
ai-business/
├── ai-team/            # vollstaendige Inventar-Doku (11 Dateien)
│   ├── SKILLS.md  PLUGINS.md  COMMANDS.md  SUBAGENTS.md  AGENTS.md
│   ├── MCP.md  TOOLS.md  REPOSITORIES.md  CAPABILITIES.md
│   └── EXPORT-MANIFEST.md  OPENCODE-INTEGRATION.md
├── capabilities/       # kopierte, portable Dateien
│   ├── agents/         # 12 ULTRA-Agenten (eigen)
│   ├── subagents/      # 17 wshobson-Agenten (aktiviert)
│   ├── commands/       # 3 ULTRA-Commands
│   ├── skills/         # ultra-enterprise-os (eigen) + Zeiger
│   ├── tools/          # rat.py
│   ├── prompts/        # mcp.example.json, hooks-uebersicht.md
│   ├── plugins/  templates/   # Zeiger auf Geschwister-Ordner
└── tools/              # rat.py, omniroute-autostart.sh (lauffaehig)
```

## Sicherheit
Keine Secrets im Export. Kopierte Tools beziehen Keys nur aus Umgebungsvariablen (`OPENROUTER_API_KEY`). Vor Commit Secret-Scan durchgefuehrt. Grosse Fremd-Marktplaetze wurden referenziert statt dupliziert.

## Was NICHT hier ist
Anthropic-Doc-Skills (pdf/docx/…), Hook-Live-Mechanik und Claude-eingebaute Tools sind **CLAUDE_ONLY** — dokumentiert, aber nicht 1:1 nach OpenCode uebertragbar. Details in den `ai-team/`-Dateien.
