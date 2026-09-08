# Automatisierung

**Grundsatz:** Automatisiert wird nur, was heute schon von Hand
funktioniert und mindestens fünfmal gemacht wurde. Alles andere wäre
Automatisierung einer Vermutung.

**Kosten:** CHF 0. Alles läuft lokal mit Python aus der
Standardbibliothek. Keine Abos, keine Trials, keine API-Kosten.
**Keine Ausgabe ohne ausdrückliche Genehmigung.**

---

## Die Kette

```
Zielfirma
   ↓  [automatisch]      cited.py pruefen  → Befund als JSON
Technischer Befund
   ↓  [von Hand, 8 Min]  Fragen an ChatGPT, Perplexity, Google AI
Antworten im Wortlaut
   ↓  [automatisch]      cited.py erfassen → Nennung erkannt
Bewertung
   ↓  [von Hand]         Punkte, Ansprechperson → leads.csv
Qualifizierter Lead
   ↓  [von Hand]         Anruf
Gespräch
   ↓  [von Hand]         Auftragsbestätigung per Mail
Auftrag
   ↓  [automatisch]      cited.py bericht → HTML-Bericht
Lieferung
   ↓  [von Hand]         Besprechung, Rechnung
Kunde
   ↓  [automatisch]      monatliche Wiederholung derselben Prüfung
Beobachtung (Stufe 3)
   ↓  [automatisch]      lagebericht.py → DAILY_REPORT.md, STATUS.md
Auswertung
```

**Was automatisch läuft, ist gebaut und getestet.** Was von Hand läuft,
steht so da, weil es entweder nicht automatisierbar ist (Gespräche) oder
nicht automatisiert werden darf (Antworten der KI-Systeme — siehe unten).

---

## Was bewusst NICHT automatisiert wird

**Die Abfrage der KI-Systeme.** Es gäbe Wege, das zu automatisieren —
API-Zugänge kosten Geld, Browser-Automatisierung verstösst gegen die
Nutzungsbedingungen der Anbieter. Beides scheidet aus: das eine braucht
Genehmigung und Budget, das andere ist Plattformmissbrauch.

Der Nebeneffekt ist ein Vorteil: **Antworten, die ein Mensch im Wortlaut
erfasst hat, sind belastbarer als geschätzte Kennzahlen.** Das ist genau
der Beleg, den die Monitoring-Anbieter nicht mitliefern.

**Die Ansprache.** Jeder Kontakt enthält eine Beobachtung über diese eine
Firma. Sobald das eine Vorlage mit eingesetzten Variablen wird, ist es
Spam — und wirkungslos.

---

## Vorhandene Skripte

| Skript | Was | Status |
|---|---|---|
| `product/sichtbarkeit/cited.py pruefen` | Technischer Befund, neun Felder | **gebaut, 39 Tests, an echten Websites verifiziert** |
| `cited.py fragen` | Fragensatz erzeugen, wiederholbar | gebaut |
| `cited.py erfassen` | Antwort ablegen, Nennung erkennen | gebaut |
| `cited.py bericht` | HTML-Bericht | gebaut |
| `operations/lagebericht.py` | DAILY_REPORT.md und STATUS.md aus status.json, Website-Prüfung | gebaut |

## Wiederkehrende Läufe

Erst einrichten, wenn es einen Kunden gibt. Vorher gibt es nichts zu
überwachen.

```bash
# Täglich, morgens: Lagebericht erzeugen und Website prüfen
python3 business/operations/lagebericht.py --schreiben --pruefen

# Monatlich je Kunde (Stufe 3): dieselbe Prüfung wiederholen
python3 business/product/sichtbarkeit/cited.py pruefen <domain> --json \
  > business/analytics/verlauf/<kunde>-$(date +%Y-%m).json
```

Der Verlaufsordner ist die Grundlage für den Vorher/Nachher-Nachweis.
Ohne ihn ist die monatliche Gebühr nicht begründbar.

## Als Nächstes automatisierbar — in dieser Reihenfolge

1. **Unterseiten mitprüfen**, nicht nur die Startseite. *(Nutzen: hoch,
   Aufwand: klein — erst nach dem ersten Audit, damit klar ist, welche
   Seiten zählen.)*
2. **Verlaufsvergleich zweier Prüfungen** als Tabelle. *(Erst ab dem
   zweiten Messmonat sinnvoll.)*
3. **Kurzbefund als PDF** statt HTML für den Mailanhang.

**Nicht auf der Liste:** Kundenportal, Login, Dashboard-Oberfläche,
automatische Rechnungsstellung. Alles davon ist erst ab etwa zehn Kunden
ein Thema und vorher reine Beschäftigung.
