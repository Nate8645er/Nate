# AI_TEAM_STATUS.md — Unified AI Team

**Stand:** 2026-11-12 · **Repo:** `Nate8645er/Nate` · **Branch:** `claude/unified-ai-team-integration-4dg535`
**Erstellt von:** Claude Code (Opus 4.8) als technischer Hauptarchitekt & Integrationsleiter.

> **Ehrlichkeits-Grundsatz dieses Berichts:** Jede „CONNECTED"/„READY"-Angabe unten ist
> durch einen **echten Testaufruf** belegt (Spalte _Beleg_). Nichts ist simuliert.

---

## 1. Tatsächlicher Status aller vier KI-Systeme

Gemessen in **dieser Cloud-Umgebung** (ephemerer Container auf claude.ai/code).

| System          | Rolle                     | Zustand                  | Beleg (echter Test)                                                                        |
| --------------- | ------------------------- | ------------------------ | ------------------------------------------------------------------------------------------ |
| **Claude Code** | LEAD ARCHITECT            | **EXECUTION READY**      | `claude --version` → `2.1.322`; realer Headless-Call `claude -p …` → exit 0, echte Antwort |
| **GPT / Codex** | DEVELOPMENT ENGINEER      | **NOT INSTALLED** (hier) | `command -v codex` → leer; `api.openai.com/v1/models` → **HTTP 401** (Key nötig)           |
| **Grok / xAI**  | RESEARCH & STRATEGY       | **NOT INSTALLED** (hier) | `command -v grok` → leer; `api.x.ai/v1/models` → **HTTP 401** (Key nötig)                  |
| **OpenCode**    | MULTI-MODEL EXECUTION HUB | **NOT INSTALLED** (hier) | `command -v opencode` → leer; keine Config unter `~/.config/opencode`                      |

**Warum 3 von 4 hier „blockiert" sind — ehrlich:**
Dieser Cloud-Container ist **nicht** deine lokale Maschine. Die CLIs von Codex/Grok/OpenCode
sind hier nicht installiert, und ihre **kostenlosen Abo-Logins** (ChatGPT, Grok) liegen auf
**deinem lokalen Rechner** und lassen sich nicht in eine Cloud-Sandbox übertragen. Die Endpunkte
sind erreichbar, verlangen aber einen **kostenpflichtigen API-Key** (HTTP 401) — und deine Regel
**FREE FIRST / keine unautorisierten API-Kosten** verbietet mir, so einen Key hier einzurichten.

➡️ **Das echte 4-Agenten-Team wird auf deiner lokalen Maschine lebendig.** Das in diesem Repo
gebaute `ai-team`-System ist genau das Werkzeug dafür: lokal ausführen, die drei CLIs einmal
anmelden (FREE), fertig. Siehe Abschnitt 10.

---

## 2. GitHub-Integrationsstatus

| Punkt            | Zustand       | Beleg                                                                                            |
| ---------------- | ------------- | ------------------------------------------------------------------------------------------------ |
| GitHub-Konto     | **CONNECTED** | `get_me` → `login: Nate8645er` (id 301040339)                                                    |
| GitHub-API       | **CONNECTED** | `https://api.github.com` → HTTP 200                                                              |
| Repo-Zugriff     | **CONNECTED** | Session-Scope `Nate8645er/Nate`, Branch gepusht via Git-Proxy                                    |
| `gh` CLI (Token) | **DEGRADED**  | `gh auth status` → _Token in `GH_TOKEN` is invalid_ → GitHub läuft über **MCP**, nicht über `gh` |

GitHub ist die **gemeinsame Zentrale**: Code, Branches, PRs, Reviews, Issues und dieser
Statusbericht liegen dort. Kein Auto-Merge in geschützte Branches.

---

## 3. Agentenrollen

| Seat       | CLI-Aufruf     | Verantwortung                                                                 |
| ---------- | -------------- | ----------------------------------------------------------------------------- |
| `claude`   | `claude -p`    | Architektur · komplexe Programmierung · Code-Review · Security · Koordination |
| `codex`    | `codex exec`   | Feature-Entwicklung · Optimierung · Refactoring · Tests · Fehlersuche · Doku  |
| `grok`     | `grok -p`      | Recherche · Datenanalyse · Strategie · gegenseitige Qualitätskontrolle        |
| `opencode` | `opencode run` | Modell-Routing · Ausführung zugewiesener Aufgaben · MCP-Integration           |

Definiert in [`ai-team/config/agents.json`](ai-team/config/agents.json); Routing pro Phase ebenda.

---

## 4. Kommunikationsarchitektur

- **Persistenter Gruppenchat:** `ai-team/state/messages.jsonl` (append-only).
  Jede Nachricht trägt: `agent`, `role`, `task`, `ts` (ISO-8601), `analysis`, `result`,
  `evidence`, `nextAction`, `status`.
- **Task-Persistenz:** `ai-team/state/tasks/<id>.json` — vollständiger Plan, Seat-Zustände,
  Ergebnisse. Wiederaufnehmbar via `ai-team status` / `ai-team bus`.
- **GitHub-Bus (optional):** `config → bus.github.enabled=true` spiegelt den Chat in ein
  GitHub-Issue (Label `ai-team`) — für maschinenübergreifende Koordination.
- **Orchestrierung:** Auftrag → Zerlegung (research→architecture→implement→test→review) →
  Routing an den _tatsächlich bereiten_ Seat → Live-Aufruf → Sammeln → Persistenz.

---

## 5. Verfügbare Befehle

```bash
ai-team start                 # Seats proben, Übersicht, Policy
ai-team agents                # Seat-Status (echte Probe)
ai-team task "<auftrag>"      # Aufgabe zerlegen → routen → live ausführen
ai-team status                # gespeicherte Tasks
ai-team bus [n]               # Gruppenchat-Verlauf
ai-team probe <id>            # einen Seat einzeln proben (JSON)
```

Launcher: `ai-team/bin/ai-team` → ruft `node ai-team/src/ai-team.mjs`. Kein `npm install` nötig.

---

## 6. Erfolgreiche Testläufe (real)

**T1 — Seat-Probe** (`ai-team agents`): claude = EXECUTION READY (2.1.322); codex/grok/opencode = NOT INSTALLED. ✅ ehrlich erkannt.

**T2 — Realer Headless-Aufruf** (`claude -p "…"`): exit 0, echte deutsche Antwort. ✅ Live-Pfad funktioniert.

**T3 — Vollständiger Multi-Agenten-Lauf** (`ai-team task "… off-by-one in last()…"`), Task-ID `tmwdt0zu10e7o`:

| Schritt | Phase        | Seat   | Status | Dauer |
| ------- | ------------ | ------ | ------ | ----- |
| 1       | research     | claude | DONE   | 23.8s |
| 2       | architecture | claude | DONE   | 26.1s |
| 3       | implement    | claude | DONE   | 53.0s |
| 4       | test         | claude | DONE   | 74.7s |
| 5       | review       | claude | DONE   | 45.4s |

**Ergebnis: `complete` (5/5 Schritte live).** Alle Schritte waren echte `claude`-Prozesse (exit 0),
in `state/messages.jsonl` + `state/tasks/tmwdt0zu10e7o.json` belegt. Inhaltlich korrekt: Root-Cause
(Off-by-One), Fix `a[a.length - 1]`, Testvorschlag, Review-Urteil.

> Hinweis zur Ehrlichkeit: Der Review-Seat merkte selbst an, dass der **verschachtelte** Sandbox-Lauf
> echte Datei-Edits blockierte — er lieferte daher Analyse-Text (wie angefragt), keine erfundene
> „Datei geändert"-Meldung.

---

## 7. Gescheiterte / blockierte Testläufe

- **Codex/Grok/OpenCode Live-Aufruf:** nicht durchführbar — CLIs hier nicht installiert
  (`NOT INSTALLED`). Der Orchestrator routet solche Schritte nicht an eine Fantasie-Antwort,
  sondern markiert sie `BLOCKED` / `MANUAL ONLY`. In T3 fiel jeder Schritt auf den einzig
  bereiten Seat (claude) zurück, daher kein `BLOCKED`-Schritt — das Verhalten ist aber im Code
  (`pickAgent` → `runTask`) implementiert und via `ai-team probe codex` nachweisbar.
- **`gh` CLI:** `GH_TOKEN` ungültig → GitHub-Schreibzugriffe laufen über MCP/Git-Proxy, nicht `gh`.

---

## 8. Kosten & Nutzungslimits

- **Claude Code:** über dein bestehendes Abo (Proxy `ANTHROPIC_BASE_URL`). T3 = 5 Headless-Calls
  (~3,8 min Gesamt-Rechenzeit). Keine zusätzlichen Kosten über das Abo hinaus.
- **Codex / Grok / OpenCode:** **0 €** ausgegeben. Es wurde **kein** kostenpflichtiger API-Key
  eingerichtet oder aufgerufen. FREE FIRST eingehalten; kein automatischer Paid-Fallback.
- **GitHub:** kostenlos.
- **Policy im Code verankert:** `agents.json → policy` (`freeFirst`, `zeroUnapprovedApiCost`,
  `noAutomaticPaidFallback`). Das Tool injiziert **nie** API-Keys und nutzt **keine**
  Cookie-/Token-Umgehung.

---

## 9. Offene Blockaden

1. **3 Seats nur lokal aktivierbar** — Codex/Grok/OpenCode-CLIs + ihre Abo-Logins existieren nur
   auf deiner lokalen Maschine, nicht in dieser Cloud-Sandbox.
2. **Grok-Automatisierung** — ein _automatischer_ programmatischer Zugriff auf Grok geht praktisch
   nur über die **kostenpflichtige xAI-API**. Ohne deine ausdrückliche Freigabe nicht aktiviert.
3. **`GH_TOKEN` ungültig** im Container (kein Blocker für die Arbeit: MCP/Git-Proxy greift).
4. **Projekt-Hook „GateGuard"** (ecc-Plugin) fragt vor jedem Schreibzugriff Fakten ab — verlangsamt
   Automatik, blockiert aber nichts Fachliches.

---

## 10. Deine noch erforderlichen Aktionen

**Um das volle 4-Agenten-Team live zu bekommen — lokal, kostenlos:**

```bash
# 1) Repo lokal holen & ins Projekt
git clone https://github.com/Nate8645er/Nate && cd Nate

# 2) Die drei fehlenden Seats mit DEINEM Abo anmelden (FREE)
npm i -g opencode-ai && opencode auth login          # OpenCode
npm i -g @openai/codex && codex login                # GPT/Codex (Sign in with ChatGPT)
#   Grok: xAI-CLI + Login gemäß xAI-Doku installieren

# 3) Team starten
./ai-team/bin/ai-team start      # zeigt jetzt mehr EXECUTION-READY-Seats
./ai-team/bin/ai-team task "Verbessere meinen HyperGrok Trading Bot (nur Paper, kein Live)"
```

**Entscheidungen, die nur du treffen kannst:**

- [ ] Soll Grok via **kostenpflichtiger xAI-API** automatisiert werden? (sonst bleibt Grok `MANUAL ONLY`)
- [ ] GitHub-Issue-Bus aktivieren? (`config → bus.github.enabled=true`)
- [ ] Für HyperGrok bestätigt: **nur Paper-Trading**, kein Live-Schalter, Risk-Manager unangetastet
      (im Code-Policy-Teil schon als Grundsatz verankert; echte Umsetzung erfolgt erst, wenn die
      Projekte eingebunden sind).

---

### Was in diesem Durchlauf tatsächlich gebaut & getestet wurde

- `ai-team/` Orchestrator (zero-dependency Node), Launcher, Rollen-/Routing-Config.
- Persistenter Gruppenchat + Task-Persistenz.
- Ehrliche Seat-Probe mit echten Testaufrufen (Phase 1).
- **Realer 5-Schritt-Multi-Agenten-Lauf** (Phase 8), `complete`.
- Dieser Bericht (Phase 10).
