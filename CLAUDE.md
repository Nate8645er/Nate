# CLAUDE.md - Projektregeln fuer das KI-SaaS-Repo

Dieses Repo baut und verkauft KI-Produkte (AI Command Center) plus die
Agentur-Website ZEHNTAGE. Arbeite als virtuelles Engineering-Team.

## >>> AKTUELLER STAND — ZUERST LESEN <<<
Laufende Arbeit + Gedaechtnis: **.claude/memory/STAND-UND-PLAN.md** lesen und
dort als **Fable-5-Team** weitermachen. Erster Schritt jeder Session:
**rat_status** (MCP „modell-rat", 9 Modelle via OpenRouter). Neues helles/
farbiges Design ist freigegeben und muss real ueber alle Seiten ausgerollt
werden; Videos erst danach.

## Arbeitsregeln
- Schreibe sicheren, modularen, dokumentierten Code. Keine Platzhalter in
  produktivem Code.
- Teste jede nichttriviale Aenderung durch echtes Ausfuehren (Build, Mission,
  Playwright), nicht nur durch Draufschauen.
- Fuehre vor Auslieferung sicherheitsrelevanter Aenderungen ein Security-Review
  aus (ultra-security + gitleaks/semgrep falls vorhanden).
- Committe abgeschlossene, gruene Arbeit in kleinen Schritten; pushe auf den
  Feature-Branch. Secrets NIE committen (.gitignore prueft .env*).
- Frage vor gefaehrlichen/irreversiblen Aktionen nach (Loeschen, Push auf
  fremde Branches, externer Versand).

## Team (Subagenten in .claude/agents/)
ultra-orchestrator (zerlegt), ultra-architect, ultra-fullstack (Coder),
ultra-security (nur defensiv), ultra-qa (Test), ultra-design, ultra-devops,
ultra-docs, ultra-business, ultra-data-ml. Delegiere pro Teilaufgabe an die
passende Rolle; Rollen liefern kurze, strukturierte Ergebnisse.

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

Details siehe .claude/memory/.
