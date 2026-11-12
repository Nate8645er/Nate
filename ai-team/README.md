# ai-team — Unified AI Team (Claude Code · OpenCode · Grok · GPT/Codex)

Ein schlanker, abhängigkeitsfreier Orchestrator, der die vier KI-CLIs zu **einem Team**
zusammenschaltet und über GitHub koordiniert. **Node ≥ 18** genügt — kein `npm install`.

## Grundprinzip (Ehrlichkeit vor Show)

> Ein Agenten-„Ergebnis" ist **immer** echte CLI-Ausgabe eines realen Aufrufs.
> Ein fehlender oder nicht angemeldeter Seat wird als das gemeldet, was er ist —
> `NOT_INSTALLED` / `INSTALLED (not authed)` / `BLOCKED` — und **nie** mit einer
> erfundenen Antwort gefüllt.

Dadurch funktioniert das System _heute_ mit dem einen live angemeldeten Seat (Claude)
und wächst automatisch, sobald du die übrigen CLIs lokal anmeldest.

## Rollen

| Seat       | CLI            | Rolle                                                              |
| ---------- | -------------- | ------------------------------------------------------------------ |
| `claude`   | `claude -p`    | **LEAD ARCHITECT** — Architektur, Review, Security, Koordination   |
| `codex`    | `codex exec`   | **DEVELOPMENT ENGINEER** — Features, Refactoring, Tests, Doku      |
| `grok`     | `grok -p`      | **RESEARCH & STRATEGY** — Recherche, Strategie, Qualitätskontrolle |
| `opencode` | `opencode run` | **MULTI-MODEL EXECUTION HUB** — Modell-Routing, Ausführung, MCP    |

Rollen, Routing und CLI-Aufrufe stehen in [`config/agents.json`](config/agents.json) und sind
frei anpassbar.

## Befehle

```bash
ai-team start                 # Seats proben, Übersicht, Policy
ai-team agents                # Seat-Status (echte Probe)
ai-team task "<auftrag>"      # Aufgabe zerlegen → an reale Seats routen → ausführen
ai-team status                # gespeicherte Tasks
ai-team bus [n]               # persistenter Gruppenchat (letzte n Nachrichten)
ai-team probe <id>            # einen Seat einzeln proben (JSON)
```

Direkt ohne Launcher: `node ai-team/src/ai-team.mjs <cmd>`.

Optional auf den PATH legen:

```bash
ln -s "$PWD/ai-team/bin/ai-team" ~/.local/bin/ai-team   # oder /usr/local/bin
```

## Wie eine Aufgabe läuft

1. **Zerlegung** in Phasen: research → architecture → implement → test → review (transparent, lokal).
2. **Routing** jeder Phase an den passenden, _tatsächlich einsatzbereiten_ Seat (`config/agents.json → routing`).
3. **Live-Ausführung**: der Seat wird als echter Unterprozess aufgerufen; nur echte stdout zählt.
4. **Gruppenchat**: jede Nachricht (Agent, Aufgabe, Zeitstempel, Ergebnis, Beleg, nächste Aktion)
   landet in `state/messages.jsonl`.
5. **Persistenz**: der ganze Task inkl. Seat-Zustände wird nach `state/tasks/<id>.json` geschrieben
   und ist mit `ai-team status` / `ai-team bus` wieder einsehbar.

## Die übrigen Seats aktivieren (FREE FIRST)

Diese CLIs nutzen deine **bestehenden Abos** über ihre eigene Anmeldung — es werden
**nie** API-Keys von diesem Tool injiziert:

```bash
# OpenCode (nutzt dein angemeldetes Modell, inkl. MCP)
npm i -g opencode-ai        # oder: brew install sst/tap/opencode
opencode auth login

# GPT / Codex (OpenAI Codex CLI, ChatGPT-Login)
npm i -g @openai/codex
codex login                 # „Sign in with ChatGPT"

# Grok (xAI) — CLI + Login gemäß xAI-Doku
# (automatischer Zugriff nur über separate, kostenpflichtige xAI-API → nicht ohne Freigabe)
```

Danach erscheint der Seat bei `ai-team agents` automatisch als `EXECUTION READY`.

## Sicherheits-Policy (eingebaut)

- **FREE FIRST**, keine unautorisierten API-Kosten, kein automatischer Paid-Fallback.
- Keine Key-Injektion, keine Session-Cookie-/Token-Umgehung.
- Kein Auto-Merge in geschützte Branches (`main`/`master`/`production`/`live`).
- Code-schreibende Seats bekommen pro Aufgabe einen eigenen Branch/Worktree (kein Konflikt).
- Laufzeit-State (`messages.jsonl`, `tasks/`) ist aus git ausgeschlossen.
