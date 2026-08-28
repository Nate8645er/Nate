# Schritt 0 — Funktioniert Schweizerdeutsch?

Dieser Vorversuch entscheidet, ob Feierabend gebaut wird. Er beantwortet
**eine** Frage:

> Wenn ein Handwerker auf Schweizerdeutsch in WhatsApp diktiert — wie viele
> Rapporte haben am Ende korrekte Felder?

**Abbruchkriterium: unter 70 % brauchbare Rapporte, und der Kanal wird
verworfen.** Nicht nachgebessert, nicht schöngerechnet. Verworfen.

## Warum nicht die Wortgenauigkeit gemessen wird

Die naheliegende Messung wäre, wie gut die Transkription den Dialekt trifft.
Das ist die falsche Frage. Ein Transkript darf „zwöi Liter Grundierig"
enthalten — solange am Ende `{material: "Grundierung", menge: 2}` herauskommt,
ist der Rapport brauchbar.

Die Sprachmodell-Schicht kann erheblichen Transkriptionsschrott auffangen,
wenn sie den Kundenstamm und die üblichen Materialien des Betriebs kennt. Das
senkt die Anforderung von „versteht Dialekt perfekt" auf „erkennt genug
Stützpunkte". Ob das reicht, misst dieser Versuch.

## Was ein Rapport brauchbar macht

Zwei Pflichtfelder: **Kunde** und **Stunden**. Ohne sie lässt sich nichts
verrechnen — das ist der ganze Zweck. Material und Tätigkeiten verbessern die
Note, tragen den Rapport aber nicht.

Der gefährlichste Fehlerfall ist nicht ein fehlendes Feld, sondern ein
**falsch erkannter Kunde**: Der Rapport sieht vollständig aus und wird dem
falschen Auftrag belastet. Deshalb zählt ein Rapport mit falschem Kunden als
unbrauchbar, egal wie gut der Rest sitzt.

## Was du beisteuern musst

**Zwanzig echte Sprachnachrichten.** Nicht vorgelesen, nicht Hochdeutsch —
so gesprochen, wie es im Lieferwagen tatsächlich klingt.

Achte auf Streuung, sonst misst der Versuch nur einen Sonderfall:

- verschiedene Dialekte (St. Galler, Zürcher, Berner, Walliser)
- verschiedene Umgebungen (Fahrzeug, Baustelle, ruhiger Raum)
- verschiedene Längen (ein Satz bis eine halbe Minute)
- auch **unvollständige** Nachrichten — jemand, der die Stunden vergisst. Das
  System muss nachfragen, nicht raten.

Zu jeder Nachricht gehört die Wahrheit: Was hätte herauskommen müssen?

## Aufbau

| Datei | Zweck |
|---|---|
| `rapport.py` | Rapport-Schema und Bewertungslogik |
| `test_rapport.py` | 34 Tests der Bewertung, laufen ohne Netz |

Die Bewertung ist getestet, bevor der Versuch läuft — misst sie falsch, ist
das Ergebnis wertlos und die Entscheidung über das ganze Produkt beruht auf
einer kaputten Zahl.

```
cd feierabend/spike
python3 -m unittest test_rapport
```

## Noch nicht gebaut

Die Anbindung an Transkription und Sprachmodell fehlt bewusst. Welches
Transkriptionsmodell verwendet wird, ist genau die Frage, die dieser Versuch
beantwortet — sie vorher festzulegen hiesse, das Ergebnis vorwegzunehmen.

Sobald die Audiodateien da sind, wird die Anbindung gebaut: zwei bis drei
Modelle im Vergleich, dieselbe Bewertung, ein Ergebnis.
