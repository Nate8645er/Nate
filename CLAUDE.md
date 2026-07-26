# Nate — Projekt-Gedaechtnis

Diese Datei wird von Claude Code **automatisch bei jeder Sitzung geladen** —
das ist der reale Mechanismus fuer "ein Gehirn, das sich jede Sitzung
merkt und anwendet". Sie liegt im Repo, ist committet und ueberlebt damit
den fluechtigen Container (der bei jeder neuen Sitzung frisch geklont wird).

## Was hier entsteht

Drei zusammenhaengende Produkte, siehe `BESTAND.md` fuer den vollen Stand:

- **Produkt A** — Multi-Tenant-KI-Plattform (`platform-backend/`): FastAPI +
  Postgres mit Row-Level-Security, LiteLLM-Gateway, Stripe-Billing.
- **Produkt B** — Shopify-Abo-Store (`store/`).
- **Produkt C** — Creative/Video-Pipeline (`creative/`): SVG-Ad-Creatives,
  Remotion-Erklaervideo mit Piper-TTS.

Alle Arbeit laeuft auf Branch `claude/ai-team-fable-5-boss-6iim48`, PR #45.

## Installierte Skills & Plugins — wo sie wirklich sind

Nicht in "Erinnerung" oder "Gedaechtnis" im menschlichen Sinn — sondern als
**committete Dateien**, die Claude Code bei jeder Sitzung neu einliest:

- `.claude-plugin/marketplace.json` — registriert zwei Plugins:
  - `ultra-enterprise-os/` — Orchestrator + spezialisierte Agenten (das
    "KI-Team": Architektur, Security, QA, DevOps, Business, Design, Data/ML,
    Fullstack, Docs). Das sind die einzigen Agenten, die real in dieser
    Umgebung als Subagenten aufrufbar sind (Tool "Agent").
  - `nate-toolkit/` — echte Skills, alle unter `nate-toolkit/skills/*/SKILL.md`:
    - `security-scan` — Secrets/CVE-Rundumcheck (`tools/security_scan.py`).
    - `ai-council` — das 13-Anbieter-KI-Team ueber OpenRouter
      (`platform-backend/ops/council.py`), echte Zweitmeinungen.
    - `dev-toolbelt` — was in dieser Sandbox wirklich installiert ist.
    - `tool-catalog` — ehrlicher Katalog der ~85 im Chat genannten
      GitHub-Repos: was real nutzbar ist, was nur Referenz ist, was nicht
      anwendbar ist. **Vor jeder "installiere Repo X"-Anfrage hier
      nachsehen.**

Ein GitHub-Repo ist **kein** Claude-Plugin, solange es keine
`.claude-plugin/plugin.json` mit `skills/`/`agents/`/`commands/` hat — das
gilt fuer praktisch alle extern genannten Repos (transformers, vscode,
elasticsearch, ...). Details und der ehrliche Umgang damit: Skill
`tool-catalog`.

## Wie diese Datei zu benutzen ist

- Bei Sitzungsbeginn automatisch gelesen — kein manueller Schritt noetig.
- Bei neuen dauerhaft relevanten Fakten (neue Skills, neue Architektur-
  Entscheidungen, neue Sicherheitsregeln) **diese Datei erweitern und
  committen** — das ist der einzige Weg, dass es "im naechsten Leben"
  (der naechsten Sitzung) noch bekannt ist.
- Nicht mit Kleinkram vollstopfen — nur was wirklich sitzungsuebergreifend
  gebraucht wird. Feature-Details gehoeren in die jeweiligen READMEs
  (`platform-backend/`, `creative/`, `store/`).

## Feste Regeln (aus bisherigen Sicherheits-Reviews)

- Vor jedem Commit mit neuen Abhaengigkeiten oder Keys: `/security-scan`
  ausfuehren (`nate-toolkit` Skill `security-scan`).
- `.env`-Dateien nie committen, immer `.env.example` mit Platzhaltern pflegen.
- App verbindet sich zu Postgres als `app_rw` (NOSUPERUSER, NOBYPASSRLS),
  nie als Superuser — sonst greift Row-Level-Security nicht.
- Bei Unsicherheit ueber Modell-/Team-Behauptungen: nachpruefen, nicht
  behaupten. Der 13-Anbieter-Council in `ai-council` ist echt verifiziert
  (13/13 antworten) — anders als eine fruehere Chat-Behauptung mit
  erfundenen Modellnamen.
