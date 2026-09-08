# CRYPTO-AI-STATUS

Erzeugt: **08.09.2026 22:23 UTC** mit `python3 -m krypto.status --schreiben`.

Jede Zeile stammt aus einer Anfrage, die bei diesem Lauf
wirklich gestellt wurde. Nichts hier ist von Hand gepflegt.

| 🟢 VERIFIED | 🟡 INSTALLED | 🔴 FAILED | ⚪ NOT CONFIGURED |
|---|---|---|---|
| geprueft, lief | Code da, nicht bestaetigt | geprueft, schlug fehl | Schluessel fehlt |

## Market Data

| Baustein | Status | Bemerkung |
|---|---|---|
| 🟢 CoinGecko | VERIFIED       | ping ok |
| 🟢 DexScreener | VERIFIED       | 30 Paare fuer SOL |
| 🟢 DefiLlama | VERIFIED       | BTC 78479 USD |
| ⚪ CoinMarketCap | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Messari | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Nansen | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Arkham | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Dune | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ The Graph | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Moralis | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Alchemy | NOT CONFIGURED | kein Schluessel gesetzt |
| ⚪ Infura | NOT CONFIGURED | kein Schluessel gesetzt |

## On-chain

| Baustein | Status | Bemerkung |
|---|---|---|
| 🟢 Ethereum | VERIFIED       | Block 25935607 |
| 🟢 Base | VERIFIED       | Block 51058419 |
| 🟢 Arbitrum | VERIFIED       | Block 503164153 |
| 🟢 Optimism | VERIFIED       | Block 156653705 |
| 🟢 Bsc | VERIFIED       | Block 120765599 |
| 🟢 Avalanche | VERIFIED       | Block 94806185 |
| 🟢 Polygon | VERIFIED       | Block 93467437 |
| 🟢 Solana | VERIFIED       | Block 445450804 |
| 🟢 Bitcoin | VERIFIED       | Block 966117 |
| ⚪ Etherscan | NOT CONFIGURED | geprueft: antwortet 'Missing/Invalid API Key' |

## Social

| Baustein | Status | Bemerkung |
|---|---|---|
| 🟢 Fear-and-Greed | VERIFIED       | Index 69 (Greed) |
| 🟢 CoinGecko Trends | VERIFIED       | 15 Werte |
| 🔴 Reddit | FAILED         | geprueft: HTTP 403 aus Rechenzentren |
| ⚪ X / Twitter | NOT CONFIGURED | Zugang kostenpflichtig |
| ⚪ Telegram | NOT CONFIGURED | braucht Bot-Konto in der Gruppe |
| ⚪ Discord | NOT CONFIGURED | braucht Bot-Konto in der Gruppe |
| ⚪ LunarCrush | NOT CONFIGURED | geprueft: HTTP 401 ohne Schluessel |
| ⚪ Santiment | NOT CONFIGURED | Metriken brauchen ein Konto |

## News

| Baustein | Status | Bemerkung |
|---|---|---|
| 🟢 RSS (Cointelegraph, Decrypt) | VERIFIED       | 68 Schlagzeilen aus 2 Feeds |

## Fomo

| Baustein | Status | Bemerkung |
|---|---|---|
| ⚪ fomo.family API | NOT CONFIGURED | keine oeffentliche API gefunden; /api und /docs liefern die App-Seite |
| ⚪ fomo.family MCP | NOT CONFIGURED | kein MCP-Server auffindbar |
| 🔴 fomo.family robots.txt | FAILED         | verbietet /coin /token /prices/ /profile/ /u/ - kein automatisierter Abruf erlaubt |
| ⚪ fomoapi.io (Dritter) | NOT CONFIGURED | unabhaengig, NICHT offiziell; Schluessel und ab 1000 Credits/Monat kostenpflichtig |
| 🟢 Fomo-Ersatzschicht | VERIFIED       | DexScreener + Trendliste + Fear-and-Greed + RSS |

## System

| Baustein | Status | Bemerkung |
|---|---|---|
| 🟢 Signal-Engine | VERIFIED       | DATA_INCOMPLETE bei fehlenden Daten |
| 🟢 Risk-Engine (Token) | VERIFIED       | leere Eingabe -> UNKNOWN |
| 🟢 Risikowache (Depot) | VERIFIED       | 7 Grenzen aktiv |
| 🟢 Paper Trading | VERIFIED       | Depot 10000.00 USD |
| 🟢 Backtesting | VERIFIED       | 199 Kerzen gerechnet |
| 🟢 Live Trading | VERIFIED       | GESPERRT - 3 offene Punkte |

## Sicherheit

| Baustein | Status | Bemerkung |
|---|---|---|
| 🟢 Zugangsdaten gitignoriert | VERIFIED       | .env, *.pem, *.key |
| 🟢 Protokoll-Schwaerzung | VERIFIED       | api_key/password/token/mail werden ersetzt |
| 🟢 RPC nur lesend | VERIFIED       | Positivliste, 20 erlaubte Methoden |
| 🟢 Kostenschranke | VERIFIED       | keine kostenpflichtige Quelle eingebunden |

## Zusammenzug

| Status | Anzahl |
|---|---|
| 🟢 VERIFIED | 26 |
| 🟡 INSTALLED | 0 |
| 🔴 FAILED | 2 |
| ⚪ NOT CONFIGURED | 18 |

**26 von 46 Bausteinen laufen nachweislich.**

Der Rest ist kein Fehler, sondern eine Grenze: die meisten
⚪-Zeilen brauchen einen kostenpflichtigen Schluessel. Ich habe
keinen gekauft und werde keinen kaufen.
