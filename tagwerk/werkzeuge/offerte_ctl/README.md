# offerte_ctl

Offerten aus einer ODT-Vorlage erzeugen — ohne Word, ohne Abo, ohne Cloud.

Ein Handwerksbetrieb schreibt eine Offerte, indem er die letzte kopiert,
Namen und Zahlen überschreibt und hofft, keine Zeile vergessen zu haben.
Das dauert zwanzig Minuten und geht regelmässig schief. `offerte_ctl`
macht daraus einen Befehl.

    python3 offerte_ctl.py erstellen vorlage.odt kunde.json

Heraus kommen eine ODT und, falls LibreOffice installiert ist, eine PDF.

## Warum es so gebaut ist

Gebaut nach der Methodik von [cli-anything](https://github.com/HKUDS/CLI-Anything)
(HKUDS, Apache 2.0): erst die Anwendung verstehen, dann die Datenschicht,
dann Probe-Befehle, zuletzt die Befehle, die etwas verändern.

Konkret hiess das hier:

| Phase | Ergebnis |
|---|---|
| 1 — Analyse | Backend ist LibreOffice headless. Datenmodell: ODT ist ein ZIP mit `content.xml`. Vorhandener CLI-Baustein: `soffice --convert-to`. |
| 2 — Architektur | Unterbefehle statt REPL — eine Offerte wird einmal erzeugt, nicht interaktiv bearbeitet. `--json` für Maschinen. |
| 3 — Umsetzung | `vorlage.py` (Daten) → `felder` (Probe) → `erstellen` (Veränderung) → `backend.py` (Anbindung). |

## Befehle

    pruefen                      Ist LibreOffice einsatzbereit?
    vorlage-neu ZIEL             Standardvorlage anlegen
    felder VORLAGE               Platzhalter einer Vorlage zeigen
    erstellen VORLAGE DATEN      Offerte erzeugen

`--json` funktioniert vor und nach dem Unterbefehl.

Für `erstellen` zusätzlich: `--ausgabe ORDNER`, `--name DATEINAME`,
`--nur-odt` (keine PDF), `--locker` (fehlende Werte erlauben).

## Datendatei

```json
{
  "firma": "Maler Rüegg GmbH",
  "firma_adresse": "Musterweg 1, 8645 Jona",
  "kunde": "Meier & Co AG",
  "kunde_adresse": "Beispielgasse 2, 8640 Rapperswil",
  "nummer": "2026-014",
  "ort": "Jona",
  "datum": "29.08.2026",
  "einleitung": "Gerne unterbreiten wir Ihnen folgende Offerte.",
  "gueltig_bis": "28.09.2026",
  "unterschrift": "M. Rüegg",
  "mwst_satz": 8.1,
  "positionen": [
    {"menge": "45", "einheit": "m2", "bezeichnung": "Grundieren", "preis": 810},
    {"menge": "45", "einheit": "m2", "bezeichnung": "Deckanstrich", "preis": 1350},
    {"menge": "1", "einheit": "Pausch.", "bezeichnung": "Reinigung", "preis": 280}
  ]
}
```

## Drei Entscheidungen, die bewusst so sind

**Summen werden gerechnet, nie übernommen.** Steht in der Datendatei ein
`total`, wird es ignoriert. Eine Offerte, in der die Zeilen nicht zur
Summe passen, ist ein Streit mit dem Kunden.

**Ein fehlender Wert ist ein Fehler.** Ohne `--locker` bricht das
Werkzeug ab, statt `{{betrag}}` an einen Kunden zu schicken.

**Werte werden XML-escaped.** Ein Kundenname wie `Meier & Co <AG>` würde
die Datei sonst zerstören. Getestet — mit genau diesem Namen.

## Eigene Vorlage

`vorlage-neu` erzeugt eine schlichte Vorlage zum Anfangen. Ein Betrieb
mit eigenem Briefpapier öffnet stattdessen sein bestehendes Dokument in
LibreOffice, schreibt `{{kunde}}`, `{{positionen}}` und so weiter an die
richtigen Stellen und speichert es als ODT. `felder` zeigt danach, welche
Werte die Datendatei liefern muss.

## Voraussetzungen

Python 3 aus der Standardbibliothek. Für PDF zusätzlich:

    sudo apt-get install libreoffice-writer

Ohne LibreOffice entsteht trotzdem die ODT — das wird gemeldet, nicht
verschwiegen.

## Tests

    python3 -m unittest test_offerte_ctl

23 Tests. Die PDF-Tests überspringen sich selbst, wenn LibreOffice fehlt.
