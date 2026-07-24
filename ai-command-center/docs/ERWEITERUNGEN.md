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

## Video-/Audio-Aufnahme auf der Kamera-Seite (`lib/aufnahme.ts`, `/kamera`)

**Warum:** Die Kamera-Seite konnte nur Fotos aufnehmen/hochladen. Der Wunsch war,
auch **Video und Ton** direkt im Browser aufzunehmen und anzuhängen.

**Was neu ist – additiv, keine neue Abhängigkeit:**
- `lib/aufnahme.ts` (reine, testbare Helfer): `waehleMimeTyp` (erster vom Browser
  unterstützter Codec aus einer Prioritätsliste), `VIDEO_MIME_KANDIDATEN` /
  `AUDIO_MIME_KANDIDATEN`, `dauerFormatieren` (mm:ss), `endungFuer` (Dateiendung
  je MIME).
- Erweiterung von `app/kamera/KameraClient.tsx` um `MediaRecorder`-Aufnahme:
  Buttons „Video aufnehmen" / „Audio aufnehmen", Live-Dauer-Anzeige mit
  Aufnahme-Indikator, „Aufnahme stoppen", anschliessend Wiedergabe
  (`<video>`/`<audio controls>`) und Download. Die bestehende Foto-/Upload-/
  Analyse-Funktion bleibt unverändert.

**Ehrlichkeit/Robustheit:** Ohne Kamera-/Mikrofon-Zugriff klarer Hinweis statt
Fehler; wählt automatisch einen unterstützten Codec (VP9→VP8→WebM→MP4 bzw. Opus),
ohne Fixierung auf ein Format.

**Tests:** `test/aufnahme.test.ts` (6) – MIME-Auswahl inkl. Priorität/leer/werfende
Prüf-Funktion, Dauer-Format, Endungs-Ableitung. Suite 162 grün; tsc + build ok.

## Datei-Anhang für alles (mehrere Dateien + Bilder an eine Mission)

**Warum:** Bisher liess sich genau **ein** Text-/PDF-Dokument an eine Mission
hängen. Gewünscht war, **mehrere** Dateien gleichzeitig anzuhängen – inklusive
**Bilder**.

**Was neu ist – additiv, rückwärtskompatibel:**
- `MissionContext.dokumente?: {name,text}[]` neben dem bestehenden `dokument`
  (`lib/agents/types.ts`). Ältere Clients mit nur `dokument` funktionieren
  unverändert.
- `documentBlock()`/`documentPlannerHint()` (`lib/agents/orchestrator.ts`) fassen
  `dokument` (zuerst) und `dokumente[]` zusammen und hängen **je Datei einen
  abgegrenzten DATENBLOCK** an die Worker-USER-Message. Dateinamen werden gegen
  Marker/Zeilenumbrüche **und Bindestrich-Ketten** gehärtet (kein falscher
  Block-Marker).
- Server (`app/api/mission/route.ts`): `sanitizeDokumente` validiert die Liste,
  begrenzt **Anzahl (6)** und **Gesamt-Zeichen (40 000)** und kappt jeden Eintrag
  wie bisher (Name 80, Text 20 000).
- Dashboard (`app/dashboard/page.tsx`): Datei-Auswahl jetzt **`multiple`** und
  `accept` inkl. `image/*`. Mehrere Chips mit Symbol (📄/🖼), Zeichenzahl und
  Einzel-Entfernen. **Bilder** werden clientseitig über die bestehende KI-Vision
  (`POST /api/bild`) in eine **Text-Beschreibung** umgewandelt und als Kontext
  angehängt – ohne bild-fähiges Modell klarer, ehrlicher Hinweis statt Schein.

**Test-Infrastruktur:** `vitest.config.ts` löst jetzt den `@/`-Alias auf (wie
tsconfig), damit Module getestet werden können, die intern `@/…` importieren
(z. B. der Orchestrator).

**Tests:** `test/dokumente.test.ts` (6) – leer ohne Anhang, Einzel-Dokument
(rückwärtskompatibel), mehrere Dokumente, Kombination, Verwerfen unvollständiger
Einträge, Namens-Härtung gegen Marker-Injection. Suite 168 grün; tsc + build ok.

## Integrationen ausbauen + sichtbar machen (`/erweiterungen`)

**Warum:** Die Integrations-Schicht (`lib/integrations/`) war getestet, aber im
UI **nirgends sichtbar** und deckte nur wenige Dienste ab. Gewünscht war ein
**Ausbau** – inkl. der ehrlichen Antwort auf „Agenten sollen eine ganze Maschine
oder Abteilung bedienen".

**Was neu ist – additiv:**
- **8 neue Module** im Register (`lib/integrations/registry.ts`), jedes Open
  Source, selbst gehostet, per ENV angebunden, mit Health-Pfad und Stufen-Gating:
  Apache Tika (Datei-Extraktion, ergänzt den Datei-Anhang), SearxNG (private
  Suche fürs Browsen), Qdrant (Vektor), Whisper (Sprache-zu-Text für Aufnahmen),
  Flowise (LLM-Flows), MinIO (Objektspeicher), **Node-RED** und **Home Assistant**
  (Geräte-/Anlagensteuerung). Neue Kategorien in `IntegrationKind`: `automation`,
  `search`, `stt`, `storage`, `extract`.
- **Neue Seite `/erweiterungen`** (Server-Component, ISR 30 min) unter *Mehr →
  Erweiterungen* und in der Dashboard-Navigation: gruppierter Katalog mit
  **ehrlichem Verbindungsstatus** – serverseitig aus den ENV abgeleitet
  (`grundStatus`, kein Wert verlässt den Server). Ohne Konfiguration „nicht
  verbunden" statt Schein.

**Sicherheit/Ehrlichkeit:** Geräte-/Computersteuerung (Home Assistant, Node-RED,
Open Interpreter) tragen einen **Freigabe-Hinweis** (Human-in-the-Loop, Token,
isolierte Umgebung). Die App lädt/startet keine fremde Software und löst nichts
automatisch aus – sie ruft nur vom Kunden gehostete Dienste per HTTP an.

**Tests:** `test/integrations.test.ts` erweitert (9) – Katalog-Konsistenz gilt
automatisch auch für die neuen Einträge; zusätzlich: neue Module vorhanden/richtig
kategorisiert, Automations-Module self-hosted + nur ab BUSINESS/ENTERPRISE, Home
Assistant mit Freigabe-Hinweis. Suite 170 grün; tsc + build ok.
