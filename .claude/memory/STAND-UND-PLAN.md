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

## Offene Aufgaben (Reihenfolge)
1. **Neues Design REAL ausrollen** über alle ~14 Seiten (dashboard, assistent,
   studio, team, faehigkeiten, agenten, email, kunden, workflows, berichte,
   analysen, benutzer, einstellungen, integrationen, status, sicherheit) +
   größere Belegschaft im echten Roster (lib/agents/roster.ts). Schritt für
   Schritt, jede Seite getestet, kleine grüne Commits.
2. **DANACH** pro Abo EIN langes, detailliertes Tutorial-Video vom FERTIGEN
   System (mit Higgsfield): jede Seite geöffnet & erklärt, KI-Stimme drüber,
   inkl. „so verbindet man seine Firma/E-Mail/Shop/Systeme". Jedes Video ans
   passende Shopify-Produkt hängen (Kunde bekommt es beim Kauf) und dem Kunden
   einzeln schicken. KEINE Videos vorher – erst wenn das System fertig ist.

## Regeln
- Ehrlich: nur behaupten, was real läuft & geprüft ist (echtes Ausführen,
  QA+Security vor „fertig"). Keine Platzhalter.
- Secrets NIE ins Git/Chat – nur .env/Umgebung (per .gitignore geschützt).
- Kleine grüne Schritte auf den Feature-Branch committen. Auf Deutsch antworten.
- Stille Wartung (ACC-Wache): keine Shopify-Produkte/Preise/Beschreibungen
  ändern, nichts löschen, keine E-Mails senden (nur Entwürfe), keine Secrets.
