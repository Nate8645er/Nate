# Phase 18/19 — CDP API Key Integration & Real-Money Readiness

**Verdict: NOT READY.** The uploaded key authenticated successfully, but it is
**refused by the bot on purpose** for two concrete, fixable reasons. No real
order was sent, no leverage touched, nothing merged. The private key was used
once, in memory only, for the read-only checks below, and never written to the
repo, a log, or this report.

## Security notice — act on this first

Your private key was uploaded into this chat, so it now exists in the
conversation history, not only on your laptop. **Delete this key in the Coinbase
CDP portal and create a fresh one.** A key that has been in a chat should not be
used for live trading.

## What the real connection showed (read-only)

The key is valid and the official SDK reached Coinbase with it (Ed25519,
through the session proxy). Then:

| Check                         | Result                                            |
| ----------------------------- | ------------------------------------------------- |
| Authentication                | **OK** — key valid, SDK + Ed25519 work            |
| Permissions                   | can_view YES, can_trade YES, **can_transfer YES** |
| Key's portfolio               | `...063ba2` (type DEFAULT)                        |
| Accounts in that portfolio    | **none with a balance** — 0 USDC, 0 BTC           |
| Open orders / history / fills | 0 / 0 / 0                                         |
| Spot fees                     | taker 0.10 %, maker 0.09 %                        |
| Futures (CFM) balance summary | none -> no futures account                        |

## Two blockers (both real, both fixable)

**1. The key can transfer/withdraw.** Your own rule is View + Trade only. The
connector refuses any transfer-capable key at construction — this is a hard
safety rule and I did not disable it:

```
ConnectorError: API key has transfer permission. Create a key with View + Trade only.
```

**2. The key is bound to the wrong portfolio.** Its portfolio `...063ba2` holds
no funds. Your 17.10 USDC sits in a different portfolio (`...4eb846`, the one the
earlier test orders ran in). Even with transfer turned off, this key would see
0 USDC and could not trade. The new key must be created **inside the portfolio
that holds the trading capital**.

## Status table (Funktion | Status | Nachweis | Blockade)

| Funktion                          | Status                  | Nachweis                                               | Blockade                                   |
| --------------------------------- | ----------------------- | ------------------------------------------------------ | ------------------------------------------ |
| API-Authentifizierung             | **READY**               | Key valid, SDK verband sich                            | —                                          |
| Schluessel-Import (JSON/PEM/Text) | **READY**               | `keyfile.py`, 8 Tests                                  | —                                          |
| Berechtigungen View+Trade         | PARTIALLY               | can_view/can_trade aktiv                               | Transfer ebenfalls aktiv                   |
| Kein Transfer/Withdraw            | **NOT READY**           | can_transfer = True                                    | Neuer Key noetig                           |
| Portfolio-Isolation               | **NOT READY**           | Key-Portfolio `...063ba2` != Kapital-Portfolio         | Key im richtigen Portfolio erstellen       |
| USDC-Guthaben lesen               | PARTIALLY               | 0 USDC im Key-Portfolio                                | Kapital liegt woanders                     |
| Offene/historische Orders         | READY (leer)            | 0 Orders, API antwortet                                | —                                          |
| Fill-Reconciliation               | **READY**               | `reconcile_fills`, an echten Fills geprueft (Phase 17) | braucht Key im Kapital-Portfolio fuer Live |
| Gebuehren                         | **READY**               | taker 0.10 %, maker 0.09 % gelesen                     | —                                          |
| Spot Trading                      | SUPPORTED / API_ENABLED | can_trade, Spot-Gebuehren                              | Kapital-Portfolio + View+Trade-Key         |
| Margin Trading                    | NOT AVAILABLE           | kein Margin-Konto sichtbar                             | —                                          |
| Perpetual Futures (INTX)          | NOT AVAILABLE           | kein INTX-Portfolio                                    | —                                          |
| US-Futures (CFM)                  | NOT AVAILABLE           | balance_summary leer                                   | separate Coinbase-Freischaltung noetig     |
| Hebel / Short                     | NOT AVAILABLE           | keine Derivate-Freischaltung                           | bewusst nicht aktiviert                    |
| Not-Aus (persistent)              | **READY**               | Phase 14/15, Tests                                     | —                                          |
| Stop-Loss / Monitor               | **READY**               | Phase 15/16, Tests                                     | —                                          |
| 15-Agenten-Meeting + Veto         | **READY**               | Phase 10-16, Tests                                     | —                                          |
| Dashboard Echtgeld-Felder         | **READY**               | `/api/live`, zeigt UNBEKANNT ohne Key                  | Key fuer Live-Werte                        |
| LIVE AUTONOMOUS                   | **BLOCKED (gewollt)**   | nicht scharfgeschaltet                                 | eigene Freigabe von Nate                   |

## 14 Readiness-Kriterien

Unveraendert **11/14**. Die drei offenen (2 Verbindung, 3 Isolation, 14 Live-
Reconciliation) bleiben FAIL, weil der Connector diesen Key ablehnt. Mit einem
View+Trade-Key im richtigen Portfolio laufen sie auf dem Laptop durch; die neuen
Pruefungen aus Phase 17 (per-Account-Isolation, Fill-Abgleich) greifen dann.

## Was gebaut wurde

- `coinbase_connector/keyfile.py` — sicherer Import einer CDP-Schluesseldatei,
  Autoerkennung JSON/PEM/Text, nichts wird auf Platte geschrieben, keine
  Secret-Ausgabe. 8 Tests.
- Connector nimmt `credentials` in-memory entgegen (kein Schluessel auf Platte).
- Backend und `readiness.ps1`/`readiness_check.py` nutzen `COINBASE_KEY_FILE`.
- **162 Tests gruen.**

## Dein naechster Schritt

1. **Diesen Schluessel im CDP-Portal loeschen.**
2. Neuen Schluessel erstellen: **View + Trade, KEIN Transfer**, **im Portfolio
   mit den 17.10 USDC** (`...4eb846`).
3. Datei auf dem Laptop speichern, dann in `coinbase-bot\.env`:
   `COINBASE_KEY_FILE=C:\Pfad\zu\cdp_api_key.json`
4. `windows\readiness.ps1` ausfuehren.

Zeigt das 14/14, hole ich — wie vereinbart — eine **separate Aktivierungs-
entscheidung fuer Spot-Trading** ein. Hebel bleibt aus; eine Freischaltung dafuer
waere eine eigene, spaetere Entscheidung und ist auf diesem Konto derzeit ohnehin
nicht verfuegbar.
