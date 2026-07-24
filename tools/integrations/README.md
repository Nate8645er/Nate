# Claude-Code-Integrationen (Tools)

Offizielle SDK-/API-Anbindungen **für die Arbeit in Claude Code** (mich + die
Subagenten) – bewusst **getrennt vom KI-System** (`ai-command-center/`), damit
dessen Build/Funktionen unberührt bleiben.

Sichere Schlüssel-Verwaltung: alle Keys **nur** in `.env` (gitignored), nie im
Code. Vorlage: `cp .env.example .env` und Werte eintragen.

Selbsttest (lädt SDKs, prüft Konfiguration, **keine** kostenpflichtigen Aufrufe):
```bash
cd tools/integrations && npm install && npm test
```
Update-Prüfung: `npm run updates` (zeigt veraltete Pakete via `npm outdated`).

## Status je Dienst (offiziell geprüft)

| Dienst | Offiziell? | Umgesetzt | Aktivierung |
|---|---|---|---|
| **Vercel AI SDK** (`ai`) | ✅ npm | ✅ installiert + getestet | Provider-Key (z. B. `OPENAI_API_KEY`) |
| **Runway** (`@runwayml/sdk`) | ✅ npm | ✅ installiert + getestet | `RUNWAY_API_KEY` |
| **v0 / Vercel** (`v0-sdk`) | ✅ npm | ✅ installiert + getestet | `V0_API_KEY` |
| **GitHub** | ✅ (CLI/API) | ✅ **bereits via GitHub-MCP aktiv** | – (Harness stellt `mcp__github__*` bereit) |
| **GitHub Copilot** | ⚠️ nur Abo/Editor | ❌ nicht integriert | siehe unten |
| **Dia / diagrams.net (draw.io)** | ❌ keine offizielle SDK/API | ❌ nicht integriert | siehe unten |

### Vercel AI SDK (`ai`)
Offizielles TypeScript-SDK von Vercel (`generateText`, `streamText`, Tools,
strukturierte Ausgaben). Provider-agnostisch – Key je Anbieter (OpenAI,
Anthropic, …). Installiert samt `@ai-sdk/openai`. Nutzbar in Skripten der Agenten.

### Runway (`@runwayml/sdk`)
Offizielles SDK der Runway-API (Video-/Bildgenerierung). Läuft headless, braucht
`RUNWAY_API_KEY` (kostenpflichtig). Ohne Key meldet der Test ehrlich
„nicht konfiguriert". Docs: https://dev.runwayml.com

### v0 (`v0-sdk`)
Offizielles SDK der v0-Platform-API (generative UI). Braucht `V0_API_KEY`
(v0.dev → API Keys). Ideal, um UI-Entwürfe programmatisch zu erzeugen.

### GitHub
In dieser Claude-Code-Umgebung ist GitHub **bereits offiziell integriert** über
den **GitHub-MCP-Server** (`mcp__github__*`) – damit erledige ich PRs, Reviews,
CI-Status usw. Die separate `gh`-CLI ist hier **nicht** der vorgesehene Weg und
hätte ohne hinterlegtes Token ohnehin keine Berechtigung. → Kein Zusatz-Setup nötig.

### GitHub Copilot — **keine offizielle Claude-Code-Integration**
Copilot ist ein **abonnementpflichtiges Editor-Produkt** (Code-Vervollständigung
in VS Code/JetBrains) bzw. eine `gh copilot`-Extension, die ein Copilot-Abo +
GitHub-Auth verlangt. Es gibt **kein offizielles SDK/keine API**, um Copilot als
Werkzeug in Claude Code einzubinden – und funktional überschneidet es sich mit
Claude Code selbst. Gemäss Vorgabe **keine inoffizielle/unsichere Anbindung**;
daher nicht integriert.

### Dia / diagrams.net (draw.io) — **keine offizielle SDK/API**
diagrams.net (draw.io) ist eine Web-/Desktop-App zum Zeichnen von Diagrammen.
Es gibt **keine offiziell unterstützte API/SDK** für eine programmatische
Claude-Code-Integration. **Sichere, offizielle Alternative, die bereits geht:**
Ich erzeuge Diagramme als **Mermaid** (nativ renderbar) oder als draw.io-XML zum
Import. Keine inoffiziellen Integrationen.

> Hinweis: „Dia" kann auch den Dia-Browser (The Browser Company) meinen – dieser
> ist ein Endnutzer-Browser ohne SDK/API und ebenfalls nicht integrierbar.
