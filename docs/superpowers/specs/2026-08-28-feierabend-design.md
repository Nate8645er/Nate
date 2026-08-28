# Feierabend — Arbeitsrapporte per Sprachnachricht

**Datum:** 2026-08-28
**Status:** Entwurf, wartet auf Validierung
**Autor:** Nate, mit Claude Code

---

## Das Problem

Ein Handwerker verlässt um 17 Uhr die Baustelle. Was er heute gemacht hat —
bei welchem Kunden, wie lange, mit welchem Material — steht nirgends. Es steht
in seinem Kopf, und der leert sich.

Abends am Küchentisch rekonstruiert er es aus dem Gedächtnis, oder er lässt es.
Nicht rapportierte Stunden werden nicht verrechnet. Das ist kein
Verwaltungsärgernis, das ist direkter Umsatzverlust.

Die vorhandenen Branchenlösungen setzen später an: Sie rechnen ab, was man
ihnen eingibt. Der Verlust entsteht davor — **im Moment der Erfassung.**

## Die Lösung

Der Handwerker schickt eine WhatsApp-Sprachnachricht, so wie er es ohnehin den
ganzen Tag tut:

> „Fertig bei Familie Meier in Jona, drei Stunden, zwei Liter Grundierung und
> eine Rolle Abdeckband. Nächste Woche nochmals hin für die zweite Schicht."

Daraus entsteht ein strukturierter Rapport: Kunde, Datum, Stunden, Tätigkeiten,
Material, Folgetermin. Am Freitag kommt die Wochenauswertung per Mail.

Keine App. Kein Login. Keine neue Gewohnheit.

## Die Wette

Alles hängt an einem Satz: **Sprache muss hier die beste Schnittstelle sein,
nicht nur eine mögliche.**

Für Büroarbeit ist Sprache schlechter als Tippen. Für jemanden auf der Leiter,
im Lieferwagen, mit Farbe an den Händen, ist Tippen keine Option. Handwerk ist
einer der wenigen Märkte, in denen Sprachsteuerung kein Gimmick ist.

Wenn diese Wette falsch ist, ist das Produkt falsch.

## Bewusste Nicht-Ziele

Wir bauen **keine** Branchensoftware. Wir bauen die Erfassungsschicht davor.

Nicht im Umfang:

- Rechnungsstellung — das können Bexio und Vertec besser
- Zeiterfassung mit Stempeluhr-Logik
- Offerten, Mahnwesen, Buchhaltung
- Eine mobile App
- Ein Web-Dashboard in Version 1 (die Wochenmail ersetzt es)
- Eine Abrechnungsautomatik in Version 1 (die ersten Kunden werden von Hand
  fakturiert)

Jeder dieser Punkte ist eine Einladung, nie fertig zu werden.

---

## Architektur

```
WhatsApp-Sprachnachricht
        │
        ▼
[1] Eingang         Webhook, HMAC-Signatur prüfen, Audio laden,
        │           danach aktiv bei Meta löschen (DELETE-Endpoint)
        ▼
[2] Transkription   Audio → Text (Schweizerdeutsch!)
        │           Audio verlässt nie den Arbeitsspeicher
        ▼
[3] Pseudonymisierung   Kundennamen → Token (KUNDE_7)
        │               lokal, gegen den Kundenstamm des Betriebs
        ▼
[4] Extraktion      Claude → strukturierter Rapport
        │           sieht nur pseudonymisierten Text
        ├─ unklar? ──► [5] Rückfrage per WhatsApp ──┐
        │                                            │
        ▼◄───────────────────────────────────────────┘
[6] Bestätigung     Handwerker sieht und bestätigt den Rapport
        │
        ▼
[7] Speicher        PostgreSQL, Row Level Security je Mandant
        │           Rohtranskript wird nach Bestätigung gelöscht
        ▼
[8] Ausgabe         Wochen-PDF per Mail · CSV · später Bexio-API
```

Die Pseudonymisierung in Schritt 3 ist der wichtigste Baustein: Kundennamen
und Adressen verlassen dadurch nie die eigene Infrastruktur. Das Sprachmodell
sieht `KUNDE_7`, nicht „Familie Meier in Jona".

### Die Einheiten

Jede ist einzeln testbar und hat einen Zweck:

| Einheit | Aufgabe | Abhängigkeiten |
|---|---|---|
| `ingest` | Webhook annehmen, Signatur prüfen, Audio holen | Meta Cloud API |
| `transcribe` | Audio → Rohtext | Speech-to-Text-Dienst |
| `extract` | Rohtext → strukturierter Rapport | Anthropic API |
| `clarify` | Fehlende Pflichtfelder erfragen | `ingest` (Rückkanal) |
| `store` | Rapporte je Mandant ablegen | PostgreSQL |
| `report` | Wochenauswertung erzeugen und versenden | `store`, Mailversand |

Die Schnittstelle zwischen `transcribe` und `extract` ist reiner Text. Die
zwischen `extract` und `store` ist ein validiertes Rapport-Objekt. Beide
Dienste sind dadurch austauschbar, ohne den Rest anzufassen.

### Identität ohne Login

**Die Telefonnummer ist das Konto.** WhatsApp liefert die Absendernummer
mitgeliefert und verifiziert — es braucht keine Registrierung, kein Passwort,
keine Passwort-vergessen-Strecke.

- Eine Nummer gehört zu genau einem Betrieb (Mandant).
- Ein Betrieb hat mehrere Nummern (Mitarbeiter).
- Eine unbekannte Nummer bekommt eine freundliche Absage, keinen Zugang.

Das ist die eleganteste Eigenschaft des Entwurfs und ergibt sich geschenkt aus
der Kanalwahl.

### Mandantentrennung von Tag eins

Aus `javier-mobile` gelernt: Ein System, das für eine Person gebaut ist, lässt
sich nicht nachträglich für viele öffnen. Jede Abfrage trägt die Mandanten-ID,
und zwar erzwungen auf Datenbankebene, nicht per Konvention im Anwendungscode.

---

## Das grösste technische Risiko: Schweizerdeutsch

Ein Maler aus dem Toggenburg spricht keine Hochsprache. Er sagt „zwöi Liter
Grundierig" und „am Zieschtig no einisch ane".

Gängige Transkriptionsmodelle sind auf Schweizerdeutsch deutlich schwächer als
auf Hochdeutsch. **Das ist die Stelle, an der dieses Produkt scheitert oder
funktioniert** — nicht die Architektur, nicht das Design.

**Die entschärfende Einsicht:** Wir brauchen keine perfekte Transkription. Wir
brauchen korrekte Felder. Die Extraktionsschicht bekommt den Rohtext samt
Fehlern und muss daraus `{Kunde, Stunden, Material}` gewinnen. Ein
Sprachmodell mit Kontext — den Kundenstamm des Betriebs, die üblichen
Materialien — verkraftet erheblichen Transkriptionsschrott.

Das senkt die Anforderung von „versteht Dialekt perfekt" auf „erkennt genug
Stützpunkte". Ob das reicht, ist eine empirische Frage.

**Sie wird zuerst beantwortet, vor allem anderen.** Details unter
Umsetzungsreihenfolge.

---

## Umgang mit Fehlern

Sprachnachrichten sind unvollständig, nicht falsch. Die Regel lautet: **nie
raten, immer nachfragen.**

| Fall | Verhalten |
|---|---|
| Stunden fehlen | Rückfrage per WhatsApp: „Wie lange warst du bei Meier?" |
| Kunde unbekannt | Rückfrage mit den drei ähnlichsten Namen aus dem Stamm |
| Transkription unbrauchbar | Ehrliche Antwort: „Ich habe dich nicht verstanden, nochmals bitte" |
| Material unklar | Als Freitext übernehmen, nicht erzwingen |
| Dienst nicht erreichbar | Nachricht in Warteschlange, später verarbeiten, Nutzer informieren |

Ein halb verstandener Rapport, der still falsch gespeichert wird, ist
schlimmer als gar keiner — er zerstört das Vertrauen in alle anderen.

---

## Recht und Datenschutz — die eigentliche Architekturvorgabe

Ein Satz bestimmt dieses Produkt: **Es sammelt systematisch Gesundheitsdaten
abwesender Dritter ein, die davon nichts wissen.**

Das ist kein Ausnahmefall, sondern Normalbetrieb. „Behindertengerechter
Duschumbau, der Herr sitzt im Rollstuhl" ist ein alltäglicher Handwerkersatz —
und ein besonders schützenswertes Datum nach Art. 5 lit. c Ziff. 2 DSG. Ebenso
Treppenlift, Pflegebett, Allergiker-Farben.

Zur Klarstellung: Zahlungsmoral ist **nicht** besonders schützenswert; die
Liste in Art. 5 DSG ist abschliessend. Gesundheit ist es eindeutig.

### Rollen

Der Handwerksbetrieb ist Verantwortlicher, wir sind Auftragsbearbeiter
(Art. 9 DSG). Das muss so bleiben: Sobald wir Transkripte für
Modellverbesserung oder produktübergreifende Statistik nutzen, werden wir
für diesen Teil selbst Verantwortlicher. **Wir tun das nicht.**

### Vier Aufbewahrungsklassen

Das ist die Kernarchitektur, nicht eine Fussnote:

| Klasse | Frist | Begründung |
|---|---|---|
| Audio | Sekunden, nie persistent | Zweck mit Transkription erfüllt |
| Rohtranskript | bis Bestätigung, max. 30 Tage | enthält allen Beiwortlaut über Dritte |
| Strukturierter Rapport | **10 Jahre** | Art. 958f OR, Buchungsbeleg |
| Kontodaten | Vertragsdauer plus Frist | im AVV geregelt |

**Der Widerspruch ist beabsichtigt und wichtig.** Verlangt ein Endkunde
Löschung, muss der Betrieb sie für den Rapport **verweigern** — die
gesetzliche Aufbewahrungspflicht geht vor. Eine Datenschutzerklärung, die
pauschal „Löschung auf Verlangen" verspricht, ist eine unzutreffende
Information nach Art. 19 DSG und nach Art. 60 DSG strafbewehrt. Die Klassen
werden im Text differenziert, nicht verschwiegen.

### Datenflüsse über die Grenze

- **Claude über AWS Bedrock oder Google Vertex in EU-Region**, nicht über die
  direkte API. Die Daten verlassen den EU/CH-Raum dann gar nicht erst.
- **Transkription selbst gehostet** in der Schweiz oder EU. Das eliminiert
  einen Auftragsbearbeiter und eine Grenzüberschreitung vollständig — bei
  Gesundheitsdaten Dritter ist das den Betriebsaufwand wert.
- **Pseudonymisierung vor jedem Modellaufruf** (Schritt 3 der Architektur).
- Häufig vergessen und ebenso zu prüfen: Backups, Fehlerprotokollierung,
  Mailversand der Wochenauswertung, Support-System.

**Zur Verschlüsselung ehrlich:** Bei der WhatsApp Cloud API endet die
Ende-zu-Ende-Verschlüsselung bei Meta. Die Sprachnachricht wird dort
entschlüsselt und zwischengespeichert. „WhatsApp ist verschlüsselt" ist als
Verkaufsargument in dieser Konstellation falsch und wird nicht verwendet.

### Was wir bewusst nie bauen

**Keine Sprechererkennung.** Sie ist verlockend („das System erkennt, wer
spricht") und würde eindeutig biometrische Daten im Rechtssinn erzeugen. Bei
Arbeitnehmern ist die Einwilligung wegen des Machtgefälles regelmässig
unwirksam — es gäbe dann keine tragfähige Rechtsgrundlage. Die Absendernummer
plus expliziter Enrollment-Schritt leistet dasselbe ohne Biometrie.

### Arbeitsrecht — das unterschätzte Risiko

Art. 328b OR erlaubt Datenbearbeitung nur mit Bezug zur Vertragserfüllung.
Art. 26 ArGV 3 verbietet Überwachungssysteme zur Verhaltenskontrolle. Eine
Auswertung „Stunden pro Mitarbeiter im Vergleich" kippt genau dorthin — und
das ist ausgerechnet das naheliegendste Feature.

Konsequenz für den Entwurf: Die Wochenauswertung ist **auftrags- und
projektbezogen**, nicht personenbezogen rangiert. Kein Standort-Tracking.
Mitarbeiterinformation ist Pflichtbestandteil des Onboardings.

### Strafrecht

Art. 179ter StGB: Nimmt der Handwerker beim Kunden auf, während dieser
mitspricht, ist das unbefugtes Aufnehmen eines Gesprächs. Täter ist der
Nutzer, Werkzeug ist unser Produkt.

Gegenmassnahme: Push-to-Talk statt Daueraufnahme (WhatsApp erfüllt das
bereits), plus ausdrückliche Onboarding-Regel — **Rapport allein diktieren,
nicht im Beisein der Kundschaft.**

### Pflichtdokumente vor dem ersten zahlenden Kunden

Datenschutz-Folgenabschätzung (Art. 22 DSG, hier voraussichtlich zwingend),
Bearbeitungsverzeichnis (Art. 12 — die KMU-Ausnahme greift bei besonders
schützenswerten Daten nicht), Auftragsbearbeitungsverträge, Liste der
Unterauftragsbearbeiter, Vorfall-Playbook, und ein Textbaustein-Kit, mit dem
der Betrieb seine eigene Informationspflicht gegenüber seinen Kunden erfüllt.

**Zur Haftung:** Art. 61 ff. DSG sieht Bussen bis CHF 250'000 vor — gegen die
**verantwortliche natürliche Person**, nicht die Firma. Bei einem
Einzelgründer trifft das dich persönlich.

---

## Technik

Bewusst langweilig und nah an dem, was Nate bereits beherrscht:

| Baustein | Wahl | Begründung |
|---|---|---|
| Backend | Python + FastAPI | Aus `javier-mobile` erprobt |
| Datenbank | PostgreSQL mit Row Level Security | Mandantentrennung erzwungen, nicht per Konvention |
| Extraktion | Claude über Bedrock/Vertex, EU-Region | Daten bleiben im EU/CH-Raum |
| Transkription | selbst gehostet, CH/EU — Modell offen | Vorversuch entscheidet; ein Auftragsbearbeiter weniger |
| Kanal | WhatsApp Cloud API | Die Gewohnheit existiert bereits |
| Hosting | EU/CH-Region | Datenschutz |
| Tests | pytest | Ab der ersten Zeile, nicht nachträglich |

### Nicht verhandelbare Sicherheitsanforderungen

Aus der Analyse, jede mit einem konkreten Fehler dahinter, der real passiert:

- **Webhook-HMAC prüfen** (`X-Hub-Signature-256`) über den **Rohbody**, vor
  jeder Deserialisierung, mit `hmac.compare_digest`. Sonst schreibt jeder mit
  der URL Rapporte in beliebige Mandanten.
- **Row Level Security** in der Datenbank, plus ein Integrationstest, der
  belegt, dass ein mandantenübergreifender Zugriff null Zeilen liefert. Der
  klassische Multi-Tenant-Bruch ist ein vergessener Filter.
- **Fehlendes Secret ist ein Startfehler**, keine Freigabe. In
  `javier-mobile` ist genau das falsch herum gebaut (`server.py:75`).
- **Absendernummer ist kein Authentifizierungsmerkmal** (SIM-Swap). Nur
  explizit eingetragene Nummern werden angenommen.
- **Nie Inhalte protokollieren** — keine Transkripte, keine Prompts. Sonst
  landen Gesundheitsdaten Schweizer Endkunden im Log-Werkzeug eines
  US-Anbieters.
- **Ratenbegrenzung** auf dem Webhook, sonst brennt ein Angreifer das
  Transkriptions- und Modellbudget ab.
- **CSV-Formel-Injection** beim Excel-Export neutralisieren. Bei einem
  Produkt, dessen Kernnutzen der Export ist, nicht theoretisch.
- **Abhängigkeiten gepinnt**, Lockfile, `pip-audit` in der CI.

Aus `javier-mobile` wandert Wissen mit, kein Code: der Agent-Loop, die
Whitelist-Denkweise bei gefährlichen Aktionen, die Disziplin, Grenzen ehrlich
zu benennen statt sie zu kaschieren — und die dort gefundenen Fehler als
Negativbeispiele.

---

## Umsetzungsreihenfolge

**Schritt 0 — Vorversuch Schweizerdeutsch (2 Tage).**
Zwanzig echte Sprachnachrichten auf Schweizerdeutsch, quer durch Dialekte und
Umgebungslärm. Durch zwei bis drei Transkriptionsdienste, danach durch die
Extraktion. Gemessen wird nicht die Wortgenauigkeit, sondern: **Wie viele
Rapporte haben korrekte Felder?**

*Abbruchkriterium: Unter 70 % korrekt extrahierte Rapporte — dann ist der
Ansatz in dieser Form tot und wir überdenken den Kanal.*

**Schritt 1 — Zehn Gespräche.**
Mit echten Handwerksbetrieben in der Region. Nicht das Produkt zeigen, sondern
fragen, wie sie heute rapportieren und was sie das kostet. Wer nach dem
Gespräch von sich aus fragt, wann er es haben kann, ist der erste Testkunde.

**Schritt 2 — Dünner Durchstich.**
Ein Betrieb, eine Nummer, Sprachnachricht bis Wochen-PDF. Alles andere von
Hand. Ziel ist nicht Vollständigkeit, sondern ein echter Rapport eines echten
Handwerkers.

**Schritt 3 — Verbreitern.**
Erst wenn Schritt 2 einen zufriedenen Nutzer hat: Mehrmandantenfähigkeit
härten, Rückfragedialog, Kundenstamm, Materialkatalog.

**Schritt 4 — Kassieren.**
Abrechnung. Bewusst zuletzt: Die ersten zehn Kunden werden von Hand
fakturiert. Eine Abrechnungsautomatik für null Kunden zu bauen ist die
teuerste Art, beschäftigt auszusehen.

---

## Woran wir Erfolg messen

- **Schritt 0:** über 70 % korrekt extrahierte Rapporte aus echtem Dialekt
- **Schritt 1:** mindestens drei Betriebe fragen von sich aus nach dem Produkt
- **Schritt 2:** ein Handwerker nutzt es zwei Wochen freiwillig weiter
- **Schritt 3:** fünf Betriebe aktiv
- **Schritt 4:** CHF 1'000 wiederkehrender Monatsumsatz

Die ersten beiden Zahlen entscheiden, ob die übrigen je erreichbar sind.

---

## Offene Punkte

1. **Markenrecherche** für „Feierabend" beim IGE — vor jeder Ausgabe.
2. **Marktanalyse und Preis** — steht aus. Der erste Anlauf brach wegen eines
   API-Limits ab; es liegen **keine** Marktdaten vor. Nichts in diesem
   Dokument behauptet, wie gross der Markt ist oder was er zahlt.
3. **Transkriptionsmodell** — wird durch Schritt 0 entschieden, nicht vorher.

### Anwaltlich zu klären, vor dem ersten zahlenden Kunden

Nicht raten, wo Fachwissen nötig ist:

1. Gilt die Stimmaufnahme nach Art. 5 lit. c Ziff. 4 DSG bereits als
   biometrisches Datum? In der Schweizer Lehre umstritten.
2. Ab wann greift die DSGVO? Sie hängt an der tatsächlichen Kundenbasis —
   Hosting in der EU allein begründet **keine** Niederlassung.
3. Metas Rolle für Inhalte und Metadaten der Cloud API, und ob regionale
   Datenhaltung für die Schweiz verfügbar ist.
4. Zulässigkeit der Wochenauswertung nach Art. 328b OR und Art. 26 ArGV 3 —
   eigene Rechtsmaterie, eigener Spezialist.
5. Tragweite von Art. 179ter/179quater StGB bei Aufnahmen vor Ort.
6. Ob der Rapport als Buchungsbeleg unter die Zehnjahresfrist nach
   Art. 958f OR fällt — mit dem Treuhänder.
7. Ob die Datenschutz-Folgenabschätzung nach Art. 22 DSG zwingend ist.
   Einschätzung: ja. Sie wird unabhängig vom Ergebnis erstellt.

### Sofort zu behebende Fehler in `javier-mobile`

Gefunden bei der Analyse, unabhängig vom neuen Produkt relevant, weil der
Prototyp bei Render deployt ist:

- `server.py:75` — **fail-open**: Ohne gesetztes `JAVIER_PASSWORD` entfällt
  die Prüfung komplett. `render.yaml:15` setzt die Variable auf
  `sync: false`, muss also manuell gesetzt werden. Wird sie vergessen, steht
  ein offener Endpunkt mit gültigem Anthropic-Key im Netz.
- `server.py:75` — Secret-Vergleich mit `!=` statt `hmac.compare_digest`.
- `server.py:85` — keine Ratenbegrenzung, bis zu acht Agent-Durchläufe pro
  Anfrage.
- `requirements.txt` — sechs Abhängigkeiten, keine gepinnt; jedes Deployment
  kann anderen Code ziehen.

Keine Befunde bei: Secrets in der Git-Historie, `contacts.json` (nur
Platzhalter), CORS, Pfad-Traversal.
