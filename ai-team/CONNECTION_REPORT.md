# Verbindungsbericht — Unified AI Team (Phase 7)

**Stand:** 2026-11-12 · **Ausgeführt in:** Linux-Cloud-Container (claude.ai/code) — **nicht** dein Windows-PC.

> ⚠️ **Wichtig:** Diese Session läuft in der Cloud. Dein Windows-System (Claude 2.1.186,
> OpenCode 2.2.5, Codex, Grok) kann ich von hier **nicht** sehen oder testen. Darum sind unten
> zwei Spalten: **Hier (Cloud)** = was ich real getestet habe; **Lokal (Windows)** = was du mit
> demselben Werkzeug erreichst, sobald du es auf deinem PC startest.

## Verbindungsstatus pro Agent

| Agent           | Hier (Cloud, real getestet)                                  | Lokal (Windows, erwartet)                                         | Auth-Weg                |
| --------------- | ------------------------------------------------------------ | ----------------------------------------------------------------- | ----------------------- |
| **Claude Code** | ✅ **CONNECTED** — echtes Modell `Claude Opus 4.8` antwortet | ✅ CONNECTED (deine 2.1.186)                                      | Claude-Abo / Login      |
| **OpenCode**    | ⛔ **BLOCKED** (CLI nicht im Container)                      | ✅ sobald `opencode` installiert+angemeldet                       | `opencode auth login`   |
| **GPT / Codex** | ⛔ **BLOCKED** (CLI nicht im Container)                      | ⚠️ **MANUAL** — Windows-Binary fehlt wegen **ENOSPC** (C: < 1 GB) | `codex login` (ChatGPT) |
| **Grok / xAI**  | ⛔ **BLOCKED** (CLI nicht im Container)                      | ❓ **UNBESTÄTIGT** — lokale Grok-CLI noch nicht verifiziert       | je nach CLI             |

## Welche Modelle tatsächlich antworten

- **Claude:** `Claude Opus 4.8` — real verifiziert (Council-Test `tmwdxai7dxsi4`, echte Antwort
  gespeichert, Modellname + Empfangsbestätigung). **Keine Simulation.**
- OpenCode/Codex/Grok: hier nicht testbar (nicht installiert). Der Orchestrator ruft sie lokal
  real auf; jeder liefert seinen eigenen Modellnamen über die erste Zeile `MODELL: …`.

## Welche Authentifizierungen funktionieren

- **Claude:** über Abo/Proxy — bestätigt (exit 0, echte Antwort).
- **GitHub:** CONNECTED (MCP), `get_me` → `Nate8645er`. `gh`-Token im Container ungültig → GitHub
  läuft über MCP/Git-Proxy.
- OpenCode/Codex/Grok: Auth wird **lokal** über die jeweilige CLI-Anmeldung geprüft
  (`probe.authFile`/`authEnv` in `config/agents.json`). Kein Token wird gespeichert oder injiziert.

## Welche Verbindungen noch fehlen (BLOCKED/MANUAL)

1. **OpenCode, Codex, Grok** laufen nur **lokal auf deinem Windows-PC** (Abo-Logins liegen dort,
   nicht in der Cloud übertragbar; FREE-FIRST verbietet kostenpflichtige API-Keys hier).
2. **Codex (Windows):** Binary fehlt wegen **ENOSPC** → erst **Speicher auf C: freimachen**,
   dann `codex` reparieren/neu installieren. (Ich räume **nichts** eigenmächtig auf.)
3. **Grok-CLI:** als lokale CLI noch nicht bestätigt — Befehl in `config/agents.json → agents.grok`
   ggf. an deine installierte Grok-CLI anpassen.

## Was du persönlich tun musst

```powershell
# 1) Repo lokal holen
git clone https://github.com/Nate8645er/Nate; cd Nate

# 2) C: aufräumen (Codex ENOSPC) — ZEIG MIR vorher die großen Dateien, ich räume nichts blind
#    z.B.:  Get-ChildItem $env:TEMP -Recurse | Sort Length -Desc | Select -First 20

# 3) Fehlende Seats mit DEINEM Abo anmelden (kostenlos)
opencode auth login
codex login                 # nach ENOSPC-Fix
#    Grok: CLI + Login gemäß deiner Grok-CLI

# 4) Team-Gruppenchat starten (Round-Table, keine festen Rollen)
.\ai-team\bin\ai-team.ps1 start
.\ai-team\bin\ai-team.ps1 council "Deine Aufgabe hier"
.\ai-team\bin\ai-team.ps1 council "Schwierige Aufgabe" --rounds=2   # mit Kreuz-Review
.\ai-team\bin\ai-team.ps1 bus                                        # Diskussionsverlauf
```

## Kosten

- **Codex/Grok/OpenCode: 0 €** — kein kostenpflichtiger API-Key eingerichtet oder aufgerufen.
- **Claude (dieser Test):** 1 echter Kurzaufruf über dein Abo (~18 s). Keine Zusatzkosten.
- **Kostenschutz im Code:** Council begrenzt echte Aufrufe (Seats × Runden ≤ 8), warnt vor
  OpenCode-Doppelaufrufen (`costNote`), kein Paid-Fallback, keine Key-Injektion.

## Wie der gemeinsame Gruppenchat startet

`ai-team council "<Aufgabe>"` → dieselbe Aufgabe geht an **alle** angemeldeten Seats gleichzeitig;
jeder antwortet als er selbst (erste Zeile `MODELL:`), alles wird dem **echten** Agenten zugeordnet
und in `state/messages.jsonl` + `state/tasks/<id>.json` gespeichert. Mit `--rounds=2` lesen die
Agenten die Vorschläge der anderen und reviewen sie gegenseitig. Claude koordiniert nur den
Nachrichtenfluss — keine festen Rollen, jeder Seat darf jede Aufgabe bearbeiten.

> Mit nur **einem** angemeldeten Seat ist es ein Monolog; die **echte Diskussion** entsteht ab
> **zwei** lokal angemeldeten Seats.
