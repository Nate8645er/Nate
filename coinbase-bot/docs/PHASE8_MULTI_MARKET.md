# Phase 8 — Multi-Market AI Trading System

Extends the existing trading_team (not a second engine) with a new
`multimarket/` package: token discovery, market-cap categorisation, memecoin
risk analysis, a liquidity-aware micro-cap paper broker, adapter status
tracking and virtual portfolios. Everything is read-only or paper; live stays
off, no keys, no wallet signing.

## 1. Implemented functions

- **Token model** (`multimarket/core.py: Token`) with every requested field
  (address, symbol, name, network, created_at, price, market cap, FDV, supply,
  liquidity, volume, trades, buyers/sellers, holders, top-holder %, price
  change, pool address, source) and a `dedup_key`.
- **Market-cap categories** 1–6 + UNKNOWN; MC vs FDV handled, `valuation()`
  marks the figure **uncertain** when circulating supply is missing. Low market
  cap is explicitly _not_ a buy signal.
- **New-token discovery** (`multimarket/discovery.py`): `GeckoTerminalSource`
  (new pools) and `DexScreenerSource` (latest profiles), both free/no-key, via
  standard-library HTTP through the agent proxy. `TokenScanner` merges and
  deduplicates. On any network/API error it returns empty and the caller
  documents the gap — no invented tokens.
- **Memecoin risk analysis** (`assess_memecoin_risk`): honeypot, mint/freeze
  authority, Token-2022 transfer fee, holder/dev concentration, wash trading,
  sell tax, and **exit-liquidity / sell feasibility**. Missing data ->
  **UNKNOWN, never SAFE**. Critical conditions set a binding `veto` for the
  RiskManager. A successful "buy" alone is not enough — a realistic sell must
  be possible.
- **Micro-cap paper broker** (`MicroCapPaperBroker`): position capped by pool
  fraction, slippage = base spread + price impact (impact grows with order
  share of liquidity), orders beyond tolerance **fail**, too little liquidity
  is **NO TRADE**, fees + priority fees charged. Paper gains cannot come from
  perfect fills.
- **Adapter registry** with status flags: Coinbase spot = PAPER (live blocked),
  Solana DEX = PAPER (sim only), Jupiter = READ ONLY, Pump.fun = READ ONLY.
  Nothing is LIVE READY and nothing auto-executes.
- **Virtual portfolios** (`Portfolio`) A–E with separate metrics (net P&L, win
  rate, profit factor, failed/no-trade count).

## 2. Actually connected data sources

| Source                                   | Status                         | Notes                                                                                                    |
| ---------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------- |
| GeckoTerminal (new pools, Solana)        | **CONNECTED (free)**           | Real HTTP, returned 18 new pools in a live run. Gives price, MC/FDV, liquidity, volume, buyers/sellers.  |
| DexScreener (token profiles)             | **CONNECTED (free)**           | Address-level discovery; market fields left None (honest).                                               |
| Coinbase Advanced Trade                  | CONNECTED (existing connector) | Spot products/prices; paper only here.                                                                   |
| Birdeye                                  | NOT connected                  | Free tier needs an API key — none configured.                                                            |
| GMGN                                     | NOT connected                  | Not authorised in this session.                                                                          |
| Solana RPC / Jupiter / Pump.fun on-chain | NOT fetched here               | Interfaces exist (`OnChain`); no RPC call wired yet, so on-chain risk inputs are UNKNOWN until supplied. |

## 3. Detected tokens (real, live run)

`run_discovery.py` against GeckoTerminal returned **18 new Solana pools**, all
category **under 100k USD**. Examples (real data): "pink/USDC" (mc/fdv ≈ 7 910,
liq ≈ 3 135), "peekaboo/SOL" (mc ≈ 2 871, liq ≈ 1 131), "mimic/SOL"
(mc ≈ 2 554, liq ≈ 2 014). Every sampled token was flagged **CRITICAL** by the
risk gate because exit liquidity is below the 5 000 USD floor -> binding veto.
This is the correct, honest outcome for brand-new thin pools, not a failure.

## 4. Paper trades

No micro-cap paper trade was opened: the discovered tokens all hit NO TRADE /
veto (insufficient exit liquidity). The broker and portfolios are unit-tested
with synthetic liquidity to prove fills, partials, failures and NO TRADE behave
correctly. The BTC MACD-trend forward paper portfolio (Portfolio A) remains the
only strategy cleared for paper from Phase 7.

## 5. Test results

`python -m pytest tests` -> **58 passing**, including Phase 8: category
boundaries, MC-vs-FDV uncertainty, missing supply, dedup, UNKNOWN-not-SAFE,
honeypot/mint-authority CRITICAL + veto, no-exit-liquidity veto, concentration
HIGH, insufficient-liquidity NO TRADE, extreme-slippage failure, partial fill,
price-impact monotonicity, buy-slips-up/sell-slips-down, adapter statuses (no
LIVE READY), portfolio metrics counting failed orders. Earlier phases' tests
(connector, team, backtest, strategies) still pass unchanged.

## 6. Security status

No real order, no transfer, no withdrawal, no leverage, no paid API, no private
key or seed stored, no wallet signing, no live switch flipped, no auto-merge,
no change to main. Live trading stays disabled; the 17.10 USDC ceiling and the
RiskManager veto are intact.

## 7. Remaining blockers / honest limitations

- **On-chain risk inputs** (mint/freeze authority, honeypot simulation, holder
  concentration) are not yet fetched from an RPC/Jupiter sim — the `OnChain`
  interface exists but is unpopulated, so those checks report UNKNOWN until a
  free RPC path is wired in.
- **Backtesting new tokens is largely impossible**: new memecoins have little
  or no history, and delisted/failed tokens leave gaps. No historical token
  data was invented. Micro-cap strategy research therefore stays forward-only.
- **Dashboard (section 11) not built**: the repo has no existing dashboard to
  extend. Deferred rather than fabricated; the data for it (adapters,
  portfolios, discovery, risk) is now available programmatically.
- **Experimental strategies (section 6 A–H)**: the price-based ones reuse the
  Phase 7 engine; on-chain/early-discovery variants need the RPC inputs above
  and are not yet meaningfully testable.

## 8. Next sensible steps

1. Wire a free Solana RPC + Jupiter quote/sim to populate `OnChain` (mint/freeze
   authority, sell simulation) so memecoin risk moves beyond liquidity-only.
2. Run multi-week **forward** paper for Portfolio A (BTC MACD) and record it.
3. Only then consider a dashboard, and only then — with separate explicit user
   consent and verified limits — discuss any live step.

A note on process: this session has grown very long and expensive. A fresh
session is advisable for the next step; the full state is in PR #50.
