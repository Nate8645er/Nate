# Tagwerk

Ein Arbeitstag, drei Automatisierungen, Festpreis. Für kleine Betriebe in
Rapperswil-Jona und Umgebung.

## Was hier liegt

| Datei | Zweck |
|---|---|
| `ENTSCHEIDUNG.md` | Warum dieses Modell und nicht die anderen acht |
| `ANGEBOT.md` | Angebot, Preis, Einwandbehandlung, Positionierung |
| `website/index.html` | Die Angebotsseite |
| `akquise/leads.md` | 26 echte Betriebe aus dem öffentlichen Verzeichnis |
| `akquise/skripte.md` | Telefon, Vorgespräch, Abschluss, Nachfassen |
| `dashboard/status.json` | Die einzige Wahrheitsquelle für Zahlen |
| `dashboard/dashboard.py` | Zeigt den Stand, Terminal oder HTML |

## Dashboard

```bash
cd tagwerk/dashboard
python3 dashboard.py          # Terminal
python3 dashboard.py --html   # erzeugt dashboard.html
```

Es zeigt den **Engpass** — die erste Trichterstufe, an der es stockt. Das ist
die einzige Zahl, die zählt: Alles davor ist erledigt, alles danach noch
nicht dran.

Und es warnt, wenn die Verkaufsstunden unter ein Drittel der Baustunden
fallen. Das ist der Frühindikator, der anschlägt, bevor der Umsatz es tut.

## Stand: kein Kunde, kein Umsatz

Es wurde noch niemand kontaktiert. Alle Zahlen im Dashboard stehen auf null,
und das ist die Wahrheit, nicht ein Platzhalter.

## Was nur du erledigen kannst

1. **Telefonnummer auf der Website eintragen.** Steht dort aktuell als
   Platzhalter — der Handlungsaufruf läuft ins Leere.
2. **IBAN und Firmendaten für die QR-Rechnung.** Ohne die kann niemand
   zahlen.
3. **Nummern der ersten fünf Betriebe prüfen.** Die Namen stimmen, die
   Kontaktdaten sind nicht einzeln verifiziert.
4. **Anrufen.** Zwischen 16:30 und 17:30, wenn die Busse zurück sind.

Punkt vier ist der einzige, der über Umsatz entscheidet. Die ersten drei sind
in einer halben Stunde erledigt.

## Kosten bisher

CHF 0. Keine Domain, kein Hosting, kein Werkzeug, kein Abo. Die Website läuft
als Artifact, das Dashboard lokal, die Leadliste stammt aus einem öffentlichen
Verzeichnis.

Wenn später eine eigene Domain gewünscht ist, kostet das etwas — das ist dann
eine Entscheidung mit Kunden im Rücken, nicht davor.

## Regeln, die für dieses Projekt gelten

**Keine erfundenen Zahlen.** Nirgends. Nicht im Dashboard, nicht auf der
Website, nicht im Verkaufsgespräch. Der reduzierte Gründungspreis hat einen
echten Grund und wird auch so genannt.

**Keine Referenzen ohne Kunden.** Auf der Website steht ausdrücklich, dass es
noch keine gibt.

**Absagen gehört dazu.** Wenn die Rechnung beim Kunden nicht aufgeht, wird
nicht verkauft. Ein Kunde unter falschen Erwartungen kostet mehr, als er
einbringt.
