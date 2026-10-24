# Architektur — JARVIS AI OS

## Überblick

```
                    ┌─────────────────────────────┐
                    │        HUD-Dashboard         │  web/ (vanilla JS)
                    │  Chat · Voice · Manager · Logs│
                    └───────┬──────────┬───────────┘
                       REST │          │ WebSocket (Events, Chat, Approvals)
                    ┌───────┴──────────┴───────────┐
                    │        FastAPI (api/)        │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │           K E R N E L        │  kernel.py
                    └┬────┬────┬────┬────┬────┬───┬┘
                     │    │    │    │    │    │   │
              EventBus Approvals Memory LLM Skills Agents … 
                     │                             │
        ┌────────────┴───────────┐     ┌───────────┴─────────────┐
        │ Scheduler · Workflows  │     │  Company (org.yaml)     │
        │ Plugins · Voice        │     │  19+ Agenten, parallel  │
        └────────────────────────┘     └─────────────────────────┘
```

Der **Kernel** (`jarvis/kernel.py`) besitzt alle Subsysteme und verdrahtet
sie beim Boot. Die API-Schicht spricht ausschließlich mit dem Kernel.

## Subsysteme

| Modul | Verantwortung |
|---|---|
| `core/events.py` | Async-Event-Bus (Pub/Sub, Wildcards, Historie). Alle Komponenten kommunizieren über Events → lose Kopplung. |
| `core/approvals.py` | Freigabe-Gate: riskante Aktionen blockieren, bis der Benutzer zustimmt (Event → UI-Modal → resolve). |
| `core/orchestrator.py` | Nimmt Benutzeräußerungen an, routet an Agenten (`@name`, Keyword-Routing, sonst CEO), verkündet Ergebnisse (Chat + TTS). |
| `agents/` | `AgentSpec` (Daten) + `Agent` (async Worker mit Inbox). Default-Verhalten: LLM-Tool-Loop mit Gedächtnis-Kontext. Beliebig viele Agenten laufen parallel (je ein asyncio-Task). |
| `company/` | Virtuelle Firma: staffing aus `org.yaml`, `hire()`/`fire()` zur Laufzeit, Org-Chart-API. |
| `skills/` | Skill = typisierte async Funktion + Kategorie + Risiko. Registry führt Approval-Gate + Telemetrie-Events aus. Agenten sehen nur Skills ihrer Kategorien (Least Privilege). |
| `plugins/` | Verzeichnis-Scan (`plugin.json`), dynamischer Import, `setup(kernel)`/`teardown(kernel)`, Skills werden dem Plugin zugeordnet und bei Deaktivierung entfernt. Zustand persistiert. |
| `memory/` | 3 Ebenen: Kurzzeit (Ringpuffer je Session), Langzeit (SQLite: Fakten/Präferenzen/Projekte + Gesprächsprotokoll), Vektor (Chroma/Qdrant optional, eingebauter Fallback). `context_pack()` baut LLM-Kontext. |
| `llm/` | Provider-Abstraktion (Anthropic, OpenAI-kompatibel, Ollama, Echo-Fallback), Tool-Calling-Schema aus Skills. |
| `voice/` | Wake Word (openwakeword), STT (faster-whisper), TTS (piper) — alle optional; Browser-Fallback über Web Speech API. `voice.speak`-Events tragen optional WAV (base64). |
| `automation/` | Scheduler (Erinnerungen, Termine, wiederkehrende Jobs) → `reminder.due`-Events. |
| `workflows/` | Deklarative Multi-Step-Automationen (YAML/JSON), Schritte = Skill oder Agent, `{{steps.x}}`-Templating. |

## Entwurfsentscheidungen

1. **Events statt Direktaufrufe** — jede Statusänderung ist ein Event; UI,
   Logs und künftige Integrationen (Redis-Bus für Multi-Prozess) hängen sich
   nur an den Bus.
2. **Agenten sind Daten** — ein neuer Spezialist ist ein YAML-Eintrag, kein
   Code. Custom-Verhalten via `AgentRegistry.register_class()`.
3. **Graceful Degradation** — jede optionale Abhängigkeit (Voice, Vektor-DB,
   LLM-Keys, OCR/PDF) fällt auf eine funktionierende Alternative zurück statt
   den Boot zu verhindern. Kern-Installation = 7 kleine Pakete.
4. **Least Privilege + Approval** — Agenten erhalten nur ihre Skill-Kategorien;
   Skills deklarieren ehrliche Risiko-Level; alles ab Threshold wartet auf den
   Benutzer. Session-Grants vermeiden Nerv-Dialoge.
5. **Horizontale Skalierung** — Agenten sind unabhängige asyncio-Worker mit
   eigener Queue. Der Schritt zu echten Prozessen/Containern ist ein
   Transport-Wechsel des Event-Busses (Redis vorbereitet in der Config),
   keine Architekturänderung.

## Erweiterungspunkte

- **Neuer Agent:** `org.yaml`-Eintrag oder `POST /api/agents`.
- **Neuer Skill:** `kernel.skills.register(Skill(...))` (Plugin) oder Eintrag in `skills/builtin.py`.
- **Neues Plugin:** Ordner mit `plugin.json` + `plugin.py::setup(kernel)`.
- **Neuer LLM-Provider:** Klasse mit `chat()` in `llm/provider.py` + Zeile in `create_provider()`.
- **Neuer Vektor-Store:** Klasse mit `add()/search()` in `memory/vector.py`.
- **MCP:** Skills besitzen bereits Tool-Schemata (`to_tool_schema()`); ein
  MCP-Server-Adapter kann sie 1:1 exportieren (geplanter nächster Schritt).

## Datenflüsse

**Sprachbefehl (Browser):** Mikrofon → Web Speech API → WS `{"type":"chat"}` →
Orchestrator → Agent (LLM-Tool-Loop → Skills → ggf. Approval-Modal) →
`chat.assistant`-Event → UI + `voice.speak` → speechSynthesis/Piper-WAV.

**Erinnerung:** Skill `create_reminder` → Scheduler → `reminder.due` →
Dashboard-Chat + Sprachansage.
