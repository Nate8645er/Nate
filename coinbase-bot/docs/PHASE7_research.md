# Phase 7 — Advanced Strategy Research

On the existing HyperGrok stand. Real Coinbase public daily candles (1100 days
≈ 3 years each, BTC-USD / ETH-USD / SOL-USD), paper only, no key, no paid API,
no real order, capital ceiling 17.10 USDC, live off.

## Phase 1 — Backtesting hardened (look-ahead removed)

- **No look-ahead:** the signal at bar _i_ uses only completed candles
  (`bars[:i+1]`); the fill happens at bar _i+1_'s **open**, never on the signal
  candle or a future close. Regression test `test_fill_happens_at_next_bar_open`.
- **Execution after the signal:** entries/exits occur on the next bar, matching
  "simulate execution no earlier than after the signal is known."
- **Fees + slippage:** 0.10 % taker + 0.05 % per fill.
- **SOL contradiction resolved:** the old engine left a position open at series
  end, so a single closed win could sit next to a negative total. The engine now
  **force-closes** at the last candle, so win rate / profit factor reconcile
  with net P&L. Regression test `test_sol_paradox_resolved...`.
- **Performance:** MACD was O(n^3) across the loop (33 s per run); rewritten to
  O(n) (0.18 s), identical result.

## Phases 2-4 — Strategy comparison (measured, not invented)

Columns: trades, win %, profit factor, net return %, max drawdown %,
out-of-sample return %, overfit flag, walk-forward mean % (5 folds),
sensitivity-stable (doubled fees + data shift), RiskManager decision.

### BTC-USD (steigend, Tagesvol 2.5 %)

| Strategy            | Trades | Win% | PF   | Net%  | MaxDD% | OOS%  | Overfit | WF mean | Sens | Risk               |
| ------------------- | ------ | ---- | ---- | ----- | ------ | ----- | ------- | ------- | ---- | ------------------ |
| macd_trend          | 44     | 34   | 1.27 | +27.5 | 26.5   | +9.9  | no      | +5.84   | yes  | **paper-freigabe** |
| breakout_volume     | 13     | 46   | 1.17 | +14.6 | 42.2   | +0.8  | yes     | +10.74  | yes  | NO TRADE           |
| rsi_trend           | 1      | 0    | 0.00 | -0.0  | 8.7    | 0.0   | no      | -0.00   | yes  | NO TRADE           |
| ema_atr_stop        | 20     | 30   | 1.54 | +59.0 | 32.5   | +2.8  | yes     | +17.12  | yes  | NO TRADE           |
| momentum_vol_filter | 35     | 26   | 1.20 | +25.1 | 37.3   | -8.8  | yes     | +8.47   | yes  | NO TRADE           |
| mean_reversion      | 13     | 62   | 1.17 | +12.5 | 39.5   | -22.4 | yes     | +8.16   | yes  | NO TRADE           |
| multi_signal        | 32     | 28   | 1.15 | +19.6 | 33.7   | -13.0 | yes     | +8.25   | yes  | NO TRADE           |

### ETH-USD (seitwärts, Tagesvol 3.5 %)

| Strategy            | Trades | Win% | PF   | Net%  | MaxDD% | OOS%  | Overfit | WF mean | Sens | Risk     |
| ------------------- | ------ | ---- | ---- | ----- | ------ | ----- | ------- | ------- | ---- | -------- |
| macd_trend          | 39     | 28   | 1.03 | +7.2  | 54.4   | +0.2  | yes     | +17.52  | no   | NO TRADE |
| breakout_volume     | 9      | 56   | 1.85 | +77.1 | 46.1   | +8.7  | yes     | +23.47  | yes  | NO TRADE |
| rsi_trend           | 1      | 100  | 999  | +3.6  | 10.2   | 0.0   | yes     | +0.72   | yes  | NO TRADE |
| ema_atr_stop        | 17     | 35   | 1.57 | +66.3 | 46.4   | +16.6 | yes     | +26.82  | yes  | NO TRADE |
| momentum_vol_filter | 32     | 25   | 1.62 | +89.0 | 46.3   | +21.2 | yes     | +28.50  | yes  | NO TRADE |
| mean_reversion      | 10     | 40   | 0.40 | -60.2 | 69.2   | -24.2 | no      | +10.77  | yes  | NO TRADE |
| multi_signal        | 27     | 33   | 1.31 | +35.6 | 46.6   | +12.5 | yes     | +15.01  | yes  | NO TRADE |

### SOL-USD (steigend, Tagesvol 4.2 %)

| Strategy            | Trades | Win% | PF   | Net%  | MaxDD% | OOS%  | Overfit | WF mean | Sens | Risk     |
| ------------------- | ------ | ---- | ---- | ----- | ------ | ----- | ------- | ------- | ---- | -------- |
| macd_trend          | 47     | 34   | 1.14 | +27.0 | 57.2   | +12.6 | no      | +20.60  | yes  | NO TRADE |
| breakout_volume     | 11     | 36   | 0.68 | -35.9 | 67.2   | -14.4 | no      | +9.93   | yes  | NO TRADE |
| rsi_trend           | 0      | 0    | 0.00 | 0.0   | 0.0    | 0.0   | no      | 0.00    | yes  | NO TRADE |
| ema_atr_stop        | 18     | 33   | 0.92 | -10.4 | 62.5   | +0.2  | no      | +17.48  | yes  | NO TRADE |
| momentum_vol_filter | 35     | 37   | 1.45 | +66.5 | 42.7   | +14.0 | yes     | +21.89  | yes  | NO TRADE |
| mean_reversion      | 12     | 67   | 0.76 | -30.8 | 66.1   | -12.1 | no      | +12.05  | yes  | NO TRADE |
| multi_signal        | 33     | 33   | 1.03 | +3.4  | 52.4   | +3.7  | no      | +10.85  | no   | NO TRADE |

Robustness gate (all required): >=8 trades, PF > 1.2, not overfit, OOS > 0,
walk-forward mean > 0, worst fold > -20 %, sensitivity-stable.

## Phase 5 — Team debate (same data, counterarguments)

- BTC-USD: consensus BUY, **not agreed** — Trend argued SELL, VolSkeptiker HOLD.
- ETH-USD: consensus BUY, **not agreed** — Trend argued SELL, VolSkeptiker HOLD.
- SOL-USD: consensus SELL, **not agreed** — Momentum argued BUY (RSI 21), MeanReversion HOLD.

No consensus was unanimous; the RiskManager keeps the binding veto.

## Verdict

**One** strategy passed every independent check: **`macd_trend` on BTC-USD**
(PF 1.27, OOS +9.9 %, not overfit, walk-forward mean +5.84 %, sensitivity
stable, 44 trades). The RiskManager clears it for **paper only**.

Every other strategy/asset is **NO TRADE** — mostly caught by the overfitting
guard (strong in-sample, weak out-of-sample) or a negative out-of-sample return.
Notably the biggest in-sample winners (ETH momentum +89 %, ETH ema_atr +66 %)
were all flagged overfit.

## Next step (not done here)

`macd_trend @ BTC-USD` goes to **independent forward paper trading** before any
live consideration. A single passing strategy is not a mandate; a good backtest
alone never authorises live trading. Live stays off; the 17.10 USDC ceiling and
the RiskManager veto remain in force. No real order, no transfer, no leverage,
no paid API, no live-switch change, no auto-merge.
