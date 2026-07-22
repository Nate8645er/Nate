# AI Command Center

Verkaufsfähige KI-SaaS (Next.js App Router). Eine KI-Abteilung für Unternehmen:
Missionen an ein Multi-Agenten-Team, echter KI-Chat mit eingebautem Browser,
KI-Studio (Entwicklungsumgebung im Browser), Skills-Katalog und Lizenz-/Plan-
System mit serverseitig erzwungenen Tageslimits.

Helles, farbiges Design über alle Seiten (`.acc-*`-Designsystem in
`app/globals.css`), ein animiertes KI-Büro (`AgentWorld`, reines CSS,
`prefers-reduced-motion`-fest), ein Integrations-/Onboarding-Assistent zum
Verbinden eigener Systeme sowie ein Video-Onboarding pro Tarif.

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
- `app/` – Seiten & API-Routen (Missionen, KI-Chat, Studio, Team, Skills,
  Integrationen, Onboarding …).
- `app/components/AgentWorld.tsx` – animiertes KI-Büro (Abteilungen, laufende
  Figuren, verbundene Firma) für Landing & Dashboard.
- `app/integrationen/OnboardingWizard.tsx` – 3-Schritt-Assistent: Systeme
  wählen (M365, Google, Slack, Notion, Shopify, Stripe, eigene API, Maschinen),
  Firma hinterlegen, Anfrage senden. Speichert lokal (`acc-firma`,
  `acc-connections`).
- `app/onboarding/` + `lib/onboarding.ts` – Video-Onboarding und interaktive
  Einrichtungs-Checkliste pro Tarif. Deutsche Sprachführung (`useVorleser`,
  Web-Speech-API des Browsers) liest die Schritte vor und hebt den aktiven
  hervor – ohne Server/Kosten, mit sauberem Fallback ohne Sprachpaket.
- `lib/agents/` – Agenten-System (Provider, Team/Roster, Orchestrator, Browser).
  Ohne API-Key wird jedes Ergebnis klar als Demo gekennzeichnet.
- `lib/connectors.ts`, `lib/skills.ts` – Kataloge (Integrationen, Fähigkeiten).
- `lib/license.ts` – Lizenz-/Usage-Token und Plan-Limits.

## Tests & Qualität
```bash
pnpm test         # Vitest (Lizenz, Blitz, Shopify-Lizenz, Daten-Integrität)
pnpm lint         # ESLint (in CI blockierend)
pnpm typecheck    # tsc --noEmit
```
CI (`.github/workflows/ci.yml`) führt Lint, Typecheck, Test und Build aus.

Hinweis: Dieses Next.js weicht von Standard-Konventionen ab – siehe `AGENTS.md`.
