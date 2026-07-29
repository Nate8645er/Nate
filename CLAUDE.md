# Nate — Arbeitsregeln fuer dieses Repo

## Was hier drin ist

- `letsdrink/` — Shopify-Shop "Let'sDrink" (Trinkflasche mit Napf fuer Hund
  und Katze, CHF 29.90, Store-Handle `i0m1xi-h5`). Massgeblich:
  `letsdrink/HANDOFF.md` (Regeln + Produktfakten) und
  `letsdrink/STATUS-2026-07-28.md` (laufender Stand).
  `letsdrink/shopify-theme-letsdrink/` ist das komplette Theme; es wird
  DIREKT per Shopify-API (`themeFilesUpsert`, BASE64/Staged-Upload) in das
  unveroeffentlichte Theme "animations-theme" deployed — keine ZIPs.
- `ultra-enterprise-os/` — Plugin: virtuelles Multi-Team-Betriebssystem.
- `graphify-plugin/` — Plugin: Wissensgraphen ueber Code/Doku bauen und
  abfragen (Skills: graphify, graphify-setup, graph-query; Agenten:
  graph-builder, graph-analyst, graph-extractor).
- `.claude-plugin/marketplace.json` — dieses Repo ist der private
  Plugin-Marketplace `nate-marketplace`.

## Harte Regeln (aus HANDOFF, gelten immer)

- Kein Schreiben auf das LIVE/MAIN-Theme; nur unveroeffentlichte Themes.
- Shared Shopify-Backend: Seiten/Themes anderer Marken (MeowUfo,
  AI Command Center) nicht anfassen.
- Schweizer Recht (UWG/PBV): keine erfundenen Bewertungen, keine
  Fake-Countdowns/Verknappung, keine Material-/BPA-/Spuelmaschinen-Claims
  ohne schriftliche Lieferantenbestaetigung. Preise CHF inkl. MwSt.
  14 Tage Rueckgabe ist freiwillig. Du-Form, Schweizer "ss" statt "ß".
- Ehrlichkeit vor Wirkung: nur belegte Fakten in Shop-Texte.

## Graphify-Workflow

Die CLI wird per SessionStart-Hook automatisch installiert
(`pip install graphifyy`, Kommando heisst danach `graphify`).

- Repo-Graph aktualisieren: `graphify update .` (Code-only, kein LLM,
  Ergebnis in `graphify-out/`).
- Fragen zum Repo: erst `graphify-out/GRAPH_REPORT.md` lesen, dann
  `graphify explain "<node>"` / `graphify path "<a>" "<b>"` —
  statt grep-Sweeps ueber das ganze Repo.
- `graphify-out/cache/` ist gitignored; die Graph-Artefakte selbst
  duerfen committet werden.

## Bekannte Redundanz (Absicht, nicht aufraeumen)

`.claude/agents|commands|skills` spiegeln den Inhalt von
`ultra-enterprise-os/`. Grund: In Remote-Containern laedt der
Marketplace-Plugin-Mechanismus nicht immer (installed_plugins leer);
die `.claude/`-Kopien garantieren, dass die ultra-Agenten trotzdem da
sind. Wer hier aufraeumt, muss vorher beweisen, dass das Plugin in
allen genutzten Umgebungen laedt. Bei Aenderungen beide Orte synchron
halten.
