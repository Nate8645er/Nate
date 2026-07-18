# Setup-Notizen: meta-mcp (Meta Ads MCP-Server)

Eingerichtet am 2026-07-18 aus dem Upstream-Snapshot
[serkanhaslak/meta-mcp](https://github.com/serkanhaslak/meta-mcp) (main, v1.0.0)
nach `./meta-mcp`. 77 Tools für den kompletten Meta-Ads-Lebenszyklus
(Kampagnen, Ad Sets, Ads, Creatives, Audiences, Insights, Pixel,
Conversions, Automatisierungs-Regeln, Batch-API, …).

## Architektur der Anbindung

meta-mcp ist ein **HTTP-Server** (Fastify, Streamable-HTTP-MCP auf
`/mcp`, REST auf `/api/v1/*`), kein stdio-Server. Anbindung an Claude
Code über `scripts/meta-mcp/launch.sh` (registriert in `.mcp.json`):

1. legt beim ersten Start `meta-mcp/.env` an (gitignored) — mit
   generiertem `MCP_API_KEY` (schützt den lokalen Port) und
   Platzhaltern für die Meta-Zugangsdaten;
2. installiert/baut das Projekt bei Bedarf (`npm install && npm run
   build` — Container sind ephemer, `node_modules`/`dist` sind nicht
   committet);
3. startet den Server auf Port 3000, falls er nicht läuft
   (Log: `meta-mcp/server.log`);
4. verbindet Claude Code per `npx mcp-remote` (stdio↔HTTP-Bridge) mit
   `Authorization: Bearer <MCP_API_KEY>`.

## Zugangsdaten (erforderlich!)

In `meta-mcp/.env` eintragen (Datei ist gitignored, Werte niemals
committen):

```
META_ACCESS_TOKEN=<System-User-Token>
META_AD_ACCOUNT_ID=act_<deine-Werbekonto-ID>
```

Token besorgen (Meta Business Suite):

1. https://business.facebook.com/settings/system-users → System-User
   anlegen (oder bestehenden nutzen)
2. System-User dem Werbekonto mit **Admin**-Rolle zuweisen
3. Token generieren mit Berechtigungen: `ads_management`, `ads_read`,
   `pages_read_engagement` (optional `leads_retrieval` für Lead-Formulare)
4. Werbekonto-ID: Ads Manager → Kontoübersicht (Format `act_123456789`)

Ohne echten Token startet der MCP-Handshake zwar (Platzhalter), aber
jeder Tool-Aufruf schlägt mit einem OAuth-Fehler der Graph API fehl.

## Hinweise

- Der Server bindet auf `0.0.0.0:3000` **im Container** (nicht öffentlich
  erreichbar); zusätzlich schützt der generierte `MCP_API_KEY` alle
  `/mcp`- und `/api/*`-Routen.
- Rate-Limiting/Retry gegen die Graph API ist eingebaut (BUC-adaptiv).
- 77 Tools sind ein großes Manifest — in dieser Umgebung lädt Claude
  Code MCP-Tools deferred (via ToolSearch), das Manifest kostet also
  erst bei Nutzung Kontext.
- `meta-mcp/.env`, `server.log`, `node_modules/`, `dist/` sind in
  `.gitignore` ausgeschlossen.

## Funktionstest (2026-07-18, dieser Container)

- Build ✓ (`tsc`, Node 22), Health ✓
  (`{"status":"ok","tools":77,"modes":["mcp","rest"]}`)
- `launch.sh`-Kette ✓: Server-Autostart → `mcp-remote`-Bridge →
  `initialize` ✓ → `tools/list` ✓ (77 Tools)
- Echte Graph-API-Aufrufe stehen noch aus, bis der echte
  `META_ACCESS_TOKEN` eingetragen ist (siehe oben).
