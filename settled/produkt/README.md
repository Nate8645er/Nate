# settled — Krypto-Zahlungsabgleich

Beantwortet für einen Onlinehändler drei Fragen, die heute Handarbeit
sind:

1. **Welche Bestellung wurde bezahlt?** — Kettenzahlungen den
   Bestellungen zuordnen.
2. **Stimmt der Betrag?** — unterbezahlt, überbezahlt, offen,
   unerwarteter Eingang.
3. **Was war das in Franken wert?** — Fiatwert am Tag des Eingangs, für
   die Buchhaltung.

## Was es nicht ist

**Kein Handelswerkzeug.** Keine Kursprognosen, keine Signale, keine
Aussage darüber, ob etwas steigt oder fällt. Nichts hier verspricht
Rendite.

**Es bewegt kein Geld.** Es liest ausschliesslich öffentliche
Kettendaten. Es verlangt zu keinem Zeitpunkt einen privaten Schlüssel,
eine Seed Phrase oder einen Börsenzugang. Ein Werkzeug, das nur lesen
kann, kann auch bei einem Fehler nichts verlieren.

**Es ist grösstenteils keine KI.** Kettendaten lesen, Beträge
vergleichen, Kurse nachschlagen — das ist Arithmetik, und das ist gut
so. In der Buchhaltung ist ein Sprachmodell, das manchmal falsch
rechnet, ein Risiko und kein Vorteil.

## Benutzung

```bash
# Was ist abgedeckt?
python3 settled.py ketten

# Eingänge einer Empfangsadresse ansehen
python3 settled.py eingaenge --adresse T... --waehrung USDT-TRC20

# Bestellungen gegen die Kette abgleichen
python3 settled.py abgleich \
  --bestellungen bestellungen.csv \
  --adresse T... --waehrung USDT-TRC20 \
  --fiat chf --csv ergebnis.csv
```

`--json` funktioniert vor und nach dem Unterbefehl.
`--ohne-kurse` läuft ohne Netzzugriff auf die Kursquelle.

### Bestellungen-CSV

Semikolon oder Komma, Kopfzeile Pflicht. Schweizer Zahlenformat
(`1'250.75`) wird gelesen.

```csv
bestellnummer;betrag;waehrung;datum;kunde
2001;100.50;USDT-TRC20;2026-08-24;Muster AG
```

Datum in `YYYY-MM-DD`, `DD.MM.YYYY`, mit oder ohne Uhrzeit, oder als
Unix-Sekunde. **Alles wird als UTC gelesen** — dieselbe Zeitzone wie die
Kettendaten. Zeitzonen zu mischen wäre der schnellste Weg zu falschen
Zuordnungen.

## Abdeckung — geprüft, nicht behauptet

| Schiene | Quelle | Status |
|---|---|---|
| Bitcoin | Blockstream | **geprüft**, gegen die Genesis-Adresse gelesen |
| USDT / USDC (ERC-20) | `eth_getLogs` über rpc.mevblocker.io | **geprüft**, 209 Eingänge in einem 60-Block-Fenster |
| USDT-TRC20 | TronGrid | **geprüft**, echte Eingänge gelesen |
| **natives ETH** | — | **nicht abgedeckt.** Braucht einen kostenpflichtigen Indexer. Wird als Lücke gemeldet, nie als „keine Zahlungen". |

Zur Ethereum-Wahl: `ethereum-rpc.publicnode.com` beantwortet
`eth_blockNumber`, weist `eth_getLogs` aber mit HTTP 403 ab.
`rpc.mevblocker.io` erlaubt es und begrenzt über die Trefferzahl statt
über die Fenstergrösse. Läuft ein Fenster über, halbiert das Werkzeug es
selbst, statt eine Grenze zu raten.

## Bekannte Grenzen

**Kurse älter als rund ein Jahr.** Die freie CoinGecko-Stufe gibt
historische Tageskurse nur für etwa 365 Tage heraus und antwortet
darüber hinaus mit HTTP 401. Betroffene Zeilen werden im Bericht als
**nicht bewertet** ausgewiesen, mit Begründung im Klartext. Für ältere
Zahlungen braucht es eine kostenpflichtige Kursquelle — **das ist eine
Ausgabe und braucht Genehmigung.**

**Tageskurs, nicht Sekundenkurs.** Für die Buchhaltung ist der Tageskurs
die übliche Grundlage. Wer zur Sekunde bewerten muss, braucht eine
andere Quelle.

**Nur bestätigte Zahlungen.** Unbestätigte Transaktionen zählen nicht.

**Eine Adresse je Lauf.** Wer je Bestellung eine eigene Adresse
erzeugt, braucht einen Lauf je Adresse — oder die nächste Ausbaustufe.

## Wie zugeordnet wird

Alle plausiblen Paare bilden, nach Güte sortieren, dann gierig vergeben —
das beste Paar zuerst. Zwei Regeln sind nicht verhandelbar:

1. **Eine Zahlung begleicht höchstens eine Bestellung** und umgekehrt.
   Ohne diese Regel liefert der Händler zweimal.
2. **Was nicht sicher zugeordnet werden kann, bleibt offen.** Eine
   unsichere Zuordnung ist schlimmer als keine, weil sie unbemerkt
   bleibt.

Zeitfenster: 2 Stunden vor bis 14 Tage nach der Bestellung.
Toleranz: 1 % bei Stablecoins, 2 % bei BTC — deckt die Netzgebühr ab,
die der Absender oft abzieht.

## Tests

```bash
python3 -m unittest test_settled
```

27 Tests, ohne Netzzugang lauffähig — die Kettendaten werden
eingespeist. Ein Buchhaltungswerkzeug, das man nur mit Live-Ketten
testen kann, ist nicht testbar.

Zusätzlich end-to-end gegen echte Ketten geprüft: drei Bestellungen
gegen eine reale öffentliche Tron-Adresse, mit echten historischen
Kursen. Ergebnis: bezahlt, unterbezahlt und offen korrekt erkannt, die
nicht bewertbare Zeile mit Begründung ausgewiesen.
