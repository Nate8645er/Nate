# Erweiterungen des KI-Systems

Prinzip: **erweitern statt ersetzen**. Jede Erweiterung ist additiv, getestet und
lässt bestehende Funktionen unverändert. Ohne Konfiguration verhält sich das
System exakt wie vorher.

## Langzeitgedächtnis & Kontextverwaltung (`lib/agents/memory.ts`)

**Warum:** Bisher kannte eine Mission nur den mitgesendeten Kontext (Branche,
Dokument, Web-Recherche). Es fehlte ein **Gedächtnis über Sitzungen hinweg**.

**Was neu ist – ausschliesslich additiv:**
- Reiner, getesteter Kern (keine Abhängigkeiten):
  - `relevanteErinnerungen(alle, anfrage, opts)` – Relevanz-Ranking
    (Schlagwort-Überschneidung + Aktualität) mit **Anzahl- und Zeichenbudget**
    → verbessert Kontextqualität **und** Token-Effizienz.
  - `erinnerungMerken(alle, neu, max)` – hinzufügen, Duplikate entfernen,
    Gesamtzahl begrenzen (älteste zuerst verworfen).
  - `erinnerungenBlock(erinnerungen)` – injection-sicherer DATENBLOCK für die
    Worker-USER-Message, im selben Stil wie `documentBlock`/`rechercheBlock`.
    Leer, wenn nichts vorliegt → **kein geändertes Verhalten**.
- Optionale Persistenz über Supabase PostgREST (wie `lib/kunden.ts`):
  `gedaechtnisKonfiguriert`, `erinnerungenLaden`, `erinnerungSpeichern`.
  Ohne `SUPABASE_SERVICE_ROLE_KEY` ehrlich „nicht-konfiguriert".

**Integration (minimal-invasiv):**
- `MissionContext.erinnerungen?` (neues optionales Feld in `lib/agents/types.ts`).
- `workerMessages()` hängt `erinnerungenBlock(context?.erinnerungen)` an – neben
  Dokument- und Recherche-Block. Ohne Einträge ändert sich nichts.

**Sicherheit:** Gespeicherte Texte sind DATEN, keine Anweisungen; der Block ist
gegen Prompt-Injection abgegrenzt und gehört nur in die USER-Message (nie in den
System-Prompt). Tabelle `gedaechtnis` mit RLS an, Zugriff nur über Service-Role.

**Aktivierung:** `supabase/schema.sql` ausführen (Tabelle `gedaechtnis`) und die
Supabase-Variablen setzen. Danach kann der Mission-Endpoint Erinnerungen laden,
die relevantesten auswählen und nach der Mission neue Fakten speichern.

**Tests:** `test/memory.test.ts` (15) – Ranking, Budget, Merken/Evict,
Datenblock-Escaping (inkl. Delimiter-Härtung), Persistenz mit injiziertem `fetch`.

## Zuverlässigkeit: JSON-Reparatur & Retry (`lib/agents/zuverlaessigkeit.ts`)

**Warum:** LLM-Ausgaben sind oft leicht defekt (```json-Zäune, Fliesstext,
typografische Quotes, abschliessende Kommas) oder scheitern flüchtig
(Netzwerk/Rate-Limit). Das kostet Genauigkeit und Zuverlässigkeit.

**Was neu ist – additiv:**
- `jsonReparieren(text)` – schneidet die erste balancierte JSON-Struktur heraus
  (String-/Escape-bewusst), entfernt Zäune, repariert Quotes/Kommas; gibt das
  Objekt oder `null` zurück (wirft nie).
- `mitWiederholung(fn, opts)` – Retry mit exponentiellem Backoff, injizierbarem
  Sleep und optionalem Ergebnis-Validator.
- `backoffPlan`, `sichereZahl` – deterministische Helfer.

**Integration (minimal-invasiv):** `parseJsonObject()` im Orchestrator nutzt
`jsonReparieren` jetzt als **Fallback**, wenn der bisherige naive Weg scheitert.
Der Erfolgspfad für sauberes JSON bleibt exakt gleich; nur bisher unlesbare
Antworten (Plan, Quality-Report) werden zusätzlich gerettet → robustere Missionen.

**Tests:** `test/zuverlaessigkeit.test.ts` (14) – Reparaturfälle, Backoff, Retry
(Erfolg/Erschöpfung/Abbruch/Validator), sichere Zahl.

## Kamera & Bildverständnis (`lib/vision.ts`, `/kamera`, `/api/bild`)

**Warum:** Bisher konnte man nur Textdokumente anhängen. Es fehlte Kamera/Bild.

**Was neu ist – additiv, keine neue Abhängigkeit:**
- Neue Seite **`/kamera`** (in der Dashboard-Navigation): Foto per Gerätekamera
  aufnehmen (getUserMedia) ODER Bild hochladen, optionale Frage stellen, von der
  KI beschreiben/auswerten lassen (z. B. Beleg, Notiz, Whiteboard, Produktfoto).
  Reine Browser-APIs (getUserMedia, canvas, FileReader); ohne Kamera sauberer
  Upload-Fallback.
- `lib/vision.ts`: `bildBeschreiben` (Anthropic-Vision-REST, dependency-frei,
  injizierbarer fetch), `dataUrlZerlegen`, `visionKonfiguriert`. Ohne
  ANTHROPIC_API_KEY ehrlich „nicht-konfiguriert".
- `app/api/bild/route.ts`: nimmt data-URL + Frage, Grössen-/Typprüfung, 501 ohne
  Key.

**Sicherheit/Ehrlichkeit:** Bild-Analyse liefert nur mit verbundenem bild-fähigem
Modell echte Ergebnisse; ohne Key klarer Hinweis statt Schein-Ergebnis. Bildgrösse
serverseitig begrenzt (~6 MB). Nutzt den bestehenden ANTHROPIC_API_KEY.

**Tests:** `test/vision.test.ts` (7) – Konfig, data-URL-Parsing, Request-Aufbau
(Bild+Frage an Anthropic), ehrliche Fehlerpfade. Suite 156 grün; tsc + build ok.
