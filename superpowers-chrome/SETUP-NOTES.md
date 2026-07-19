# Setup-Notizen: superpowers-chrome in Nates Marketplace

Installiert am 2026-07-18 aus dem Upstream-Snapshot
[obra/superpowers-chrome](https://github.com/obra/superpowers-chrome) (main, v3.0.2)
als Plugin `superpowers-chrome@nate-marketplace`.

## Was das Plugin bietet

- **MCP-Server `chrome`** mit einem einzigen Tool `use_browser`
  (navigate, click, type, select, eval, extract, screenshot, tabs, …).
  DOM-verändernde Aktionen erzeugen automatisch Captures
  (page.html, page.md, screenshot.png, DOM-Zusammenfassung).
- **Skill `browsing`**: CLI `skills/browsing/chrome-ws` mit 17 Kommandos
  (start, tabs, new, close, navigate, wait-for, wait-text, click, fill,
  select, eval, extract, attr, html, screenshot, markdown, raw).
- **Agent `browser-user`** (agents/browser-user.md).
- Zero Runtime-Dependencies; `mcp/dist/index.js` ist vorgebaut und committed.

## Änderungen gegenüber Upstream

1. **`mcp/launch.cjs` (neu)** — Umgebungsbewusster Starter für den MCP-Server:
   - Setzt `CHROME_WS_BROWSER=/opt/pw-browsers/chromium`, wenn kein Chrome
     unter den Standardpfaden liegt (Claude-Code-Remote-Container haben nur
     den Playwright-Chromium).
   - Hängt `--proxy-server=$HTTPS_PROXY --ssl-version-max=tls1.2` an
     `CHROME_EXTRA_ARGS` an, wenn ein Egress-Proxy gesetzt ist (Pflicht in
     Remote-Sessions). Das TLS-1.2-Limit ist nötig, weil der Egress-Gateway
     Chromes TLS-1.3-ClientHello mit Connection-Reset beantwortet (per
     Chrome-Netlog verifiziert; auch mit deaktiviertem ML-KEM/ECH). Die
     Zertifikatsprüfung bleibt vollständig aktiv; nicht inspizierte Hosts
     werden mit ihrer echten öffentlichen Zertifikatskette durchgereicht.
   - Auf normalen Rechnern (Chrome installiert, kein Proxy) verhält er sich
     identisch zum direkten Start von `mcp/dist/index.js`.
2. **`.claude-plugin/plugin.json`** — `mcpServers.chrome.args` zeigt auf
   `mcp/launch.cjs` statt `mcp/dist/index.js`.
3. **`skills/browsing/lib/chrome-process.js`** — respektiert jetzt (wie die
   CLI `chrome-ws` bereits) die Env-Variable `CHROME_WS_BROWSER` zur
   Browser-Auswahl. Ohne diese Variable unverändertes Verhalten.
4. **`.private-journal/` entfernt** (Entwickler-Notizen des Upstream-Autors,
   nicht Teil der Distribution).

## Änderungen an Repo-Konfiguration

- **`.claude-plugin/marketplace.json`**: Plugin-Eintrag `superpowers-chrome`
  (source `./superpowers-chrome`) hinzugefügt.
- **`.claude/settings.json`**: `"superpowers-chrome@nate-marketplace": true`
  unter `enabledPlugins` hinzugefügt.

Das Plugin wird damit in jeder neuen Claude-Code-Session, die dieses Repo
nutzt, automatisch geladen (MCP-Server + Skill + Agent). In einer bereits
laufenden Session ist ein Neustart der Session nötig.

## Umgebungsvariablen (optional)

| Variable | Wirkung |
| --- | --- |
| `CHROME_WS_BROWSER` | Pfad zum Browser-Binary (überschreibt Auto-Erkennung) |
| `CHROME_WS_PORT` / `--port=N` | Fester Debug-Port (Standard: dynamisch 9222–12111) |
| `CHROME_WS_PROFILE` | Festes Profil, um einen Chrome zwischen Prozessen zu teilen |
| `CHROME_EXTRA_ARGS` | Zusätzliche Chrome-Flags (Launcher ergänzt Proxy automatisch) |
| `--headless` (MCP-Arg) | Headless erzwingen; ohne Flag Auto-Erkennung über DISPLAY |

## Bekannte Einschränkungen in Remote-Containern

- `chrome-ws start` (CLI) startet Chrome immer **headed** und scheitert ohne
  Display. Workaround: Chrome über den MCP-Server starten lassen (headless-
  Auto-Erkennung) oder manuell headless starten und die CLI-Kommandos gegen
  den laufenden Chrome verwenden (`CHROME_WS_PORT` passend setzen).
- Erreichbare Domains sind durch die Egress-Policy der Umgebung begrenzt;
  blockierte Hosts liefern Verbindungsfehler.

## Funktionstest (2026-07-18, Claude-Code-Remote-Container)

MCP-Server über `mcp/launch.cjs` per stdio JSON-RPC getestet — ohne Symlinks
oder manuell gesetzte Env-Variablen, exakt wie das Plugin startet:

- `initialize` ✓ (`chrome-mcp-server` 3.0.2), `tools/list` ✓ (`use_browser`)
- Launcher erkannte Playwright-Chromium und Session-Proxy automatisch ✓
- Chrome-Autostart headless (DISPLAY-Auto-Erkennung) ✓
- `navigate https://example.com` ✓ → „Example Domain", Auto-Capture
  (page.html, page.md, Screenshot-PNG, Console-Log) erzeugt ✓
- `eval document.title` ✓ → „Example Domain"
