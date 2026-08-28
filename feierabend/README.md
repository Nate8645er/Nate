# Feierabend — Kern der Rapport-Erfassung

**Status: Produktvorhaben in dieser Form gestoppt.** Die Marktanalyse hat die
Grundannahme widerlegt — Schweizerdeutscher Sprachrapport ist bereits
Marktware (e-rapport.ch, CHF 12.50 je Mitarbeiter/Monat, inklusive
Rechnungsstellung). Begründung in
`docs/superpowers/specs/2026-08-28-feierabend-design.md`.

Der Code hier bleibt trotzdem stehen. Nicht aus Anhänglichkeit, sondern weil
drei der vier Bausteine unabhängig vom Produkt taugen.

## Was gebaut ist

| Modul | Zweck | Wiederverwendbar? |
|---|---|---|
| `core/pseudonym.py` | Kundennamen → Token, bevor Text an ein Sprachmodell geht | **Ja** — überall dort, wo Daten Dritter ein fremdes Modell erreichen könnten |
| `core/webhook.py` | HMAC-Signaturprüfung, Wiedereinspielsperre, Nummernfreigabe | **Ja** — für jeden Meta-Webhook |
| `core/extract.py` | Anweisung bauen, Modellantwort streng validieren | **Ja** — das Muster gilt für jede LLM-Extraktion |
| `core/pipeline.py` | Verkettung Audio → Transkript → Token → Modell → Rapport | Nur mit diesem Produkt |
| `spike/` | Prüfstand für das Schweizerdeutsch-Abbruchkriterium | Nur mit diesem Produkt |

## Tests

133 Tests, ohne Netz und ohne API-Schlüssel lauffähig.

```
cd feierabend/tests && python3 -m unittest discover
cd feierabend/spike && python3 -m unittest test_rapport
```

## Die zwei Entwurfsentscheidungen, die zählen

**Nie raten.** Fehlt der Kunde oder die Stundenzahl, geht eine Rückfrage
zurück statt eines Eintrags in die Datenbank. Ein still falsch gespeicherter
Rapport ist schlimmer als gar keiner — er zerstört das Vertrauen in alle
anderen. Deshalb werden auch unplausible Werte (26 Stunden an einem Tag) und
halluzinierte Kunden-Token verworfen statt übernommen.

**Kein Klarname am Modell vorbei.** Nach der Pseudonymisierung prüft ein
Sicherheitsnetz, ob noch ein bekannter Kundenname im Text steht. Schlägt es
an, bricht der Durchlauf ab, bevor irgendetwas das Haus verlässt. Der Grund
steht im Datenschutzteil der Spec: Diese Sprachnachrichten enthalten
vorhersehbar Gesundheitsdaten von Menschen, die nie eingewilligt haben.

## Was fehlt

Anbindung an Transkription und Sprachmodell, Datenbank, Weboberfläche,
Abrechnung. Bewusst nicht gebaut — solange nicht feststeht, dass jemand
zahlt, wäre jede weitere Zeile verlorene Arbeit.
