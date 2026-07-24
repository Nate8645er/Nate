# Werkzeugkasten (Phase 0) — MCP-Server & Entwickler-Tools

Eine versionierte Quelle für den Toolstack. MCP-Server werden über die
Repo-`.mcp.json` in Claude Code geladen (auf **deinem** Rechner, beim Öffnen
des Repos). Diese Session läuft in einem flüchtigen Cloud-Container — hier
installierte Dienste sind nach Session-Ende weg; deshalb ist die **Config das
Artefakt**, nicht eine lokale Installation.

Status-Legende: **AKTIV** = in `.mcp.json`, läuft ohne Key · **KEY** = Config
liegt bereit, braucht deinen Token · **CLI/LIB** = kein MCP, Kommandozeile/
Bibliothek · **REF** = Referenz/Vorbild, kein Dauerdienst hier.

## 1) MCP-Server AKTIV (in `.mcp.json`, sofort nutzbar nach Claude-Code-Reload)

| Server | Paket | Zweck |
|---|---|---|
| modell-rat | `tools/modell-rat-mcp` | 9-Modelle-Rat via OpenRouter (bestehend) |
| context7 | `@upstash/context7-mcp` | Aktuelle Bibliotheks-Doku statt aus dem Gedächtnis |
| playwright | `@playwright/mcp@latest` | Browser-Automatisierung, E2E, Screenshots |
| chrome-devtools | `chrome-devtools-mcp@latest` | Performance-/Layout-Prüfung des UI |
| filesystem | `@modelcontextprotocol/server-filesystem` | Datei-Operationen im Projekt |

## 2) MCP-Server mit deinem Key (in `.mcp.json` ergänzen, Token setzen)

GitHub (Versionsverwaltung — in dieser Cloud-Session bereits vom Host bereitgestellt):
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "DEIN_TOKEN" }
}
```
Supabase (DB/Auth/Storage):
```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@supabase/mcp-server-supabase@latest", "--access-token", "DEIN_TOKEN"]
}
```
Notion:
```json
"notion": { "command": "npx", "args": ["-y", "@notionhq/notion-mcp-server"],
  "env": { "NOTION_TOKEN": "DEIN_TOKEN" } }
```
Slack:
```json
"slack": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-slack"],
  "env": { "SLACK_BOT_TOKEN": "xoxb-...", "SLACK_TEAM_ID": "T..." } }
```
Vercel (gehosteter MCP über Bridge):
```json
"vercel": { "command": "npx", "args": ["-y", "mcp-remote", "https://mcp.vercel.com"] }
```

> Secrets NIE ins Repo. Token nur lokal in deiner `.mcp.json` oder via ENV.
> Nach dem Eintragen Claude Code neu starten; Server erscheinen in `/mcp`.

## 3) CLI / Bibliotheken (kein MCP — so eingesetzt)

| Tool | Einsatz |
|---|---|
| Docker | isolierte Dev-/Test-Umgebungen (platform-backend Compose) |
| PostgreSQL | Datenbank (über Supabase oder eigenes Postgres) |
| LiteLLM | einheitlicher Modell-Zugang / Router-Grundlage |
| pandas | Tabellen/Auswertungen (Python) |
| JupyterLab | Analysen, Kostenrechnung |
| AWS CLI | Cloud-Infra, sobald über Vercel hinaus nötig |
| Open Interpreter / Aider / Continue.dev | lokale Coding-Assistenz |
| Browser Use | Web-Automatisierung für Kundenagenten (Phase 9) |
| GPT Researcher | Recherche-Agent (Phase 9) |
| Mem0 | Langzeitgedächtnis (SDK/Dienst, Key nötig) |

## 4) Welle C — Auswahl (EINES je Gruppe, Rest installiert aber ungenutzt)

- **Multi-Agent:** CrewAI · AutoGen · LangGraph → *Empfehlung: LangGraph*
  (feingranulare, prüfbare Graphen; passt zum Boss/Worker-Muster).
- **Retrieval:** LangChain · LlamaIndex → *Empfehlung: LlamaIndex*
  (schlanker für Dokument-Indexing/RAG). Endgültige Wahl in Phase 4/9.

## 5) Referenz-Apps (Vorbild, kein Dauerdienst im Cloud-Container)

n8n, Flowise, AnythingLLM (Workflow-/RAG-Referenz), Obsidian (Notizen).

## 6) Kataloge

- MCP Servers: https://github.com/modelcontextprotocol/servers
- Awesome MCP Servers: https://github.com/punkpeye/awesome-mcp-servers
- Awesome Claude Code: https://github.com/hesreallyhim/awesome-claude-code

## Aktualisieren

Die `@latest`-Einträge ziehen bei jedem Start die aktuelle stabile Version.
Update-Läufe nur **zwischen** Phasen, nicht mitten drin. Bei Problemen den
betroffenen Server in `.mcp.json` auf eine feste Version pinnen.
