# MCP-Server

> **SICHERHEIT:** Hier stehen **keine** Tokens, API-Keys, Passwoerter oder Cookies. MCP-Server werden auf der claude.ai-/Umgebungsebene konfiguriert (nicht in diesem Repo). Fuer jeden Key gilt: `API_KEY=REQUIRED_BY_USER`. Es gibt **keine** Projekt-`.mcp.json` (`NOT FOUND`).

Die folgenden Server wurden **in dieser Sitzung beobachtet** (aus der Laufzeit, nicht aus einer Konfigurationsdatei). Sie sind an das claude.ai-Konto gebunden und meist per OAuth/Connector authentifiziert.

## Beobachtete MCP-Server (10)

| Name | Zweck | Server/Paket | Auth | Env / Secret | OpenCode |
|---|---|---|---|---|---|
| **Shopify** | Store-Management (Produkte, Orders, Inventar, Collections, Discounts, GraphQL Admin API) | Shopify MCP (Connector) | JA (OAuth Store) | `SHOPIFY_*=REQUIRED_BY_USER` | AUTH_REQUIRED — Server existiert auch fuer OpenCode, eigener Login noetig |
| **Facebokk_Ads** | Meta-Werbung: Kampagnen, Ad Sets, Ads, Creatives, Pixel/CAPI, Catalog, Insights | Meta Ads MCP | JA (OAuth Meta) | `META_*=REQUIRED_BY_USER` | AUTH_REQUIRED |
| **DSERS** | Dropshipping-Automation (Produkt-Import/Push, Supplier-Remap) | DSers MCP | JA (OAuth accounts.dsers.com) | — (OAuth) | AUTH_REQUIRED |
| **Gmail** | E-Mail lesen/senden/labeln/entwuerfe | Google Gmail MCP | JA (OAuth Google) | — (OAuth) | AUTH_REQUIRED |
| **Google_Drive** | Dateien lesen/erstellen/teilen/suchen | Google Drive MCP | JA (OAuth Google) | — (OAuth) | AUTH_REQUIRED |
| **Higgfield** | Medien-Generierung (Bild/Video/Audio/3D), TikTok-Publish | Higgsfield MCP | JA (Konto) + Credits | `HIGGSFIELD_*=REQUIRED_BY_USER` | AUTH_REQUIRED + kostenpflichtig |
| **Chatplaceio** | Bots/Automations/Mailings/AI-Agents/Virale-Content | ChatPlace MCP | JA (Konto) | `CHATPLACE_*=REQUIRED_BY_USER` | AUTH_REQUIRED |
| **Anthropic_Economic_Index** | Oeffentlicher Datensatz zur Claude-Nutzung | Anthropic MCP | NEIN | — | DIRECT (oeffentlich) |
| **github** | GitHub (PRs, Issues, Code, Actions) | GitHub MCP | JA (App/Token) | `GITHUB_TOKEN=REQUIRED_BY_USER` | AUTH_REQUIRED |
| **Claude_Code_Remote** | Sitzungs-/Trigger-/Repo-Verwaltung (claude-code-remote) | intern | JA (Sitzung) | — | CLAUDE_ONLY |

## Lokaler Zusatz-"Server" (kein MCP, aber modell-Routing)
- **OmniRoute** — lokaler Router auf `http://localhost:20128` (OpenAI-kompatible API, SSE-Streaming, OpenRouter-Katalog). Wird von `tools/omniroute-autostart.sh` beim Sitzungsstart hochgefahren. Braucht `OPENROUTER_API_KEY` (Umgebungsvariable, **nie im Repo**). Wird von `tools/rat.py` und Agent `omni-team` genutzt.

## Konfigurations-Vorlage (ohne Secrets)
Eine sichere Beispielstruktur liegt unter `capabilities/prompts/mcp.example.json` — nur Platzhalter, keine echten Werte.

## OpenCode-Hinweis
OpenCode unterstuetzt MCP-Server. Uebertragbar ist der **Servertyp** (welches Paket, welcher Zweck), **nicht** die Anmeldung. Jeder Server muss in OpenCode neu authentifiziert werden (OAuth-Flow oder eigener Key). Interaktiv authentifizierte Server koennen in Headless-/Cron-Laeufen fehlen.

## NOT FOUND
- Keine `.mcp.json` im Projekt.
- Keine gespeicherten Credentials im Repo (bewusst — siehe SICHERHEIT).
