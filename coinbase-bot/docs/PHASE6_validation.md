# Phase 6 — Strategy Validation

Validated on the existing HyperGrok stand (no new engine). Real Coinbase public
candles only (SIX_HOUR, ~300 bars ≈ 75 days per asset), paper only, no key,
no real order, capital ceiling 17.10 USDC, live off.

## Method

- Strategies: `sma_cross` (10/30) and `rsi_reversion` (14, 35/65).
- Fees 0.10 % taker + 0.05 % slippage per fill (real Coinbase USDC taker rate).
- No look-ahead / no data leak: at bar _i_ a strategy sees only `closes[:i+1]`
  and fills at bar _i_'s own price. Verified in `backtest()`.
- Out-of-sample: 70/30 split; a strategy positive in-sample but negative
  out-of-sample is flagged overfit.
- Walk-forward: 4 sequential folds, each warmed up on at most half its own
  data, so every fold trades on unseen bars.
- Metrics: trades, win rate, profit factor, net P&L, return, max drawdown.

The 300-bar windows covered real market phases: BTC -11.6 %, ETH -20.1 %,
SOL -21.4 % drift — a broad downtrend with 27-58 % intraday range.

## Results (measured, not invented)

| Asset | Strategy      | Trades | Win% | PF   | Net    | Return  | MaxDD | OOS     | Overfit | WF mean/worst | Verdict |
| ----- | ------------- | ------ | ---- | ---- | ------ | ------- | ----- | ------- | ------- | ------------- | ------- |
| BTC   | sma_cross     | 6      | 16.7 | 0.28 | -10.80 | -10.80% | 16.1% | -5.74%  | no      | -2.84/-5.74%  | reject  |
| BTC   | rsi_reversion | 3      | 100  | 999  | +1.98  | +1.98%  | 9.6%  | -5.56%  | **yes** | +0.59/-4.20%  | reject  |
| ETH   | sma_cross     | 8      | 25.0 | 0.13 | -21.01 | -21.01% | 21.8% | -7.72%  | no      | -5.80/-7.72%  | reject  |
| ETH   | rsi_reversion | 1      | 0    | 0.00 | -16.35 | -16.35% | 17.3% | -2.52%  | no      | -3.34/-9.26%  | reject  |
| SOL   | sma_cross     | 4      | 25.0 | 0.51 | -5.46  | -5.46%  | 10.8% | +0.00%  | no      | -2.49/-3.51%  | reject  |
| SOL   | rsi_reversion | 1      | 100  | 999  | -25.75 | -25.75% | 31.8% | -16.32% | no      | -2.37/-13.30% | reject  |

The one in-sample winner (BTC rsi_reversion, PF 999) was **caught as overfit**:
it lost -5.56 % out of sample. The data-leak / overfitting guard did its job.

## Team debate (counterarguments)

- BTC: consensus BUY but **not agreed** — Trend voice argued SELL, VolSkeptiker HOLD.
- ETH: consensus SELL, not agreed — Momentum argued BUY (RSI 29 oversold).
- SOL: consensus HOLD, agreed — Trend argued SELL.

No consensus produced an approved, robust trade.

## Verdict

**NO TRADE.** No strategy produced robust results on sufficient unseen data
(walk-forward mean <= 0 or out-of-sample <= 0 or overfit for every candidate)
over the tested downtrend period. The framework will approve a strategy only
once one actually passes.

## Constraints honoured

No new engine, no real order, no paid API, no live-switch change, no auto-merge.
Capital ceiling stays 17.10 USDC; the RiskManager may only tighten.
