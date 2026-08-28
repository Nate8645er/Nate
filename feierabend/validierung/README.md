# Die Validierung — 6 Wochen, kein Produkt

Die Marktanalyse hat ergeben: Schweizerdeutscher Sprachrapport gibt es
bereits (e-rapport.ch, CHF 12.50 je Mitarbeiter/Monat, inklusive
Rechnungsstellung — an der Quelle geprüft). Ein besseres Produkt zu bauen ist
damit nicht der Engpass. Der Engpass ist die Frage, ob überhaupt jemand
zahlt.

Diese Frage kostet sechs Wochen. Sie zu umgehen kostet zwölf Monate.

## Das Abbruchkriterium

> **20 Gespräche. Davon 3 Vorauszahlungen à CHF 500 für 12 Monate Nutzung.
> Frist: 6 Wochen.**

Kommen die drei nicht zusammen, ist das Projekt beendet. Nicht „das Produkt
noch besser machen". Beendet.

Schreib dir das Datum jetzt auf, bevor du anfängst. Ein Abbruchkriterium, das
man im Nachhinein festlegt, hat noch nie jemanden gestoppt.

## Der Frühindikator

Trag jede Woche zwei Zahlen ein: **Verkaufsstunden** und
**Entwicklungsstunden**, getrennt.

Liegen die Verkaufsstunden drei Wochen in Folge unter zehn, wiederholt sich
der Shopify-Verlauf — dort wurde vier Monate lang gebaut und nie verkauft.
Das ist der Frühindikator, und er schlägt an, lange bevor die sechs Wochen um
sind.

## Wie du an die Gespräche kommst

**Der Abholmarkt, 6:45 Uhr.** Debrunner Acifer, Sanitas Troesch, regionale
Maler- und Sanitärgrosshändler. Dort steht die Zielgruppe, wartet und ist
gesprächsbereit. Drei Morgen pro Woche, acht Gespräche pro Morgen. Unangenehm
— deshalb macht es kaum jemand, und deshalb funktioniert es.

**Türgespräche 16:30–17:30**, wenn die Busse zurück sind. Rapperswil-Jona,
Jona, Eschenbach, Uznach, Schmerikon, Lachen, Pfäffikon SZ.

**Gewerbe Rapperswil-Jona** (gwrj.ch), Mitgliederverzeichnis öffentlich.
Mitglied werden, an drei Anlässen erscheinen, nichts verkaufen, nur zuhören.

Was nicht funktioniert: Kaltakquise per Mail, LinkedIn, Inhalte schreiben.
Die Zielgruppe ist dort nicht, und du lernst dabei nicht verkaufen.

## Der Einstieg, 30 Sekunden, auswendig

> „Grüezi, ich bin Nate aus Jona. Ich baue etwas für Handwerksbetriebe und
> will nichts verkaufen — ich habe eine einzige Frage: Wie kommen bei Ihnen
> die Stunden von der Baustelle ins Büro? … Und wie lange sitzen Sie dafür
> abends noch dran? … Darf ich Ihnen in zwei Wochen zeigen, was ich gebaut
> habe? Kostet Sie zehn Minuten, und wenn es Seich ist, sagen Sie es mir
> direkt."

Die zweite Frage ist die wichtige. Wer „eine halbe Stunde" sagt, hat kein
Problem. Wer seufzt, ist dein Kunde.

## Die Nachricht danach

> „Grüezi Herr [Name], Nate von vorhin beim [Ort]. Wie besprochen: Sie
> schicken mir eine Sprachnachricht wie Sie sie normal reden, ich schicke
> Ihnen in 2 Minuten den fertigen Rapport zurück. Kostet nichts, keine
> Anmeldung. Probieren Sie es einmal — wenn es nichts taugt, haben Sie 30
> Sekunden verloren."

## Das Werkzeug

```
python3 rapport_cli.py
```

Du hörst die Sprachnachricht an, tippst die Felder ein, kopierst den
formatierten Rapport und schickst ihn zurück. Zwei Minuten Arbeit.

Der Handwerker merkt nicht, dass du von Hand arbeitest. Du dagegen lernst bei
jedem Rapport genau, wo eine spätere Automatik scheitern würde — und
sammelst nebenbei das Material für den Schweizerdeutsch-Vorversuch.

Keine Abhängigkeiten, kein Netz, kein API-Schlüssel. Absicht: Es soll heute
laufen, nicht nach einem Setup.

**`rapporte.jsonl` ist per `.gitignore` ausgeschlossen** und muss es bleiben —
darin stehen Namen von Endkunden, die davon nichts wissen. Genau die Daten,
um die es im Datenschutzteil der Spec geht.

## Was du beim Preis sagst

Nicht CHF 500 als Preis nennen, sondern als Vorauszahlung für ein Jahr
Nutzung zum Vorzugspreis. Wer zahlt, ist Referenzkunde und bestimmt mit, was
gebaut wird.

Wenn jemand fragt, was es später kostet: CHF 12 je Mitarbeiter und Monat,
mindestens CHF 49 je Betrieb. Das liegt knapp unter e-rapport — und du musst
wissen, dass e-rapport für diesen Preis mehr liefert. Wer danach fragt,
bekommt diese Antwort ehrlich. Ein Kunde, der unter falschen Annahmen kauft,
kündigt im dritten Monat.

## Woran du nach sechs Wochen misst

| Kennzahl | Zielwert |
|---|---|
| Erstgespräche | 20 |
| Betriebe, die eine Sprachnachricht schicken | 8 |
| **Vorauszahlungen à CHF 500** | **3** |
| Verkaufsstunden pro Woche | mindestens 10 von 25 |

Die dritte Zeile entscheidet. Die anderen erklären nur, warum.
