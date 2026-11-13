# Phase 5 — Trading Intelligence & Skills Integration

Investigated the requested GitHub projects and integrated only self-written,
dependency-free improvements into the existing HyperGrok architecture. No
third-party trading code was installed, no second engine was built, no real
order was placed, and the live switch stays off.

## Repositories investigated

| Repo                                  | Publisher / License         | Verdict                 | Why                                                                                                                                       |
| ------------------------------------- | --------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| coinbase/coinbase-advanced-py         | Coinbase, Apache-2.0        | **Keep (already used)** | Official SDK; the verified connector builds on it.                                                                                        |
| TauricResearch/TradingAgents          | Tauric Research, Apache-2.0 | **Pattern only**        | Multi-agent debate idea adopted; the framework needs many paid LLM/data API keys — not installed.                                         |
| freqtrade/freqtrade                   | freqtrade, **GPL-3.0**      | **Pattern only**        | Full bot + backtester. GPL would infect the repo if copied; it is also a second engine. Backtest/walk-forward reimplemented from scratch. |
| freqtrade/freqai.md                   | freqtrade, GPL-3.0          | **Not used**            | Heavy ML stack; out of scope for a 17.10 USDC paper bot.                                                                                  |
| anthropics/claude-plugins-official    | Anthropic                   | **Not used**            | Not trading-specific; nothing needed here.                                                                                                |
| jup-ag/docs                           | Jupiter                     | **Not used**            | Solana DEX; irrelevant to Coinbase spot.                                                                                                  |
| Jakeschincariol/trader-skill          | MIT, ~1.8k stars            | **Not integrated**      | US-equities (13F, Congress, Alpaca). Not Coinbase crypto; would add external data endpoints.                                              |
| Jakeschincariol/day-trader-skill      | MIT, ~7.6k stars            | **Pattern only**        | Good "risk-gated ticket before order" idea — already matched by our connector + risk manager. Equities-focused, not integrated.           |
| agiprolabs/claude-trading-skills      | MIT                         | **Pattern only**        | 68 crypto/DeFi (Solana) skills; needs `uv` + per-skill deps, some API keys, some can execute DEX trades. Not integrated.                  |
| shakeebshaan/claude-code-quant-skills | MIT, 3 stars                | **Checklist adopted**   | Prompt-only; its backtest-bias / overfitting checklist informed `backtest.overfitting_check`. No files copied.                            |

Security note: the four personal skill repos ship runnable scripts that call
external endpoints and, in some cases, can route real orders. None were
executed or imported. Only ideas were reused; all new code is original.

## Components added (all in `trading_team/`, no new dependencies)

- `indicators.py` — SMA, EMA, RSI, MACD, ATR, Bollinger (standard library).
- `collaboration.py` — a debate room: four voices (Trend, Momentum,
  MeanReversion, VolSkeptiker) judge the **same** market data, may disagree
  (challenges are recorded), and a weighted consensus is formed. A BUY still
  passes the binding RiskManager veto; the room readily returns **NO TRADE**.
- `backtest.py` — historical backtest with taker fees and slippage, max
  drawdown, in-sample/out-of-sample split, walk-forward folds, and an
  overfitting check.
- `hypergrok_config.py` — absolute capital ceiling **17.10 USDC**; live stays
  disabled (`limits_confirmed=False`), ceiling never raised automatically.

## Validated against REAL Coinbase data (public candles, no key)

BTC-USDC, 120 x 1h candles:

- Debate result: Trend=SELL, others HOLD -> consensus HOLD, decision **no_trade**
  (one recorded challenge from the Trend voice). The team correctly declined.
- SMA-cross backtest: 4 trades, return -2.13 %, max drawdown 2.13 %, fees 0.3952.
- Overfitting check: in-sample -1.89 %, out-of-sample 0.0 % -> not flagged.
- Walk-forward (4 folds): [-0.15, 0, 0, 0] %, mean -0.04 %.

These are real measured results on live data, not invented.

## Tests (36 passing)

Phase 7 collaboration checks included: all voices receive the same report;
voices can disagree; the RiskManager can veto a consensus BUY; no order is
prepared twice (cloid guard in the connector); fees are accounted for in paper
and backtest; strategies validated independently (walk-forward / OOS); the
team accepts NO TRADE; the emergency stop blocks every new buy.

## Costs and open blockers

- Added cost: **none** — standard library only, free public market data.
- Live trading remains blocked until the user separately and explicitly
  confirms activation of the 17.10 USDC limit (Phase 6 forbids flipping it here).
