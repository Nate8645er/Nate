# CLAUDE.md — Projektregeln fuer dieses Repo

Dieses Repo traegt MEHRERE Projekte: das KI-SaaS (AI Command Center) mit
der Agentur-Website ZEHNTAGE UND den Shopify-Shop Let'sDrink. Lies den
Abschnitt, der zur aktuellen Aufgabe gehoert.

## >>> AKTUELLER STAND — ZUERST LESEN <<<
- KI-SaaS/ZEHNTAGE: Gedaechtnis in **.claude/memory/STAND-UND-PLAN.md**,
  dort als Fable-5-Team weitermachen. Erster Schritt jeder Session:
  **rat_status** (MCP „modell-rat", 9 Modelle via OpenRouter). Neues
  helles/farbiges Design ist freigegeben und muss real ueber alle Seiten
  ausgerollt werden; Videos erst danach.
- Let'sDrink: Stand + Uebergabe in **SESSION-HANDOFF.md** und
  `letsdrink/STATUS-2026-07-28.md`.

## Let'sDrink (Shopify)

- `letsdrink/` — Shop "Let'sDrink" (Trinkflasche mit Napf fuer Hund und
  Katze, CHF 29.90, Store-Handle `i0m1xi-h5`, shared Backend mit
  MeowUfo/AI Command Center). Massgeblich: `letsdrink/HANDOFF.md`
  (Regeln + Produktfakten) und `letsdrink/STATUS-2026-07-28.md`.
- `letsdrink/shopify-theme-letsdrink/` ist das komplette Theme; es wird
  DIREKT per Shopify-API (`themeFilesUpsert`, BASE64 bzw. Staged-Upload)
  in das unveroeffentlichte Theme "animations-theme"
  (`gid://shopify/OnlineStoreTheme/196787667321`) deployed — keine ZIPs.
- Harte Regeln: Kein Schreiben aufs LIVE/MAIN-Theme. Seiten/Themes
  anderer Marken nicht anfassen. Schweizer Recht (UWG/PBV): keine
  erfundenen Bewertungen, keine Fake-Countdowns/Verknappung, keine
  Material-/BPA-/Spuelmaschinen-Claims ohne schriftliche Bestaetigung.
  Preise CHF inkl. MwSt, 14 Tage Rueckgabe ist freiwillig, Du-Form,
  Schweizer "ss" statt "ß". Ehrlichkeit vor Wirkung.

## KI-SaaS / ZEHNTAGE — Arbeitsregeln

- Schreibe sicheren, modularen, dokumentierten Code. Keine Platzhalter in
  produktivem Code.
- Teste jede nichttriviale Aenderung durch echtes Ausfuehren (Build,
  Mission, Playwright), nicht nur durch Draufschauen.
- Fuehre vor Auslieferung sicherheitsrelevanter Aenderungen ein
  Security-Review aus (ultra-security + gitleaks/semgrep falls vorhanden).
- Committe abgeschlossene, gruene Arbeit in kleinen Schritten; pushe auf
  den Feature-Branch. Secrets NIE committen (.gitignore prueft .env*).
- Frage vor gefaehrlichen/irreversiblen Aktionen nach (Loeschen, Push auf
  fremde Branches, externer Versand).

## Team (Subagenten in .claude/agents/)
ultra-orchestrator (zerlegt), ultra-architect, ultra-fullstack (Coder),
ultra-security (nur defensiv), ultra-qa (Test), ultra-design, ultra-devops,
ultra-docs, ultra-business, ultra-data-ml. Delegiere pro Teilaufgabe an die
passende Rolle; Rollen liefern kurze, strukturierte Ergebnisse.

## Plugins & Graphify

- Dieses Repo ist der private Plugin-Marketplace `nate-marketplace`
  (`.claude-plugin/marketplace.json`) mit `ultra-enterprise-os/` und
  `graphify-plugin/` (Skills: graphify, graphify-setup, graph-query;
  Agenten: graph-builder, graph-analyst, graph-extractor).
- Die graphify-CLI wird per SessionStart-Hook automatisch installiert
  (`pip install graphifyy`, Kommando: `graphify`).
- Repo-Graph: `graphify update .` auffrischen; Fragen zum Repo zuerst
  ueber `graphify-out/GRAPH_REPORT.md`, `graphify explain "<node>"` und
  `graphify path "<a>" "<b>"` beantworten statt grep-Sweeps.
- `graphify-out/cache/` ist gitignored; Graph-Artefakte duerfen
  committet werden.

## Token-Headroom / Kontext
- Lade nur benoetigte Dateien; scanne keine ganzen Repos ohne Grund.
- Nutze Diffs statt ganzer Dateien; komprimiere lange Ergebnisse.
- Wichtige Fakten in .claude/memory/ ablegen statt im Chat wiederholen.
- Nach Abschluss temporaeren Kontext freigeben; Subagenten liefern knapp.

## Wichtige Pfade
- ai-command-center/ : die verkaufte SaaS (Next.js). Agenten-Logik in
  lib/agents/. Deploy-Ziel Vercel (Env: 3 API-Keys + LICENSE_SECRET).
- websites/agentur/ : ZEHNTAGE-Live-Site (GitHub Pages).
- ki-agentur-setup/ : Windows-Setup + STACK.md + Plugin-Doku.
- letsdrink/ : Shopify-Shop Let'sDrink (siehe oben).

## Bekannte Redundanz (Absicht, nicht aufraeumen)
`.claude/agents|commands|skills` spiegeln den Inhalt von
`ultra-enterprise-os/`. Grund: In Remote-Containern laedt der
Marketplace-Plugin-Mechanismus nicht immer; die `.claude/`-Kopien
garantieren, dass die ultra-Agenten trotzdem da sind. Bei Aenderungen
beide Orte synchron halten.

Details siehe .claude/memory/.
