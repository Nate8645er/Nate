# JARVIS Enterprise Live-Ticker — Anleitung

Ausführliche Dokumentation des Enterprise-Moduls von Open.Jarvis: eine
deterministisch simulierte Workforce aus **1.000.000.000.000 direkten
Mitarbeitern** (10¹², „1000 Milliarden"), von denen jeder ein eigenes
Unternehmen mit 10¹² Mitarbeitern und einem zusätzlichen 10¹²-köpfigen
Developer-Team führt — **Gesamt-Workforce: 2·10²⁴ + 10¹² =
2.000.000.000.001.000.000.000.000**.

Alles läuft offline, ausschließlich mit der Python-Standardbibliothek
(bzw. eigenständigem JavaScript im Dashboard).

---

## Inhalt

1. [Architektur](#architektur)
2. [Deterministisches Prinzip](#deterministisches-prinzip)
3. [CLI-Referenz](#cli-referenz)
4. [Python-API](#python-api)
5. [Dashboard-Funktionen](#dashboard-funktionen)
6. [Event-Typen](#event-typen)
7. [Plugin-Katalog: 128 echte Plugins](#plugin-katalog-128-echte-plugins)
8. [FAQ](#faq)

---

## Architektur

Das Enterprise-Modul besteht aus vier Python-Dateien in
`open_jarvis/enterprise/` plus dem eigenständigen HTML-Dashboard:

```text
┌──────────────────────────────────────────────────────────────────────┐
│  catalog.py            Single Source of Truth                        │
│                        200 Skills · 128 Plugins · 192 Tools          │
│                        (je 16 Kategorien)                            │
└───────────────┬──────────────────────────────────────────────────────┘
                │  all_skills(), all_plugins(), all_tools(),
                │  catalog_summary(), export_catalog_json()
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  workforce.py          deterministische Workforce-Engine             │
│                        mix64() · employee_identity() · employee()    │
│                        workforce_summary() · Konstanten (10¹², …)    │
└───────────────┬──────────────────────────────────────────────────────┘
                │  employee_identity(id), Konstanten
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  live_ticker.py        Event-Engine                                  │
│                        LiveTicker · event_for_tick() · 10 Templates  │
└───────────────┬──────────────────────────────────────────────────────┘
                │  LiveTicker.tick(), aggregate_stats()
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  __main__.py           Terminal-Frontend                             │
│                        python3 -m open_jarvis.enterprise             │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  dashboard/jarvis_live_ticker.html                                   │
│  Browser-Frontend: eigene JavaScript-Implementierung derselben       │
│  Algorithmen (BigInt) + eingebetteter Katalog — bitidentisch zur     │
│  Python-Engine, komplett offline, keine externen Ressourcen.         │
└──────────────────────────────────────────────────────────────────────┘
```

- **`catalog.py`** definiert die drei Kataloge `SKILL_CATALOG`,
  `PLUGIN_CATALOG` und `TOOL_CATALOG` als geordnete Kategorie-Wörterbücher
  und liefert flache Listen (`all_skills()` usw.), Kennzahlen
  (`catalog_summary()`) und einen JSON-Export (`export_catalog_json()`).
- **`workforce.py`** enthält die Konstanten (`EMPLOYEES_DIRECT`,
  `COMPANY_EMPLOYEES`, `COMPANY_DEVELOPERS`, `TOTAL_WORKFORCE`), den
  SplitMix64-Hash `mix64()` und die Mitarbeiter-Ableitung
  (`employee_identity()` leichtgewichtig, `employee()` vollständig inkl.
  Katalog-Blöcken und Unternehmensdaten).
- **`live_ticker.py`** erzeugt aus `(seed, tick)` deterministische Events
  über die Workforce (Klasse `LiveTicker`).
- **`__main__.py`** ist das Terminal-Frontend mit Kopfzeile, Kennzahlen
  und Endlos- bzw. N-Tick-Betrieb.
- **Das Dashboard** implementiert `mix64`, die Mitarbeiter-Ableitung und
  die Event-Engine noch einmal in JavaScript (mit `BigInt` für exakte
  64-Bit- und 10²⁴-Arithmetik) und bettet den kompletten Katalog ein.

---

## Deterministisches Prinzip

Es gibt **keine Datenbank** und **keinen Zufallszahlengenerator mit
Zustand**: Jeder Mitarbeiter und jedes Event wird bei Bedarf rein
funktional aus einer Ganzzahl berechnet. Grundbaustein ist der
**SplitMix64-Finalizer** in 64-Bit-Arithmetik:

```python
MASK = (1 << 64) - 1

def mix64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return (z ^ (z >> 31)) & MASK
```

### Mitarbeiter-Ableitung (ID: 1 bis 10¹², inklusive)

Aus der ID wird eine Hash-Kette gebildet; jedes Kettenglied wählt ein
Merkmal aus festen, exakt geordneten Listen:

| Schritt | Formel | Merkmal | Liste (Größe) |
|---|---|---|---|
| `h1 = mix64(id)` | `h1 % 32` | Vorname | `FIRST_NAMES` (32) |
| `h2 = mix64(h1)` | `h2 % 32` | Nachname | `LAST_NAMES` (32) |
| `h3 = mix64(h2)` | `h3 % 24` | Rolle | `ROLES` (24) |
| `h4 = mix64(h3)` | `h4 % 16` | Abteilung | `DEPARTMENTS` (16) |
| `h5 = mix64(h4)` | `h5 % 16` | Firmen-Suffix | `COMPANY_SUFFIXES` (16) |
| `h6 = mix64(h5)` | `h6 % 200` | Spezialisierung | `all_skills()` (200, Katalog-Reihenfolge) |

Daraus entstehen:

- `name = Vorname + " " + Nachname`
- `badge = "JRV-" + ID, links auf 13 Stellen mit Nullen aufgefüllt`
- `company_name = Name + " " + Firmen-Suffix`

Jeder Mitarbeiter besitzt zusätzlich **alle 200 Skills, alle 128 Plugins
und alle 192 Tools** des Katalogs, und sein Unternehmen (10¹² Mitarbeiter
plus 10¹² Entwickler) ebenfalls.

**Gleiche ID ⇒ gleicher Mitarbeiter — immer und überall.** Die
JavaScript-Implementierung im Dashboard verwendet `BigInt` mit
`& 0xFFFFFFFFFFFFFFFFn` und liefert für dieselbe ID bitidentische
Ergebnisse wie Python. Beispiel (reproduzierbar):

```python
>>> from open_jarvis.enterprise.workforce import employee_identity
>>> employee_identity(42)
{'id': 42, 'first': 'Theo', 'last': 'Almeida', 'name': 'Theo Almeida',
 'badge': 'JRV-0000000000042', 'role': 'Product Manager',
 'department': 'DevOps & Cloud', 'specialization': 'Videoproduktion',
 'company_name': 'Theo Almeida Werke'}
```

Wer im Dashboard-Inspektor die ID `42` eingibt, sieht exakt denselben
Datensatz.

### Event-Ableitung

Events entstehen rein aus `(seed, tick)`:

```text
e      = mix64(seed XOR mix64(tick))
emp_id = (e mod 10¹²) + 1              → betroffener Mitarbeiter
e_type = mix64(e) mod 10               → Event-Template (siehe unten)
d1, d2, d3 = weitere mix64-Runden      → Zahlen, Prozente, Projekt-Codes, Versionen
```

Zwei Ticker mit demselben Seed erzeugen deshalb exakt dieselbe
Event-Sequenz — in Python und im Browser.

---

## CLI-Referenz

Der Terminal-Ticker wird aus dem Verzeichnis `jarvis/` gestartet:

```bash
python3 -m open_jarvis.enterprise [--ticks N] [--interval SEK] [--seed N] [--summary]
```

| Option | Typ | Standard | Bedeutung |
|---|---|---|---|
| `--ticks N` | int | `0` | Anzahl der Events. `0` (oder weggelassen) = endlos bis `Strg+C`. |
| `--interval SEK` | float | `1.0` | Pause zwischen zwei Events in Sekunden. `0` = so schnell wie möglich. |
| `--seed N` | int | `20260712` | Seed der Event-Sequenz. Gleicher Seed ⇒ gleiche Sequenz. |
| `--summary` | Flag | aus | Gibt nur die globalen Kennzahlen als JSON aus und beendet sich. |

### Beispiel 1: 20 Events mit Standard-Seed

```bash
cd jarvis
python3 -m open_jarvis.enterprise --ticks 20
```

### Beispiel 2: Reproduzierbare Sequenz, ohne Pause

```bash
cd jarvis
python3 -m open_jarvis.enterprise --ticks 6 --interval 0 --seed 42
```

Beispielausgabe (bei `--seed 42` immer exakt identisch):

```text
==============================================================================
  JARVIS ENTERPRISE — LIVE-TICKER
==============================================================================
  Mitarbeiter direkt:          1.000.000.000.000
  Mitarbeiter je Unternehmen:  1.000.000.000.000
  Entwickler je Unternehmen:   1.000.000.000.000
  Entwickler gesamt:           1.000.000.000.000.000.000.000.000
  Gesamt-Workforce:            2.000.000.000.001.000.000.000.000
  Katalog: 200 Skills | 128 Plugins | 192 Tools (je 16 Kategorien)
  Seed: 42 | Intervall: 0.0s | Ticks: 6
------------------------------------------------------------------------------
#     1  JRV-0320742759466  🏢 Kai Quandt Dynamics: 21.252 neue Entwickler im Onboarding
#     2  JRV-0525164838580  🧠 Aria Kovacs hat Skill "Ticket-Management" auf Level MAX zertifiziert
#     3  JRV-0236239627171  ✅ Emil Sato hat Projekt PRJ-FF4094 erfolgreich abgeschlossen
#     4  JRV-0711120590920  🛰️ JARVIS synchronisiert 471.318.857 Unternehmens-Knoten im Orbit-Cluster
#     5  JRV-0987070419363  🛠️ Tool "Icon-Bibliothek" auf Version 3.27 aktualisiert bei Sofia Kovacs Networks
#     6  JRV-0050861303281  📈 Maya Almeida Robotics meldet +23% Produktivität in Design
```

### Beispiel 3: Endlosbetrieb (Abbruch mit Strg+C)

```bash
cd jarvis
python3 -m open_jarvis.enterprise --interval 0.5
```

Nach `Strg+C` erscheint eine Abschluss-Statistik, z. B.:

```text
Live-Ticker beendet nach 137 Events (137 Mitarbeiter gesehen).
```

### Beispiel 4: Nur die Kennzahlen als JSON

```bash
cd jarvis
python3 -m open_jarvis.enterprise --summary
```

```json
{
  "employees_direct": 1000000000000,
  "companies": 1000000000000,
  "company_employees": 1000000000000,
  "company_developers": 1000000000000,
  "total_workforce": 2000000000001000000000000,
  "total_developers": 1000000000000000000000000,
  "skills": 200,
  "plugins": 128,
  "tools": 192,
  "skill_categories": 16,
  "plugin_categories": 16,
  "tool_categories": 16
}
```

---

## Python-API

Die Engine lässt sich direkt aus Python nutzen:

```python
from open_jarvis.enterprise.workforce import employee, employee_identity, workforce_summary
from open_jarvis.enterprise.live_ticker import LiveTicker

# Beliebige Mitarbeiter-ID inspizieren (1 bis 10**12, inklusive):
mitarbeiter = employee(123_456_789_000)
print(mitarbeiter["name"], "—", mitarbeiter["role"])
print(mitarbeiter["skills"]["count"])           # 200
print(mitarbeiter["company"]["developers"])     # 1000000000000

# Deterministische Event-Sequenz:
ticker = LiveTicker(seed=42)
for event in ticker.stream(5):
    print(event["badge"], event["text"])
print(ticker.aggregate_stats())

# Globale Kennzahlen:
print(workforce_summary()["total_workforce"])   # 2000000000001000000000000
```

Ungültige IDs (`0`, negative Werte, `> 10**12`) lösen einen `ValueError`
aus — der gültige Bereich ist `1` bis `10**12` **inklusive**.

---

## Dashboard-Funktionen

Datei: [`../dashboard/jarvis_live_ticker.html`](../dashboard/jarvis_live_ticker.html)
— einfach im Browser öffnen. Eine einzige, komplett eigenständige
HTML-Datei: kein Server, kein CDN, keine Fonts von außen, keine
`fetch`-Aufrufe. Alle Berechnungen laufen lokal in JavaScript (`BigInt`).

| Bereich | Funktion |
|---|---|
| **Kennzahlen** | Zeigt die globalen Zahlen der Workforce: 10¹² direkte Mitarbeiter, 10¹² Unternehmen, je 10¹² Mitarbeiter + 10¹² Entwickler pro Unternehmen, Gesamt-Workforce 2·10²⁴ + 10¹² sowie den Katalog (200 Skills / 128 Plugins / 192 Tools). Die großen Zahlen werden mit `BigInt` exakt berechnet, nie gerundet. |
| **Ticker-Steuerung** | Live-Ticker starten und pausieren, Geschwindigkeit (Intervall) einstellen und den Seed ändern. Gleicher Seed ⇒ exakt dieselbe Event-Sequenz wie im Terminal-Ticker mit `--seed`. |
| **Inspektor** | Beliebige Mitarbeiter-ID (1 bis 10¹²) eingeben und den vollständigen deterministischen Datensatz ansehen: Name, Badge, Rolle, Abteilung, Spezialisierung, Unternehmen (Name, 10¹² Mitarbeiter, 10¹² Entwickler) sowie die Fähigkeiten-Zähler (200/128/192). Identisch zur Python-Ausgabe von `employee()`. |
| **Katalog-Browser** | Alle 200 Skills, 128 Plugins und 192 Tools nach den 16 Kategorien durchstöbern — derselbe Katalog wie in `open_jarvis/enterprise/catalog.py`, direkt in die HTML-Datei eingebettet. |

---

## Event-Typen

Der Live-Ticker kennt genau **10 Event-Templates**. Der Typ wird
deterministisch per `mix64(e) mod 10` gewählt; Platzhalter stammen aus dem
Mitarbeiter-Datensatz, Zahlen aus weiteren `mix64`-Runden.

| Nr. | Typ (intern) | Template | Deterministische Werte |
|---:|---|---|---|
| 1 | `feature` | 🚀 {name} ({role}, {department}) hat bei {company} ein neues Feature ausgeliefert | — |
| 2 | `onboarding` | 🏢 {company}: {n} neue Entwickler im Onboarding | n: 1.000–99.999 |
| 3 | `projekt` | ✅ {name} hat Projekt {projektcode} erfolgreich abgeschlossen | Code: `PRJ-` + 6 Hex-Stellen |
| 4 | `produktivitaet` | 📈 {company} meldet +{pct}% Produktivität in {department} | pct: 2–49 |
| 5 | `skill` | 🧠 {name} hat Skill "{skill}" auf Level MAX zertifiziert | Skill: einer der 200 |
| 6 | `plugin` | 🔌 Plugin "{plugin}" bei {company} konzernweit ausgerollt | Plugin: eines der 128 |
| 7 | `tool` | 🛠️ Tool "{tool}" auf Version {maj}.{min} aktualisiert bei {company} | Tool: eines der 192; maj: 1–9, min: 0–99 |
| 8 | `sync` | 🛰️ JARVIS synchronisiert {k} Unternehmens-Knoten im Orbit-Cluster | k: 100.000.000–999.999.999 |
| 9 | `partnerschaft` | 🤝 {company} startet Partnerschaft mit {company2} | Partner: zweites, deterministisch gewähltes Unternehmen |
| 10 | `auszeichnung` | 🏆 {name} zum "Mitarbeiter des Zyklus" in {department} ernannt | — |

Jedes Event-Objekt enthält `tick`, `employee_id`, `badge`, `text` und
`type` — die betroffene Mitarbeiter-ID kann also jederzeit im Inspektor
oder per `employee()` nachgeschlagen werden.

---

## Plugin-Katalog: 128 echte Plugins

Die 128 Plugins des Katalogs sind nicht nur Namen: Sie liegen als **echte,
ladbare Open.Jarvis-Plugins** unter `plugins/<plugin_id>/` — 16 Kategorien
à 8 Plugins, exakt wie in `open_jarvis/enterprise/catalog.py` definiert.

### Aufbau eines Plugins

Jedes Plugin besteht aus genau zwei Dateien:

```text
plugins/<plugin_id>/
├── plugin.json   ← Manifest
└── main.py       ← Entrypoint (nur Standardbibliothek, kein Netzwerk)
```

Format von `plugin.json`:

```json
{
  "id": "medien_unterhaltung_spotify_steuerung",
  "name": "Spotify-Steuerung",
  "version": "1.0.0",
  "entrypoint": "main.py",
  "description": "JARVIS-Plugin „Spotify-Steuerung“ aus der Katalog-Kategorie „Medien & Unterhaltung“ mit deutschen Sprachbefehlen.",
  "permissions": ["commands.register", "ui.notify"]
}
```

Die `plugin_id` wird deterministisch aus Kategorie und Plugin-Name gebildet
(kleingeschrieben, nur `a–z`, `0–9`, `_`): aus „Medien & Unterhaltung" +
„Spotify-Steuerung" wird `medien_unterhaltung_spotify_steuerung`.

`main.py` liefert beim direkten Ausführen ein JSON mit `plugin_id`,
`kategorie` und deutschen Sprachbefehlen:

```bash
python3 plugins/medien_unterhaltung_spotify_steuerung/main.py
```

### Registry

Die Plugin-Registry von Open.Jarvis entdeckt und validiert alle 128
Plugins, **ohne Plugin-Code auszuführen**:

```python
from open_jarvis.plugins.registry import build_plugin_registry

registry = build_plugin_registry("plugins")
print(registry["summary"])   # 128 Plugins, 0 blockiert
```

Jedes Manifest wird gegen das Schema (`open_jarvis/plugins/manifest.py`)
und die Berechtigungs-Richtlinien (`open_jarvis/plugins/permissions.py`)
geprüft; alle 128 Plugins nutzen nur die risikoarmen Berechtigungen
`commands.register` und `ui.notify`. Details: [`../plugins/README.md`](../plugins/README.md).

---

## FAQ

### Warum eine Simulation?

Weil es der einzige ehrliche und zugleich exakte Weg ist, eine Organisation
dieser Größe abzubilden. 2·10²⁴ + 10¹² Mitarbeiter lassen sich weder als
Prozesse starten noch als Datensätze speichern (allein die IDs wären
Zettabytes). Die deterministische Ableitung macht die Organisation trotzdem
**vollständig real inspizierbar**: Jede der 10¹² Mitarbeiter-IDs liefert
jederzeit, auf jedem Rechner, in Python wie im Browser exakt denselben
Datensatz — nichts wird „ausgedacht", alles ist reproduzierbar. Der
Live-Ticker ist damit eine virtuelle Organisation, die on-the-fly berechnet
statt gespeichert wird.

### Wie funktionieren die großen Zahlen technisch?

- **Python** rechnet nativ mit beliebig großen Ganzzahlen (`int`), daher
  ist `TOTAL_WORKFORCE = 10**12 + 10**12 * (10**12 + 10**12)` exakt —
  keine Rundung, kein Float.
- **JavaScript** nutzt dafür `BigInt`
  (`10n ** 12n + 2n * 10n ** 24n`), da normale `Number`-Werte oberhalb
  von 2⁵³ ungenau würden. Auch die 64-Bit-Hash-Arithmetik läuft im
  Dashboard über `BigInt` mit der Maske `0xFFFFFFFFFFFFFFFFn`.
- Die Kennzahlen werden **immer als Ausdruck berechnet und nie als
  Zahl abgetippt** — so können sich Python und JavaScript nicht
  auseinanderentwickeln.

### Wie erweitere ich den Katalog?

Ausschließlich in der Single Source of Truth
`open_jarvis/enterprise/catalog.py`:

1. Eintrag in der passenden Kategorie von `SKILL_CATALOG`,
   `PLUGIN_CATALOG` oder `TOOL_CATALOG` ergänzen (oder eine neue
   Kategorie anlegen). Die Reihenfolge ist bedeutsam: Die flachen Listen
   (`all_skills()` usw.) bestimmen, welche Spezialisierung bzw. welcher
   Event-Inhalt zu welchem Hash-Wert gehört.
2. Abgeleitete Stellen nachziehen: Die Modulo-Konstanten in
   `workforce.py`/`live_ticker.py` und im Dashboard entsprechen den
   Katalog-Größen (200/128/192) — bei geänderten Größen anpassen, sonst
   weichen Python und JavaScript voneinander ab. Für ein neues Plugin
   zusätzlich den Ordner `plugins/<plugin_id>/` mit `plugin.json` und
   `main.py` anlegen.
3. Den eingebetteten Katalog im Dashboard
   (`dashboard/jarvis_live_ticker.html`) synchron halten — Vorlage ist
   `catalog.export_catalog_json()`.
4. Tests laufen lassen:

```bash
cd jarvis
python3 -m pytest tests/test_enterprise_*.py
```

Die Suiten `test_enterprise_workforce.py`, `test_enterprise_live_ticker.py`
und `test_enterprise_plugins.py` prüfen Katalog-Größen, Determinismus und
alle 128 Plugin-Manifeste.

### Beeinflusst das Enterprise-Modul den Assistenten?

Nein. Das Modul ist rein additiv, benötigt keine zusätzlichen
Abhängigkeiten und keinen Netzwerkzugriff. Der Open.Jarvis-Assistent
(`python jarvis.py`) funktioniert unverändert; die 128 Plugins nutzen nur
die risikoarmen Berechtigungen `commands.register` und `ui.notify`.
