# Phase 9 — On-Chain Intelligence + Trading Dashboard

All data below was fetched live from free, public endpoints. Nothing invented.
No order, no swap, no key, no wallet signature.

## 1. Solana on-chain (real)

`multimarket/solana_rpc.py` talks to the free public RPC
(`api.mainnet-beta.solana.com`, verified with `getVersion`):

- **Mint authority / freeze authority** from `getAccountInfo` (jsonParsed):
  `null` means revoked, an address means still active (critical).
- **Token-2022** detected from the owning program id.
- **Token supply** from `getTokenSupply`.
- **Holder concentration** from `getTokenLargestAccounts` divided by supply.
- Any field that cannot be fetched stays `None`, which the risk engine reports
  as **UNKNOWN — never SAFE**.

Live proof: a scanned token ("CC / SOL") came back as Token-2022 with a
transfer fee and was rated **HIGH**; others hit the exit-liquidity veto.

## 2. Jupiter (real quotes, no swaps)

`multimarket/jupiter.py` uses the free lite API
(`lite-api.jup.ag/swap/v1/quote`). The older `quote-api.jup.ag/v6` host is
blocked from this environment (proxy 502) and is not used.

- Real quotes with `priceImpactPct`.
- `round_trip_quote()` quotes the buy **and** the sell of what was received, so
  a missing sell route is surfaced as an exit-liquidity red flag.
- There is no signer and no swap call anywhere in the module.

## 3. Memecoin sources — what is actually reachable

| Source | Status | Note |
|---|---|---|
| GeckoTerminal | **CONNECTED** | New pools, price, MC/FDV, liquidity, volume, buyers/sellers |
| DexScreener | **CONNECTED** | Latest token profiles (address-level) |
| Solana RPC | **CONNECTED** | Free public node |
| Jupiter | **CONNECTED** | lite-api quotes |
| Coinbase | **CONNECTED** | Public products/candles + authorised connector |
| Birdeye | not connected | free tier needs an API key — none configured |
| GMGN | not connected | not authorised in this session |
| Pump.fun / PumpSwap / Raydium | indirect | reached through GeckoTerminal/DexScreener pool data, not via their own APIs |
| Phantom | **NOT CONNECTED** | wallet — deliberately absent (no keys, no signature) |

## 4. Forward paper trading

Five virtual portfolios were started; none was forced into a trade.

| # | Market | Decision in this run |
|---|---|---|
| A | Coinbase BTC MACD-Trend | signal **SELL**; 120-day reference backtest 1 trade, −3.7 %, max DD 3.8 % |
| B | Other Coinbase coins | watching — no robust strategy cleared |
| C | Solana memecoins | **NO TRADE** — 11 of 12 scanned tokens vetoed |
| D | Micro-caps < 1M USD | **NO TRADE** — exit liquidity / data insufficient |
| E | Micro-caps < 500k USD | **NO TRADE** — exit liquidity / data insufficient |

12 tokens scanned, **9 risk vetoes**. All real, all paper.

## 5. Dashboard

`dashboard/index.html` renders the real snapshot
(`state/dashboard_snapshot.json`) with all eight sections: command centre,
AI team, live market, memecoin scanner, portfolios, trading journal, risk
centre, connectors. Live prices in the captured snapshot: BTC 68 883.83,
ETH 1 940.10, SOL 80.03 (Coinbase). Mobile and desktop verified by real
screenshots; no horizontal scroll at phone width.

Offensive token names coming from on-chain data are masked in the display; the
underlying data is unchanged.

## 6. Verification performed

- Solana RPC `getVersion` and `getTokenSupply` answered live.
- Jupiter quote returned a route with price impact for SOL→USDC.
- GeckoTerminal and DexScreener returned real payloads.
- Connector probes map CONNECTED / NOT CONNECTED correctly (unit-tested both ways).
- RPC parsing, Jupiter round-trip logic and the veto path are unit-tested with
  monkeypatched responses — no network needed in the suite.
- Dashboard rendered in a real browser, screenshots captured.

## 7. Security status

No real order, no transfer, no withdrawal, no leverage, no paid API, no key
stored, no wallet signature, live switch untouched, no auto-merge, main
unchanged.

## 8. Remaining blockers

- Honeypot detection is inferred from exit liquidity and sell-route presence,
  not from a full sell simulation against the live pool.
- Birdeye and GMGN stay unavailable without credentials.
- The dashboard is a snapshot, not a live stream (see Phase 10 section 6).
