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

**Tests:** `test/memory.test.ts` (14) – Ranking, Budget, Merken/Evict,
Datenblock-Escaping, Persistenz mit injiziertem `fetch`.
