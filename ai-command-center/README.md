# AI Command Center

Verkaufsfähige KI-SaaS (Next.js App Router). Eine KI-Abteilung für Unternehmen:
Missionen an ein Multi-Agenten-Team, echter KI-Chat mit eingebautem Browser,
KI-Studio (Entwicklungsumgebung im Browser), Skills-Katalog und Lizenz-/Plan-
System mit serverseitig erzwungenen Tageslimits.

## Schnellstart (Entwicklung)

```bash
pnpm install
pnpm dev          # http://localhost:3000
```

Vor dem Start `.env.example` nach `.env` kopieren und mindestens einen
LLM-Anbieter-Key setzen (ohne Key läuft ein klar gekennzeichneter Demo-Modus):

```bash
cp .env.example .env
```

## Wichtige Umgebungsvariablen
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MOONSHOT_API_KEY` – LLM-Anbieter
  (mindestens einer für echte Missionen). Optionaler Modell-Rat: siehe
  `.env.example` (google/xai/qwen/deepseek/meta/mistral).
- `LICENSE_SECRET` – Signatur der Lizenzschlüssel (Produktion: Pflicht).
- `LOCAL_LLM_URL` – optionales eigenes/lokales Modell (OpenAI-kompatibel).

## Bauen / Deploy
```bash
pnpm build && pnpm start
```
Deploy-Ziel Vercel (Root Directory `ai-command-center`). Ablauf für Verkauf,
Lizenzschlüssel und Plan-Limits: siehe `VERKAUF.md`, `GO-LIVE.md`,
`LIZENZ-AUTOMATIK.md`.

## Struktur (Kurz)
- `app/` – Seiten & API-Routen (Missionen, KI-Chat, Studio, Team, Skills …).
- `lib/agents/` – Agenten-System (Provider, Team/Roster, Orchestrator, Browser).
- `lib/license.ts` – Lizenz-/Usage-Token und Plan-Limits.

Hinweis: Dieses Next.js weicht von Standard-Konventionen ab – siehe `AGENTS.md`.
