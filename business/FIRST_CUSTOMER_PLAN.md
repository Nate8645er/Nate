# Plan bis zum ersten zahlenden Kunden

**Grundsatz:** Ab jetzt wird nichts mehr gebaut, was nicht direkt zu
einem Gespräch führt. Das Werkzeug läuft, der Bericht sieht aus wie ein
Gutachten, die Website steht. Was fehlt, sind Menschen, die gefragt
wurden.

---

## Stunde 0–2 · Was noch gebaut werden muss

**Fast nichts.** Das ist Absicht.

| Aufgabe | Dauer | Status |
|---|---|---|
| Prüfwerkzeug einsatzbereit | — | ✔ fertig, 39 Tests, an echten Sites geprüft |
| Bericht erzeugbar | — | ✔ fertig |
| Website | — | ✔ veröffentlicht |
| Angebot, Preise, Skripte | — | ✔ fertig |
| **Liste mit 25 Zielfirmen zusammenstellen** | 60 Min | offen — **von Nate** |
| **Erreichbarkeit prüfen: Telefon und Ansprechperson** | 30 Min | offen — **von Nate** |
| Domain entscheiden und registrieren | 15 Min | offen — **braucht Genehmigung (CHF ~15/Jahr)** |

**Nicht bauen:** Logo, Kundenportal, automatische API-Abfragen,
Verlaufsdiagramme, Rechnungssystem. Alles davon ist erst nach dem
dritten Kunden ein Thema.

---

## Stunde 2–4 · Was validiert werden muss

Nicht die Technik — die ist geprüft. Zu validieren ist die **Annahme**.

### Prüfschritt 1: Sind die Zielfirmen tatsächlich unsichtbar?

Für die ersten fünf Firmen den Kurzbefund erstellen:

```
python3 cited.py pruefen <domain>
```

**Erwartung:** Mindestens drei von fünf liegen unter 70 % oder sperren
Antwort-Crawler.

**Wenn nicht:** Die Zielgruppe stimmt nicht. Dann eine Branche wählen,
deren Websites schwächer sind — Handwerk und Gesundheitsberufe vor
IT-Dienstleistern.

### Prüfschritt 2: Werden sie in Antworten wirklich nicht genannt?

Für dieselben fünf je drei Fragen an ChatGPT, Perplexity und Google AI
stellen. Antworten im Wortlaut erfassen:

```
python3 cited.py fragen --firma "..." --domain ... --branche ... --ort ... \
  --leistung ... --datei erhebungen/<firma>.json --anzahl 5
python3 cited.py erfassen --datei erhebungen/<firma>.json \
  --system ChatGPT --frage 1 --antwort-datei antwort.txt
```

**Erwartung:** Bei mindestens der Hälfte kommt die Firma nicht vor,
dafür ein Konkurrent.

**Das ist der eigentliche Test des ganzen Geschäfts.** Wenn die
Zielfirmen problemlos genannt werden, gibt es kein Problem zu lösen —
und dann muss die Zielgruppe gewechselt werden, nicht das Verkaufsskript.

### Prüfschritt 3: Interessiert es sie?

Erst nach 1 und 2. Zwei Anrufe, nur um zu hören, ob die Reaktion
Neugier oder Gleichgültigkeit ist. Noch nichts verkaufen.

**Abbruchkriterium:** Wenn nach zehn erreichten Gesprächen niemand ein
20-Minuten-Gespräch will, ist die Annahme falsch. Dann nicht das Skript
ändern, sondern die Zielgruppe.

---

## Stunde 4–8 · Kundengewinnung

**Reihenfolge, nicht Parallelbetrieb.**

1. **Kurzbefunde für 15 Firmen erstellen.** Rund 15 Minuten je Firma,
   davon 13 automatisch. → ca. 3 Stunden für alle.
2. **Aussortieren.** Firmen mit gutem Befund fallen raus. Erwartung:
   9–12 bleiben.
3. **Anrufen, 16:30–17:30.** Nicht mailen. Der Befund ist am Telefon
   stärker, weil man ihn vorlesen kann und die Reaktion hört.
4. **Nach jedem Anruf:** Mail mit dem Kurzbefund als Anhang. Nur an
   Erreichte. Nie unaufgefordert vorher — rechtlich heikel und
   wirkungslos.
5. **Ziel des Anrufs:** kein Verkauf, sondern ein 20-Minuten-Termin.

**Erwartung, ehrlich:** 15 Wählversuche → 5–7 erreicht → 2–3 Termine →
0–1 Abschluss. Wer nach 15 Anrufen aufhört, hat nichts gemessen.

---

## Stunde 8–24 · Optimierung

Was nach der ersten Runde ausgewertet wird — **an Zahlen, nicht am
Gefühl**:

| Frage | Woran messbar | Was folgt daraus |
|---|---|---|
| Kommt der Einstieg an? | Anteil, der nach 30 Sek. noch dran ist | Unter 50 % → Einstieg neu formulieren |
| Versteht er das Problem? | Rückfragen statt Höflichkeit | Wenn nicht → nicht erklären, sondern vorlesen |
| Ist der Befund überzeugend? | Anteil Termine je erreichtem Gespräch | Unter 30 % → mehr Antworten pro Kurzbefund erfassen |
| Ist der Preis das Hindernis? | Wie oft „zu teuer" gegen andere Einwände | Selten → Preis war zu tief |
| Ist die Branche richtig? | Befundwerte je Branche | Streuen → auf die schwächste Branche fokussieren |

**Die wichtigste Auswertung:** Wenn abgesagt wird — welcher Satz kam?
Fünf Absagen mit demselben Satz sagen mehr als fünfzig Kurzbefunde.

---

## Der Ablauf in einem Bild

```
Zielfirma
   ↓
Kurzbefund (15 Min, weitgehend automatisch)
   ↓
Befund schlecht? ── nein ──→ nicht anrufen. Kein Kunde.
   ↓ ja
Anruf mit dem konkreten Ergebnis
   ↓
20-Minuten-Gespräch: Befund gemeinsam ansehen
   ↓
Audit CHF 790 (Gründungspreis)
   ↓
Fünf Arbeitstage Lieferung
   ↓
Besprechung → Umsetzung (2'400) oder Beobachtung (290/Mt.)
```

---

## Was diesen Plan scheitern lässt

**Weiterbauen.** Das Werkzeug lädt dazu ein: automatischer API-Abruf
wäre elegant, ein Portal wäre schön, ein Logo wäre hübsch. Nichts davon
bringt einen Anruf näher. Jede Stunde Bauzeit vor dem ersten Kunden ist
eine Stunde, in der niemand gefragt wurde.

**Die Regel für die nächsten Tage:** Keine Zeile Code, bis der erste
Kurzbefund telefonisch besprochen wurde.
