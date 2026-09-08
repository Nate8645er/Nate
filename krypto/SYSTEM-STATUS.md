# SYSTEM STATUS — KRYPTO

Stand 08.09.2026. Jede Zeile ist entweder mit einem ausgeführten Befehl
belegt oder ausdrücklich als **NICHT VERIFIZIERT** markiert. Nichts
dazwischen.

---

## Zusammenfassung

| | |
|---|---|
| **LIVE TRADING** | **AUS.** `LIVE_TRADING_ENABLED=false`, nirgends im Code auf true gesetzt (grep-geprüft) |
| **Broker-Anbindung** | **NICHT VORHANDEN** — bewusst nicht gebaut |
| **Echte Orders gestellt** | **null** |
| **Echtes Geld bewegt** | **CHF 0.00** |
| **Kosten entstanden** | **CHF 0.00** |
| Papierdepot | 10 000.00 USD, Startzustand |
| Module | 22 Python-Dateien, 2 818 Zeilen |
| Tests | **68, alle grün** (`python3 -m krypto.tests.test_krypto`) |

---

## VERIFIZIERT — mit echtem Befehl belegt

| Baustein | Nachweis |
|---|---|
| Datenquelle CoinGecko | `/ping` → 200; `/coins/markets` → 200, 25 Werte; `/coins/bitcoin/ohlc?days=30` → 200, 180 Kerzen |
| `health` | `GESAMT OK` |
| Datenprüfung | 180 BTC-Kerzen → „Daten tauglich" |
| Marktscan | 25 geprüft → 16 zugelassen, 9 abgelehnt (Stablecoins, verpackte Abbilder, Liquiditätsgrenze) |
| Recherche | BTC 78 892 USD, RSI 44.0, ATR 0.81 %, Regime ruhig → NO TRADE (Chance 0) |
| Signale | 5 Werte → 3 × TRADE (ETH, BNB, SOL), 2 × NO TRADE |
| Positionsgrösse | ETH: 0.810143 zu 2 468.70 = 2 000.00 = exakt der 20-%-Deckel |
| Papierhandel | 2 Positionen eröffnet, Depot 9 996.00 (Differenz = Gebühren) |
| Stop/Ziel gesetzt | ETH Stop 2 413.35 / Ziel 2 551.73 — aus ATR, nicht geraten |
| Risikoanzeige | Exposure 40.03 % von 60 %, Drawdown 0.04 % von 15 %, 2/5 Positionen, 2/6 Trades |
| Notbremse | gezogen → ETH und BNB `ABGELEHNT: Notbremse gezogen`; gelöst → wieder handelbar |
| Notbremse überlebt Neustart | liegt als Datei in `zustand/`, Test `test_notbremse_ueberlebt_neustart` |
| Live-Tor | `tor.freigeben()` wirft `LiveGesperrt`, auch mit `bestaetigung_mensch=True` |
| Kein Blick in die Zukunft | `test_kein_blick_in_die_zukunft` — identische Entscheide bis zum Verzweigungspunkt |
| Protokoll-Schwärzung | Testeintrag mit API-Key, Passwort, Mail und Token → alles `<GESCHWAERZT>`; grep über `logs/` findet keinen Klartext |
| Backtest | BTC 180 Kerzen: +0.05 %, 8 Trades, Trefferquote 50 %, Profitfaktor 1.03, Max. DD 1.65 %, Sharpe 0.02 |

## NICHT VERIFIZIERT / NICHT VORHANDEN

| Punkt | Stand |
|---|---|
| Live-Handel | **nicht implementiert.** Keine Order-Ausführung existiert. |
| Capital.com-Verbindung | MCP-Server läuft (38 Werkzeuge, `√ Connected`), aber **nur Platzhalter-Zugangsdaten**. Es wurde **nie** eine Sitzung aufgebaut. |
| Nachrichten / Sentiment | **nicht gebaut** — braucht bezahlte Quelle |
| Leerverkäufe | nicht unterstützt |
| Intraday unter 4 h | freie CoinGecko-Stufe gibt das nicht her |
| Walk-Forward über Marktphasen | historische Tageskurse nur ~365 Tage → **nicht möglich ohne bezahlte Quelle** |
| Aussage über Profitabilität | **keine.** 8 Trades sind statistisch nichts. |

---

## Das unbequeme Ergebnis

```
System:            +0.05 %
Kaufen und halten: +22.49 %   (nach Kosten)
```

Über die verfügbaren 180 BTC-Kerzen war das System **deutlich
schlechter** als einfach kaufen und liegenlassen. Das ist kein Fehler im
Code — es ist das Messergebnis. Drei mögliche Lesarten, ehrlich
nebeneinander:

1. Der Zeitraum war ein Aufwärtsmarkt; ein System mit Stops und
   Teilzeiten am Markt verliert dort strukturell gegen Halten.
2. 8 Trades sind zu wenig für jede Aussage.
3. Das Modell taugt nichts.

**Ich kann zwischen den dreien nicht unterscheiden**, weil die freie
Datenquelle keinen längeren Zeitraum hergibt. Wer das entscheiden will,
braucht mehrjährige Kursdaten — und damit eine bezahlte Quelle. Das ist
eine Ausgabe und damit deine Entscheidung, nicht meine.

---

## Was du tun musst, damit mehr geht

| Wenn du willst … | brauchst du … | Kosten |
|---|---|---|
| Aussagekräftigen Backtest | mehrjährige OHLC-Daten (CoinGecko Pro o. ä.) | kostenpflichtig |
| Kürzere Kerzen | API-Schlüssel | kostenpflichtig |
| Echten Handel | Broker-Konto **und** den Live-Pfad, den ich bewusst nicht gebaut habe | Risiko, kein Preis |

Für Capital.com wären das genau drei Umgebungsvariablen —
`CAP_API_KEY`, `CAP_IDENTIFIER`, `CAP_API_PASSWORD` —, sie gehören in
`~/.config/capital-mcp/.env` und **nicht in einen Chat**. Solange
`CAP_DRY_RUN=true` und `CAP_ALLOW_TRADING=false` gesetzt sind, kann auch
damit nichts ausgeführt werden.

Ich habe nichts davon gesetzt und werde es nicht tun.
