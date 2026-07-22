# STAND & PLAN — Gedächtnis für jede neue Session

Diese Datei ist das gemeinsame Gedächtnis. Jede neue Session liest sie zuerst
(CLAUDE.md verweist darauf) und macht als **Fable-5-Team** hier weiter.

## Sofort beim Start
1. **rat_status** aufrufen (MCP „modell-rat") → prüfen, ob die 9 Modell-Worker
   bereit sind. Erwartung mit gesetztem OPENROUTER_API_KEY: „9 von 9 einsatzbereit
   (OpenRouter aktiv – ein Key für alle)".
2. Nicht 9/9? → Umgebung „Claudcode" prüfen: `OPENROUTER_API_KEY=sk-or-…`
   gesetzt und Netzwerkzugriff = „Voll". (Key NIE in den Chat.)
3. Danach an den offenen Aufgaben weiterarbeiten (unten), mit dem ganzen Team.

## Repo / Branch
- **claude/ai-dev-environment-setup-0nnvu7** = alles (Produkt + Team). Hier
  weiterarbeiten.
- `main` = Team-Infrastruktur (MCP-Brücke + Boss-Agent).
- Produkt liegt in `ai-command-center/` (Next.js). Build: `pnpm build`.

## Das Team (immer bei JEDER Aufgabe aktiv)
- **Boss:** Fable 5 (Agent `fable5-boss`).
- **Modell-Worker** (via OpenRouter, ein Key für alle; MCP „modell-rat"):
  Gemini 3 Ultra, Grok 5, Kimi, Qwen 3 Max, DeepSeek R2, Llama 4 Behemoth,
  ChatGPT, Claude Sonnet 5, Mistral Magistral. Tools: `ask_*`, `rat_council`
  (Frage an alle, Boss führt zusammen), `rat_status`.
- **Assistenten:** ultra-orchestrator/-architect/-fullstack/-security/-qa/
  -design/-devops/-docs/-business/-data-ml + generative Belegschaft.

## Schon fertig (Build grün)
- KI-Studio (ai-command-center/app/studio): Tabs, Suchen&Ersetzen, Diff,
  Multi-Datei-KI-Apply, Live-Vorschau, Vorlagen, projektweite Suche,
  Editor-Komfort.
- Modell-Rat im Produkt (Provider + council.ts + /team + /api/rat).
- Aufräum-Durchgang (tote Dateien raus, NUL-Bytes gefixt, ehrliche Preise:
  Free 3/Tag, Starter 25/Tag statt „unbegrenzt").
- Shop: bewegter Trailer, 6 Abo-Tutorials hochgeladen.
- MCP-Team-Brücke: tools/modell-rat-mcp/.

## FREIGEGEBEN: Neues Design (noch NICHT real eingebaut – nur Vorschau!)
Der Kunde hat den neuen Look freigegeben: **hell/weiß + farbig** statt
dunkel/braun. Merkmale:
- Weißer Grund (#f5f6fb), weiße Karten, weiche Schatten, klare Rundungen.
- Farbige Akzente: Indigo/Violett (Haupt) + Orange + Teal + Pink.
- Verlaufs-Überschriften, Verlaufs-Buttons.
- Fähigkeiten werden BESCHRIEBEN, NICHT in Zahlen gezählt (kein „79 Skills",
  sondern „Skills – wofür sie da sind").
- Mehr Belegschaft, in Abteilungen (Führung, Entwicklung, Marketing,
  Kundenservice, Finanzen, Medien, Betrieb …).
Aktuell sind die ~14 echten Seiten noch im ALTEN dunklen HUD-Look
(globals.css `--hud-*`/`.hud-*` + inline bg-[#0b0a08]).

## ERLEDIGT (Branch claude/ki-system-redesign-rollout-5nhzzg, PR #41)
- **Design-Rollout KOMPLETT:** alle ~14 Seiten + Startseite + Dashboard auf
  hellen acc-Look (Build grün, je Seite per Screenshot verifiziert). Fähigkeiten
  beschrieben statt gezählt. Dashboard: KI-Büro-Animation als helles
  „Live-Büro"-Panel eingebettet (AgentWorld/.aw-* dunkel belassen = Live-Monitor).
- **Belegschaft ausgebaut:** lib/agents/roster.ts 37 → 55 benannte Spezialisten.
- **Phase 0 Bestandsaufnahme:** ai-command-center/BESTANDSAUFNAHME.md (Ist-Zustand,
  Schwachstellen kritisch/hoch/mittel, Phasenplan).
- **Video-Onboarding-System:** app/onboarding (pro-Abo Tutorial + Übersichtsvideo
  + interaktive Checkliste mit localStorage-Fortschritt + Tooltips). Inhalte
  zentral/versioniert in lib/onboarding.ts (Tarif-Videos leicht einhängbar).
- **Absichern (Phase 4 Anfang):** Vitest + 14 Unit-Tests (lib/license.ts),
  GitHub-CI (.github/workflows/ci.yml: install+typecheck+test+build; Lint
  nicht-blockierend), Security-Fix (vorname in Webhook-Mail escaped).

## NÄCHSTE OFFENE AUFGABEN (Reihenfolge)
1. **Fundament (Enterprise-Blocker, braucht Provider-Entscheidung + Zustimmung
   für externen Dienst):** Postgres + echte Anmeldung + Mandantentrennung/RBAC,
   serverseitige Datenhaltung + Quota-Enforcement. Siehe BESTANDSAUFNAHME.md.
2. **Integrations-Hub real:** OAuth2-Route + verschlüsselter Token-Store +
   Adapter (erst 1–2 echte Connectors) + Human-in-the-Loop + Audit-Log.
3. **Lint-Bereinigung:** 29 vorbestehende Next-16-Befunde, dann CI-Lint blockierend.
4. **Higgsfield (autorisiert):** Büroszene/Shop-Visuals + pro-Abo Tutorial-Videos
   (eine KI-Stimme). Videos an passendes Shopify-Produkt hängen. Erst wenn System
   fertig; Videos dann in lib/onboarding.ts pro Tarif einhängen.
5. **Shop-Theme** an den hellen Look angleichen.

## Regeln
- Ehrlich: nur behaupten, was real läuft & geprüft ist (echtes Ausführen,
  QA+Security vor „fertig"). Keine Platzhalter.
- Secrets NIE ins Git/Chat – nur .env/Umgebung (per .gitignore geschützt).
- Kleine grüne Schritte auf den Feature-Branch committen. Auf Deutsch antworten.
- Stille Wartung (ACC-Wache): keine Shopify-Produkte/Preise/Beschreibungen
  ändern, nichts löschen, keine E-Mails senden (nur Entwürfe), keine Secrets.
