# Jarvis Ultra — Architektur

Jarvis Ultra erweitert Open.Jarvis um den vollen Plugin/Skill/Tool-Loadout und
einen Live-Ticker über eine simulierte Mega-Organisation.

## Adress-Schema und Determinismus

Jede Entität wird über einen **Pfad** aus Indizes adressiert:

- `(7,)` → direkter Mitarbeiter Nr. 7 von Jarvis HQ (`E-7`)
- `(7, 42)` → Mitarbeiter Nr. 42 im Unternehmen von `E-7` (`E-7.42`)
- beliebig tief — die Rekursion endet nie.

Alle Attribute (Name, Rolle, Firmenname, KPIs) werden aus
`sha256(seed:adresse:feld)` abgeleitet (`jarvis_ultra/mega_org.py`). Es gibt
keinen globalen Zufallszustand: dieselbe Adresse liefert immer denselben
Mitarbeiter, ohne dass je etwas gespeichert wird. Namen entstehen aus
Teil-Listen (64 Vornamen × 64 Nachnamen, 32 × 16 × 4 Firmenbausteine), sodass
praktisch unbegrenzt viele unterscheidbare Kombinationen existieren.

## Aggregat-Mathematik (exakt, Big-Int)

Mit `N = D = 10^12` (Mitarbeiter bzw. Developer je Unternehmen) gilt bis zur
Tiefe `t`:

```
mitarbeiter(t)   = Σ N^d   für d = 1..t
unternehmen(t)   = mitarbeiter(t)          # jeder besitzt genau eines
developer(t)     = mitarbeiter(t) · D
mitglieder(t)    = 1 (Jarvis) + mitarbeiter(t) + developer(t)
loadout_items(t) = mitglieder(t) · 84
```

`org_totals(depth)` berechnet diese Werte exakt mit Python-Ganzzahlen;
`format_big()` formatiert deutsch (Punktgruppierung) mit langskaligen
Zahlwörtern (Billion 10¹², Quadrillion 10²⁴, Sextillion 10³⁶ …).

## Katalog

`jarvis_ultra/catalog.py` definiert den kanonischen Loadout: 16 Plugins,
50 Skills, 18 Tools (84 pro Kopf). `full_loadout()` wird jedem Mitarbeiter und
jedem Unternehmen zugewiesen; `has_full_loadout()` prüft Vollständigkeit. Der
Skill-Katalog enthält das komplette Team: die zehn Agentenrollen des
`ultra-enterprise-os`-Plugins (architect, fullstack, qa, security, devops,
data-ml, design, docs, business, orchestrator), die Betriebsmodi (cod,
jarvis-omega, omega-jarvis, omega-enterprise, javier-architect,
ultimate-performance), die komplette Fable-5-Leiter (fable-5, turbo, max,
ultra, milliarden) samt milliarden-unternehmen, die Shopify-Ebene
(shopify-godmode, shopify-operations), die Design-Suite (design-taste,
impeccable, canvas-design, theme-factory, web-artifacts-builder,
artifact-design) sowie Dokument- und Hilfs-Skills (docx, pdf, pptx, xlsx,
skill-creator, morning).

## Terminal-Live-Ticker

`python -m jarvis_ultra.live_ticker` erzeugt pro Tick 1–3 deterministische
Events (`--seed`), darunter Einstellungen, Deployments, Skill-Aktivierungen,
Plugin-Ladevorgänge, Tool-Starts, Unternehmensgründungen, Umsatzmeldungen und
Beförderungen — jedes verweist auf einen konkreten Mitarbeiter samt Unternehmen.
Alle 10 Ticks (und am Ende) erscheint der Gesamtstand über `org_totals`.
`--json` liefert ein maschinenlesbares Event pro Zeile.

## Plugin-Integration

`plugins/jarvis_ultra_ticker/` ist ein reguläres Open.Jarvis-Plugin:

- **Manifest** (`plugin.json`): id `jarvis_ultra_ticker`, Entrypoint
  `plugin.py`, Berechtigungen nur `commands.register` und `ui.notify`
  (Risikostufe *low*), `enabled_by_default: true`.
- **Hooks**: `on_load` registriert die Kommandos, `on_enable` meldet den
  Loadout, `on_command` beantwortet `ticker`, `mega org status` und `loadout`
  über `context.notify(...)`, `on_shutdown` verabschiedet sich. Kein Hook wirft
  Ausnahmen; fehlt das `jarvis_ultra`-Paket, kommt eine saubere deutsche
  Fallback-Meldung.
- Der Import von `jarvis_ultra` geschieht lazy in den Funktionen (der
  Plugin-Loader importiert die Datei isoliert), mit `sys.path`-Erweiterung auf
  die Projektwurzel.

## Dashboard

`dashboard/jarvis-live-ticker.html` ist vollständig autark (kein CDN, keine
Fonts, keine Netzwerkzugriffe) und spiegelt die Python-Logik in JavaScript
(BigInt, FNV-1a-Hash, dieselben Namens-Listen):

- animierte Zähler-Kacheln (exakte BigInt-Werte im Tooltip),
- Live-Feed mit Typ-Filtern, Pause und Hover-Pause,
- Org-Navigator: Breadcrumb ab „JARVIS HQ", 12er-Stichprobe je Ebene,
  Mitarbeiter-Profil mit KPIs und komplettem Loadout, unendlicher Abstieg in
  jedes Unternehmen, Adress-Suche (`7.42.1337`),
- Ticker-Laufband im Footer, `prefers-reduced-motion` wird respektiert.
