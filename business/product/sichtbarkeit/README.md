# cited — KI-Sichtbarkeit prüfen

Beantwortet zwei Fragen über eine Website:

1. **Könnte ein KI-System sie überhaupt lesen und daraus zitieren?**
   Neun Prüffelder, vollautomatisch, jederzeit wiederholbar.
2. **Wird die Firma in KI-Antworten tatsächlich genannt?**
   Fragensatz erzeugen, Antworten im Wortlaut erfassen, Nennungen zählen.

## Was dieses Werkzeug NICHT tut

**Es ruft keine KI-Systeme auf.** Keine API-Zugänge, kein Budget, keine
automatischen Abfragen von ChatGPT, Perplexity oder Gemini.

Der Fragensatz wird erzeugt, die Antworten stellt und erfasst ein
Mensch. Dadurch ist jede Zahl im Bericht auf eine nachlesbare Antwort
zurückführbar. Eine geschätzte Nennung wäre eine erfundene Zahl, und
eine erfundene Zahl macht den ganzen Bericht wertlos.

Der Bericht weist beide Teile getrennt aus. Steht in Teil 2 nichts,
steht dort „noch nicht erhoben" — nie eine Schätzung.

## Benutzung

```bash
# 1. Kurzbefund — Sekunden, ohne Vorbereitung. Das Akquise-Werkzeug.
python3 cited.py pruefen beispiel.ch
python3 cited.py pruefen beispiel.ch --json > befunde/beispiel.json

# 2. Fragensatz erzeugen und Erhebung anlegen
python3 cited.py fragen \
  --firma "Meier Treuhand AG" --domain meier.ch \
  --branche Treuhandbüro --ort Rapperswil \
  --leistung Buchhaltung --leistung Steuererklärung \
  --datei erhebungen/meier.json

# 3. Antworten erfassen — eine je Aufruf, im Wortlaut
python3 cited.py erfassen --datei erhebungen/meier.json \
  --system ChatGPT --frage 1 --antwort-datei antwort.txt \
  --quelle "https://example.ch"

# 4. Bericht erzeugen
python3 cited.py bericht --datei erhebungen/meier.json \
  --ausgabe berichte/meier.html
```

`--json` funktioniert vor und nach dem Unterbefehl.

## Die neun Prüffelder

| Feld | Gewicht | Warum |
|---|---:|---|
| Lesbarer Inhalt | 6 | Entsteht der Text erst im Browser, ist die Seite für Antwort-Crawler leer. Schwerster Einzelbefund. |
| Crawler-Zugang | 5 | `robots.txt` sperrt Antwortsysteme aus. Häufigster und billigst zu behebender Fehler. |
| Erreichbarkeit | 5 | Ohne erreichbare Seite ist alles andere gegenstandslos. |
| Strukturierte Daten | 4 | Die maschinenlesbare Visitenkarte. Ohne sie muss geraten werden. |
| Fragen auf der Seite | 3 | Antwortsysteme übernehmen Frage-Antwort-Muster bevorzugt. |
| Titel | 2 | Grundlage. |
| llms.txt · Kurzbeschreibung · Sitemap | je 1 | Kleinigkeiten, oft fehlend. |

Punkte sind gewichtete Anteile. **Nicht geprüfte Felder zählen nicht
mit** — ein Zeitlimit darf das Ergebnis nicht schönen und nicht
verschlechtern.

### Antwort-Crawler vs. Trainings-Crawler

Der wichtigste Unterschied im ganzen Werkzeug. Nur Antwort-Crawler
fliessen als Mangel in die Bewertung ein:

| Kennung | Betreiber | Zweck |
|---|---|---|
| OAI-SearchBot, ChatGPT-User | OpenAI | **Antwort** |
| Claude-User, Claude-SearchBot | Anthropic | **Antwort** |
| PerplexityBot, Perplexity-User | Perplexity | **Antwort** |
| Google-Extended | Google | **Antwort** |
| GPTBot, ClaudeBot, CCBot, Bytespider, Applebot-Extended | div. | Training |

Trainings-Crawler zu sperren ist eine legitime Entscheidung und wird
nicht als Mangel gewertet. Antwort-Crawler zu sperren heisst
unsichtbar sein.

## Aufbau

```
netz.py      HTTP. Ehrlicher User-Agent, Zeitlimits, Fehler sind
             Ergebnisse statt Ausnahmen.
technik.py   Die neun Prüfungen. Bekommt die Holfunktion eingespeist,
             deshalb ohne Netz testbar.
fragen.py    Fragensatz, Erhebung, Nennungserkennung.
bericht.py   Der HTML-Bericht für den Kunden. Escapt jeden Fremdtext.
cited.py     Kommandozeile.
```

## Tests

```bash
python3 -m unittest test_cited
```

39 Tests, ohne Netzzugang lauffähig. Geprüfte Fälle unter anderem:
robots-Gruppen und Vorrangregeln, JSON-LD mit `@graph`, Unterarten von
`Organization` (eine sauber ausgezeichnete Zahnarztpraxis darf keinen
Mangel gemeldet bekommen), Nennungserkennung ohne Teiltreffer,
Escaping von Fremdtext im Bericht.

## Grenzen, die man kennen muss

- **Wortzahl als Näherung für JavaScript-Abhängigkeit.** Eine Seite mit
  wenig Text kann auch einfach wenig Text haben. Der Befund nennt die
  Zahl, damit man selbst urteilen kann.
- **Fragen in Überschriften** erkennt nur ein Fragezeichen in einem
  `h2`. Eine Nachrichtenseite mit Fragen als Schlagzeilen besteht diese
  Prüfung, ohne eine FAQ zu haben.
- **Nur die Startseite** wird geprüft. Für ein vollständiges Audit
  gehören die wichtigsten Unterseiten dazu — von Hand, bis das
  automatisiert ist.
- **`robots.txt` wird vereinfacht ausgewertet.** Ausreichend für die
  Frage „ist gesperrt", keine vollständige Standardumsetzung.
