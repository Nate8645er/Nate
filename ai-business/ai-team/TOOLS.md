# TOOLS & SCRIPTS

## Eigene, portable Tools (KOPIERT nach `ai-business/tools/`)

### `rat.py` — Externe Modell-Flotte (DIRECT)
Fragt mehrere fremde Modelle parallel dieselbe Frage ueber den lokalen OmniRoute-Server (`localhost:20128`, OpenAI-kompatibel, SSE). Zweck: echte Zweitmeinung — nicht Claude prueft Claude.
- **Flotte:** GPT-5.6, Kimi K3, Gemini 3.7, Qwen3-Max, DeepSeek V4, Grok 4.6, Mistral L (je ein anderes Haus).
- **Nutzung:** `echo "Frage" | python3 tools/rat.py`
- **Voraussetzung:** OmniRoute laeuft + `OPENROUTER_API_KEY` gesetzt (AUTH_REQUIRED).
- **Secrets:** keine im Code — Key kommt aus der Umgebung.
- **Besonderheit:** liest bewusst SSE-`data:`-Zeilen; hohe Token-Untergrenze, weil denkende Modelle sonst leer zurueckkommen.

### `omniroute-autostart.sh` — Router-Autostart (ADAPTABLE)
Startet OmniRoute im Hintergrund (SessionStart-Hook), installiert es einmalig per npm, hinterlegt den OpenRouter-Key **aus der Umgebungsvariable** und wartet, bis der Server erreichbar ist. Log: `/root/.omniroute/`.
- **Secrets:** keine — Key ausschliesslich aus `OPENROUTER_API_KEY`.
- **OpenCode:** als normales Shell-Startskript nutzbar; Pfade/Log-Ort anpassen.

## Eigene Tools (referenziert, nicht kopiert)

### `../curbcut/` — Barrierefreiheits-Pruefer (13 Python-Dateien, DIRECT)
Eigenes Produkt: prueft ausgeliefertes HTML gegen WCAG (Kontrast per Luminanzformel), statt Overlays.
- `kern/`: `farbe.py`, `regeln.py`, `seite.py`, `bauteile.py`, `pruefen.py`, `befund.py`
- `betrieb/`: `rechnung.py`, `waechter.py`, `reihe.py`
- `film/`: `folien.py`, `bauen.py` (Erklaervideo-Bau)
- `waehlen.py`, `web/server.py`
- Tageswaechter als GitHub Action: `.github/workflows/curbcut-waechter.yml`.

### `../marketing-skillstack/tools/`
Hilfsskripte des Marketing-Skillstacks (referenziert).

### `../n8n-templates/` — 328 n8n-Workflows (DIRECT/ADAPTABLE)
Automations-Vorlagen (Zie619-Sammlung). `catalog.json`, `INDEX.md`. Direkt in n8n importierbar; einzelne Nodes brauchen eigene Credentials.

## Claude-Code-eingebaute Tools (Referenz, CLAUDE_ONLY)
Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, Task/Agent, Artifact, TaskCreate/Update, Workflow, u.a. — Teil der Claude-Code-Laufzeit. OpenCode hat eigene Aequivalente (Datei-/Shell-/Such-Tools), aber nicht denselben Satz. In Agenten-Frontmatter referenziert (`tools:`); beim Port auf OpenCodes Tool-Namen mappen.

## GitHub-Actions (Workflows im Repo)
- `.github/workflows/curbcut-waechter.yml` — taeglicher Cron-Waechter (oeffentliches Repo = gratis).
- `.github/workflows/platform-backend-release.yml`.

## Portierbarkeit-Zusammenfassung
| Tool | OpenCode | Auth |
|---|---|---|
| rat.py | DIRECT | OPENROUTER_API_KEY |
| omniroute-autostart.sh | ADAPTABLE | OPENROUTER_API_KEY |
| curbcut/*.py | DIRECT | nein |
| n8n-templates | DIRECT | pro Node |
| Claude-Tools | CLAUDE_ONLY | — |

## NOT FOUND
- Keine kompilierten Binaries, keine weiteren eigenen CLI-Tools ausserhalb der genannten.
