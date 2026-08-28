# Feierabend — der Dienst

Arbeitsrapporte per Sprache erfassen, direkt nach bexio.

## In fünf Minuten lokal starten

```bash
cd feierabend/app
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python3 einrichten.py "Malerei Huber" Nate Kevin
uvicorn main:app --reload
```

`einrichten.py` gibt für jeden Mitarbeiter einen sechsstelligen Zugangscode
aus. Der Code ist der ganze Login — kein Passwort, kein Konto, keine
E-Mail-Bestätigung. Am Telefon durchgeben und fertig; die Zeichen 0/O und
1/I/L kommen deshalb nicht vor.

Dann `http://localhost:8000` auf dem Handy öffnen, Code eingeben, sprechen.

## Wie die Daten fliessen

```
Handy  ──[Web Speech API]──►  Text
                                │        Audio bleibt auf dem Gerät
                                ▼
                          Pseudonymisierung          lokal, im Dienst
                                │
                          Sicherheitsnetz: noch ein Klarname drin?
                                │  ja → Abbruch, nichts geht raus
                                ▼
                          Sprachmodell               sieht nur KUNDE_7
                                │
                                ▼
                          Entwurf → Handwerker bestätigt → gespeichert
```

Die Spracherkennung läuft **im Browser**. Es gibt keinen
Transkriptionsdienstleister, keine Audiodatei auf dem Server, keine
Minutenabrechnung — und die heikelste Datenklasse (Stimme, Nebengeräusche,
Stimmen Dritter im Raum) entsteht bei uns gar nicht.

## Umgebungsvariablen

| Variable | Pflicht | Zweck |
|---|---|---|
| `ANTHROPIC_API_KEY` | ja | Ohne ihn kein Rapport-Entwurf |
| `FEIERABEND_URL` | für bexio | Öffentliche Adresse, sonst schlägt der Rückruf fehl |
| `FEIERABEND_DB` | nein | Pfad zur SQLite-Datei |
| `BEXIO_CLIENT_ID` / `_SECRET` | für bexio | Aus einer bexio-Anwendung |

## bexio verbinden

Einmalig pro Betrieb, mit einem gültigen Zugangscode:

```
<URL>/bexio/verbinden?code=<CODE>
```

Danach werden die bexio-Kontakte als Kundenstamm übernommen — den braucht
die Pseudonymisierung, sonst kann sie keine Namen erkennen.

**Ehrlich zum Stand:** OAuth-Ablauf und Zeiteintrag sind nach der
bexio-Dokumentation gebaut, aber **nicht gegen die echte API getestet** —
dafür braucht es eine registrierte bexio-Anwendung. Die Feldnamen im
Zeiteintrag sind der wahrscheinlichste Punkt, an dem beim ersten echten
Aufruf nachjustiert werden muss.

## Bewusste Entscheidungen

**Nie raten.** Fehlt Kunde oder Stundenzahl, kommt eine Rückfrage statt
eines Eintrags. Unplausible Werte (26 Stunden an einem Tag) und
halluzinierte Kunden werden verworfen. Ein still falsch gespeicherter
Rapport ist schlimmer als gar keiner — er wird verrechnet.

**Auswertung nach Auftrag, nicht nach Person.** Art. 328b OR erlaubt
Datenbearbeitung nur mit Bezug zur Vertragserfüllung, Art. 26 ArGV 3
verbietet Überwachungssysteme zur Verhaltenskontrolle. Eine Rangliste
„Stunden je Mitarbeiter" kippt dorthin. Die Zuordnung bleibt im
Einzelrapport, wo sie zur Abrechnung nötig ist.

**Kein Werkzeugaufruf am Modell.** Der Text stammt aus einer
Spracherkennung und ist nicht vertrauenswürdig. Ein Modell ohne Werkzeuge
kann durch eingeschleuste Anweisungen höchstens schlechte Daten liefern,
niemals Aktionen auslösen.

**Keine Selbstregistrierung.** Die ersten Kunden werden von Hand
aufgeschaltet, während du mit ihnen sprichst.

## Tests

```bash
cd feierabend/tests && python3 -m unittest discover
```

114 Tests, davon die wichtigsten zur Mandantentrennung: Ein Betrieb darf
die Rapporte, Kunden und Auswertungen eines anderen unter keinen Umständen
sehen.

## Was noch fehlt

- **Zahlungsabwicklung.** Die ersten Kunden werden von Hand fakturiert.
- **PostgreSQL.** SQLite trägt die ersten Betriebe; jede Abfrage führt
  bereits die Mandanten-ID mit, der Wechsel ist eine Frage der
  Verbindungszeile.
- **bexio gegen die echte API geprüft.**
- **Löschfristen automatisiert.** Rapporte unterliegen der Zehnjahresfrist
  nach Art. 958f OR, sobald sie einer Rechnung zugrunde liegen.
