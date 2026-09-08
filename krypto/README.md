# KRYPTO — Analyse- und Papierhandelssystem

**Dieses System stellt keine echten Orders.** Es ist an keinen Broker
angebunden. Der Live-Pfad ist nicht implementiert, und das Freigabetor
(`krypto/handel/tor.py`) wirft in jedem Fall eine Ausnahme. Wer echtes
Geld handeln will, muss diesen Teil bewusst selbst bauen — er ist
absichtlich nicht da.

---

## Was es tut

```
Marktdaten holen → Datenqualität prüfen → Universum filtern
   → Indikatoren → Chance/Risiko bewerten → TRADE / NO TRADE
   → Positionsgrösse aus dem Stop-Abstand → Risikowache
   → Papierdepot buchen → protokollieren
```

Jede Stufe kann NEIN sagen. Keine Stufe rät.

## Schnellstart

```bash
python3 -m krypto.cli health          # läuft die Datenquelle?
python3 -m krypto.cli scan            # was ist überhaupt handelbar?
python3 -m krypto.cli research bitcoin
python3 -m krypto.cli signals
python3 -m krypto.cli paper --trocken # zeigt, was passieren würde
python3 -m krypto.cli backtest bitcoin
python3 -m krypto.tests.test_krypto   # 68 Tests
```

Als Slash-Befehle in Claude Code: `/crypto-status`, `/crypto-health`,
`/crypto-scan`, `/crypto-watchlist`, `/crypto-research`,
`/crypto-signals`, `/crypto-risk`, `/crypto-backtest`, `/crypto-paper`,
`/crypto-positions`, `/crypto-performance`, `/crypto-kill`.

## Aufbau

| Datei | Zuständig für |
|---|---|
| `konfig.py` | alle Zahlen, die über Geld entscheiden, an einer Stelle |
| `daten/quelle.py` | CoinGecko, Puffer, Drosselung, ehrliche Fehler |
| `daten/pruefung.py` | ist diese Zeitreihe rechenbar? |
| `daten/universum.py` | Volumen- und Marktkapitalfilter, Stablecoins raus |
| `analyse/indikatoren.py` | RSI, MACD, EMA/SMA, ATR, Bollinger, Vola, Marken |
| `analyse/bewertung.py` | Chance, Risiko, Entscheid, Stop und Ziel |
| `risiko/groesse.py` | Positionsgrösse aus dem Stop-Abstand |
| `risiko/wache.py` | alle Grenzen, Notbremse, Fehlerzähler |
| `handel/papier.py` | Depot, Orders, Gebühren, Slippage, Historie |
| `handel/tor.py` | die verschlossene Tür zum echten Geld |
| `backtest/motor.py` | Rückrechnung ohne Blick in die Zukunft |
| `betrieb/protokoll.py` | sieben Spuren, mit Schwärzung |
| `cli.py` | Bedienung |

## Risikogrenzen (Vorgaben)

| | |
|---|---|
| Risiko je Trade | 1 % des Kapitals |
| Tagesverlustgrenze | 3 % → Notbremse |
| Max. Drawdown | 15 % → Notbremse |
| Max. Einzelposition | 20 % des Depots |
| Max. Exposure | 60 % |
| Max. Positionen | 5 |
| Max. Trades pro Tag | 6 |
| Stop-Loss | **Pflicht.** Ohne Stop keine Order. |
| Gebühr / Slippage | 0.1 % / 0.05 % je Seite, immer eingerechnet |

Alles per Umgebungsvariable überschreibbar (`KRYPTO_*`, siehe
`konfig.py`). Die Vorgaben sind die vorsichtigen.

## Die drei Regeln, die im Code stehen

1. **Bei Unsicherheit: NO TRADE.** Ein fehlender Indikator ist nie ein
   Argument dafür, nur dagegen.
2. **Ohne Stop keine Order.** Kein Sonderfall, keine Ausnahme.
3. **Was nicht gemessen wurde, wird nicht behauptet.** Fehlende Daten
   erscheinen als `NICHT VERFÜGBAR` oder `NICHT BERECHENBAR`, nie als 0.

## Kein Blick in die Zukunft

Der Backtest entscheidet auf dem **Schluss von Kerze i** — und bekommt
dabei physisch nur `kerzen[0..i]` übergeben. Ausgeführt wird zur
**Eröffnung von Kerze i+1**. Stop und Ziel werden an Hoch und Tief
geprüft, nicht am Schlusskurs; reisst eine Kerze beides, gilt der Stop.

Das ist getestet, nicht nur behauptet
(`test_kein_blick_in_die_zukunft`): zwei Reihen, bis Kerze 150
identisch, danach einmal steil hoch und einmal steil runter. Die
Entscheide bis Kerze 150 müssen exakt gleich sein.

## Was beim Bauen an echten Daten aufgefallen ist

**1. Der Backtest schlägt Kaufen-und-Halten nicht.** BTC, 180 Kerzen,
Stand 08.09.2026:

```
System:            +0.05 %   (8 Trades, Trefferquote 50 %, Gebühren 32.27)
Kaufen und halten: +22.49 %  (nach Kosten)
```

Das ist das wichtigste Ergebnis dieser Arbeit, und es spricht gegen das
System. 8 Trades beweisen nichts — aber sie widerlegen auch nichts.
Wer auf dieser Grundlage echtes Geld einsetzt, tut es ohne Beleg.

**2. Ein Markt ohne Rücksetzer wird nie gekauft.** Steigt ein Kurs
ununterbrochen, bleibt der RSI bei 100 und das System sieht dauerhaft
„überkauft". Es verpasst Parabeln. Bewusst so — wer bei RSI 100 kauft,
kauft die Spitze. Festgehalten in
`test_senkrechter_trend_wird_nicht_gekauft`.

**3. Die Altersgrenze für Daten muss zum Kerzentakt passen.** CoinGecko
liefert bei `days=30` einen 4-Stunden-Takt. Eine feste 1-Stunden-Grenze
verwarf beim ersten echten Lauf jede Reihe als „veraltet", obwohl nichts
fehlte. Jetzt gilt: konfigurierte Grenze als Boden, doppelter Kerzentakt
als Massstab.

**4. Risikopunkte sind keine Vetos.** Anfangs führte jede Risikonotiz zu
NO TRADE — BNB wurde mit Chance 80 und Risiko 34 abgelehnt, allein wegen
eines niedrigen Umschlags, der bei den grössten Werten normal ist. Damit
war der Risiko-Score wirkungslos. Getrennt in `gruende` / `hinweise` /
`blocker`.

## Was NICHT gebaut ist

- **Keine Broker-Anbindung.** Kein Live-Handel, in keiner Form.
- **Keine Nachrichten- und Stimmungsanalyse.** Dafür bräuchte es eine
  bezahlte Quelle. Ein LLM, das Schlagzeilen bewertet, wäre eine
  Meinung mit Zahlenanstrich — das ist nicht dasselbe wie eine Messung.
- **Keine Leerverkäufe.** Long-only.
- **Keine Intraday-Daten.** Die freie CoinGecko-Stufe gibt 4-Stunden-
  Kerzen; kürzer geht nur mit Schlüssel.
- **Keine Optimierung von Parametern.** Absichtlich: Wer Schwellen auf
  180 Kerzen optimiert, optimiert auf Rauschen.
- **Kein Walk-Forward über mehrere Marktphasen.** Die freie Stufe gibt
  historische Tageskurse nur rund 365 Tage zurück.

## Sicherheit

- Es steht **kein einziges Zugangsdatum** in diesem System. Nichts wird
  gelesen, gespeichert oder ausgegeben.
- Jeder Protokolleintrag geht durch eine Schwärzung: Felder wie
  `api_key`, `password`, `token`, `identifier` werden ersetzt; lange
  Zeichenketten und Mailadressen ebenfalls. Geprüft, nicht nur behauptet.
- `logs/` und `zustand/` sind in `.gitignore`.
- Einzige Netzwerkadresse im Code: `https://api.coingecko.com/api/v3`,
  nur lesend.
- Kein `eval`, kein `exec`, kein `pickle`, kein `subprocess`.

## Der Satz zum Schluss

Automatisierung macht die **Ausführung** schneller, nicht die
**Entscheidung** besser. Dieses System kann sauber rechnen, Grenzen
einhalten und ehrlich berichten. Es kann nicht wissen, wohin der Kurs
geht — und der Backtest oben legt nahe, dass es das auch nicht tut.
