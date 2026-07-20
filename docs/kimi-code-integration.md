# Kimi-Code-Integration für Claude Code

Dieses Repo enthält eine vollständige Integration des [kimi-code-mcp](https://github.com/howardpen9/kimi-code-mcp)-Servers (Version 0.4.1, gevendort unter `tools/kimi-code-mcp/`), der Claude Code mit **Kimi Code** (`kimi-for-coding`, 256K Kontext, Moonshot AI) verbindet. Damit kann Claude umfangreiche Codeanalyse-, Review- und Verifikationsaufgaben an Kimi delegieren und spart ~90 % Claude-seitige Tokens bei analyse-lastigen Aufgaben.

## Komponenten

| Komponente | Ort | Zweck |
|---|---|---|
| MCP-Server (Quellcode) | `tools/kimi-code-mcp/` | kimi-mcp-server 0.4.1 (neuer als npm-Release 0.3.0) |
| Projekt-MCP-Konfiguration | `.mcp.json` | Lädt den Server automatisch, wenn Claude Code in diesem Repo startet |
| Setup-Skript | `scripts/setup-kimi-mcp.sh` | Baut den Server, schreibt `~/.claude/mcp.json`, installiert optional die Kimi-CLI |

## Einrichtung

```bash
./scripts/setup-kimi-mcp.sh
```

Danach in Claude Code mit `/mcp` prüfen: Der Server `kimi-code` sollte mit 8 Tools erscheinen
(`kimi_query`, `kimi_verify`, `kimi_analyze`, `kimi_resume`, `kimi_list_sessions`, `kimi_status`, `kimi_cache_status`, `kimi_cache_invalidate`).

## API-Key (erforderlich für kimi_query / kimi_verify)

1. Key erstellen: [code.kimi.com](https://code.kimi.com) → Settings → API Keys (beginnt mit `sk-`).
2. Als Umgebungsvariable setzen: `export KIMICODE_API_KEY="sk-..."`
   - Lokal: in `~/.bashrc` / `~/.zshrc`.
   - **Claude Code Remote/Web:** als Umgebungsvariable in den Environment-Einstellungen hinterlegen, damit sie jede Session erbt.
3. Alternativ in `~/.kimi/config.toml` hinterlegen (siehe `tools/kimi-code-mcp/README.md`).

**Wichtig:** Den Key niemals ins Repo committen. In `.mcp.json` keinen `env`-Block mit `${KIMICODE_API_KEY}` verwenden — Claude Code expandiert unbekannte Variablen nicht, der Platzhalter würde als literaler (ungültiger) Key durchgereicht. Der Server erbt die Umgebungsvariablen automatisch.

## Kimi-CLI (nur für kimi_analyze / kimi_resume)

Die codebase-lesenden Tools benötigen zusätzlich die Kimi-CLI plus Login:

```bash
uv tool install kimi-cli   # oder: curl -L code.kimi.com/install.sh | bash
kimi login                  # OAuth im Browser
```

Die API-Tools (`kimi_query`, `kimi_verify`) funktionieren ohne CLI — nur mit API-Key.

## Hinweis für Claude Code Remote (Web/Cloud)

Die Umgebung erreicht das Internet über einen Egress-Proxy mit Allowlist. Für die Kimi-Integration müssen folgende Hosts in den Netzwerkeinstellungen der Umgebung freigegeben werden:

- `api.kimi.com` — Kimi-Code-API (kimi_query, kimi_verify)
- `code.kimi.com` — CLI-Installer/Portal (optional)

Ohne Freigabe antwortet der Proxy mit `HTTP 403: Host not in allowlist`.

## Verwendung

Claude delegiert automatisch, sobald der Server verbunden ist. Faustregeln:

- **Großes/unbekanntes Codebase verstehen** → `kimi_analyze` (CLI nötig)
- **Eigene Änderungen gegenprüfen (Second Opinion)** → `kimi_verify` (nur API-Key)
- **Schnelle Programmierfrage an ein anderes Modell** → `kimi_query` (nur API-Key)
- **Kleine Aufgaben (<10 Dateien)** → Claude liest direkt, Kimi überspringen

Diagnose bei Problemen: `kimi_status` aufrufen.
