"""Core of the HyperGrok autonomous trading team.

Agents:
  MarketAnalyst   - reads real candles, measures trend / volatility / volume.
  Strategist      - turns analysis into a signal with stop-loss, take-profit,
                    hold horizon and a suggested position size.
  RiskManager     - approves or rejects a signal against capital and loss
                    limits. It may tighten limits on its own but can never
                    raise the user-confirmed absolute loss limit.
  ExecutionAgent  - routes an approved order to the paper broker, or (only
                    when a human has confirmed limits) to the live connector.
  TradeReviewer   - records every trade and computes realised P&L incl. fees.
  Supervisor      - runs one decision cycle and owns the emergency stop.

Design rules:
  * Real-money execution is OFF until RiskConfig.limits_confirmed is True and a
    positive absolute_max_loss_usdc is set. Until then the ExecutionAgent only
    touches the PaperBroker, whatever the mode argument says.
  * The team never holds leverage, never transfers and never withdraws.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import ROUND_DOWN, Decimal
from pathlib import Path
from typing import Any, Literal

Side = Literal["BUY", "SELL"]
D = Decimal


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RiskConfig:
    """Risk limits. The absolute loss limit is the one number only the user
    may set; everything else the RiskManager may tighten but not loosen past
    these ceilings."""

    allocated_capital_usdc: Decimal = D("0")
    # User-confirmed hard floor on remaining equity. 0 means NOT confirmed,
    # which keeps live trading disabled.
    absolute_max_loss_usdc: Decimal = D("0")
    limits_confirmed: bool = False
    # Fraction of allocated capital a single position may use. 1.0 = 100 %.
    max_position_fraction: Decimal = D("1.0")
    # Soft daily loss cap; must not exceed absolute_max_loss_usdc.
    daily_loss_limit_usdc: Decimal = D("0")
    # Most a single trade may risk (stop-loss distance x size).
    per_trade_risk_usdc: Decimal = D("0")
    taker_fee_rate: Decimal = D("0.001")
    min_order_usdc: Decimal = D("1")

    def live_allowed(self) -> bool:
        return self.limits_confirmed and self.absolute_max_loss_usdc > 0


@dataclass(frozen=True)
class AnalystReport:
    symbol: str
    last_price: Decimal
    sma_fast: Decimal
    sma_slow: Decimal
    trend: Literal["up", "down", "flat"]
    volatility: Decimal  # stdev of recent returns
    momentum: Decimal  # last_price / sma_slow - 1


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side | None  # None = stay flat
    reason: str
    entry: Decimal = D("0")
    stop_loss: Decimal = D("0")
    take_profit: Decimal = D("0")
    size_fraction: Decimal = D("0")  # of allocated capital
    hold_seconds: int = 0


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    quote_size_usdc: Decimal = D("0")
    effective_stop: Decimal = D("0")


# --------------------------------------------------------------------------
# Market Analyst
# --------------------------------------------------------------------------


class MarketAnalyst:
    def __init__(self, fast: int = 10, slow: int = 30):
        self.fast, self.slow = fast, slow

    def analyse(
        self, symbol: str, closes: list[Decimal], volumes: list[Decimal] | None = None
    ) -> AnalystReport:
        if len(closes) < self.slow:
            raise ValueError(f"Need at least {self.slow} candles, got {len(closes)}.")
        sma_fast = sum(closes[-self.fast :]) / self.fast
        sma_slow = sum(closes[-self.slow :]) / self.slow
        last = closes[-1]
        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
            if closes[i - 1] != 0
        ]
        vol = (
            D(str(statistics.pstdev([float(r) for r in returns[-self.slow :]])))
            if returns
            else D("0")
        )
        if sma_fast > sma_slow * D("1.001"):
            trend = "up"
        elif sma_fast < sma_slow * D("0.999"):
            trend = "down"
        else:
            trend = "flat"
        momentum = last / sma_slow - 1 if sma_slow else D("0")
        return AnalystReport(symbol, last, sma_fast, sma_slow, trend, vol, momentum)


# --------------------------------------------------------------------------
# Strategist
# --------------------------------------------------------------------------


class Strategist:
    """Simple, auditable momentum strategy. Long-only on spot (no shorting,
    no leverage). Decides entry, stop-loss, take-profit, size and hold time."""

    def __init__(
        self,
        stop_pct: Decimal = D("0.02"),
        take_pct: Decimal = D("0.04"),
        base_fraction: Decimal = D("0.5"),
        hold_seconds: int = 3600,
    ):
        self.stop_pct, self.take_pct = stop_pct, take_pct
        self.base_fraction, self.hold_seconds = base_fraction, hold_seconds

    def decide(self, report: AnalystReport, holding: bool) -> Signal:
        price = report.last_price
        if holding:
            # Exit logic is handled by stop/take in the broker; strategist only
            # flattens on a trend break.
            if report.trend == "down":
                return Signal(
                    report.symbol,
                    "SELL",
                    "Trend gedreht (abwärts), Position schließen",
                    entry=price,
                )
            return Signal(report.symbol, None, "Trend intakt, halten")
        if report.trend == "up" and report.momentum > D("0.002"):
            # Stronger momentum -> larger (but still capped) fraction.
            frac = min(self.base_fraction + report.momentum * 10, D("1.0"))
            return Signal(
                report.symbol,
                "BUY",
                f"Aufwärtstrend, Momentum {report.momentum:.4f}",
                entry=price,
                stop_loss=price * (1 - self.stop_pct),
                take_profit=price * (1 + self.take_pct),
                size_fraction=frac,
                hold_seconds=self.hold_seconds,
            )
        return Signal(report.symbol, None, f"Kein Setup (Trend {report.trend})")


# --------------------------------------------------------------------------
# Risk Manager
# --------------------------------------------------------------------------


class RiskManager:
    def __init__(self, config: RiskConfig):
        # Normalise: soft limits may never exceed the user's absolute ceiling.
        abs_loss = config.absolute_max_loss_usdc
        daily = config.daily_loss_limit_usdc
        if abs_loss > 0:
            daily = min(daily, abs_loss) if daily > 0 else abs_loss
        self.config = replace(config, daily_loss_limit_usdc=daily)
        self.realized_loss_today = D("0")
        self.halted = False
        self.halt_reason = ""

    def tighten(
        self,
        *,
        daily_loss_limit: Decimal | None = None,
        max_position_fraction: Decimal | None = None,
        per_trade_risk: Decimal | None = None,
    ) -> None:
        """The RiskManager may lower limits on its own. It can never raise the
        user-confirmed absolute loss limit, and this method cannot touch it."""
        c = self.config
        if daily_loss_limit is not None:
            new_daily = (
                min(daily_loss_limit, c.daily_loss_limit_usdc)
                if c.daily_loss_limit_usdc > 0
                else daily_loss_limit
            )
        else:
            new_daily = c.daily_loss_limit_usdc
        new_frac = (
            min(max_position_fraction, c.max_position_fraction)
            if max_position_fraction is not None
            else c.max_position_fraction
        )
        if per_trade_risk is not None:
            new_risk = (
                min(per_trade_risk, c.per_trade_risk_usdc)
                if c.per_trade_risk_usdc > 0
                else per_trade_risk
            )
        else:
            new_risk = c.per_trade_risk_usdc
        self.config = replace(
            c,
            daily_loss_limit_usdc=new_daily,
            max_position_fraction=new_frac,
            per_trade_risk_usdc=new_risk,
        )

    def record_loss(self, amount: Decimal) -> None:
        if amount > 0:
            self.realized_loss_today += amount
        self._check_halt()

    def _check_halt(self) -> None:
        c = self.config
        if (
            c.absolute_max_loss_usdc > 0
            and self.realized_loss_today >= c.absolute_max_loss_usdc
        ):
            self.emergency_stop(
                f"Absolute Verlustgrenze erreicht ({self.realized_loss_today} >= {c.absolute_max_loss_usdc})"
            )
        elif (
            c.daily_loss_limit_usdc > 0
            and self.realized_loss_today >= c.daily_loss_limit_usdc
        ):
            self.emergency_stop(
                f"Tagesverlustgrenze erreicht ({self.realized_loss_today} >= {c.daily_loss_limit_usdc})"
            )

    def emergency_stop(self, reason: str) -> None:
        self.halted = True
        self.halt_reason = reason

    def evaluate(self, signal: Signal) -> RiskDecision:
        c = self.config
        if self.halted:
            return RiskDecision(False, f"Not-Aus aktiv: {self.halt_reason}")
        if signal.side != "BUY":
            return RiskDecision(True, "Verkauf/Flat benötigt keine Kapitalfreigabe")
        if c.allocated_capital_usdc <= 0:
            return RiskDecision(False, "Kein Trading-Kapital zugewiesen")
        frac = min(signal.size_fraction, c.max_position_fraction)
        quote = (c.allocated_capital_usdc * frac).quantize(
            D("0.01"), rounding=ROUND_DOWN
        )
        if quote < c.min_order_usdc:
            return RiskDecision(
                False, f"Ordergröße {quote} unter Minimum {c.min_order_usdc}"
            )
        # Risk = stop distance * size. Reject if it exceeds per-trade risk or
        # what is left before the absolute loss limit.
        if signal.entry > 0 and signal.stop_loss > 0:
            stop_dist = (signal.entry - signal.stop_loss) / signal.entry
            risk_amount = quote * stop_dist
            if c.per_trade_risk_usdc > 0 and risk_amount > c.per_trade_risk_usdc:
                return RiskDecision(
                    False,
                    f"Trade-Risiko {risk_amount:.2f} über Limit {c.per_trade_risk_usdc}",
                )
            remaining = c.absolute_max_loss_usdc - self.realized_loss_today
            if c.absolute_max_loss_usdc > 0 and risk_amount > remaining:
                return RiskDecision(
                    False,
                    f"Trade-Risiko {risk_amount:.2f} über Restbudget {remaining:.2f}",
                )
        return RiskDecision(
            True,
            f"Freigegeben: {quote} USDC ({frac:.2f} des Kapitals)",
            quote_size_usdc=quote,
            effective_stop=signal.stop_loss,
        )


# --------------------------------------------------------------------------
# Paper broker
# --------------------------------------------------------------------------


@dataclass
class PaperBroker:
    """Simulated broker that fills market orders at a supplied real price and
    charges the real taker fee. Keeps cash and one position per symbol."""

    cash_usdc: Decimal
    taker_fee_rate: Decimal = D("0.001")
    positions: dict[str, Decimal] = field(default_factory=dict)
    avg_cost: dict[str, Decimal] = field(default_factory=dict)
    journal: Path | None = None

    def market_buy(self, symbol: str, quote_usdc: Decimal, price: Decimal) -> dict:
        fee = quote_usdc * self.taker_fee_rate
        spend = quote_usdc
        if spend + fee > self.cash_usdc:
            raise ValueError("Paper: zu wenig Cash")
        qty = (quote_usdc - fee) / price
        prev_qty = self.positions.get(symbol, D("0"))
        prev_cost = self.avg_cost.get(symbol, D("0")) * prev_qty
        self.positions[symbol] = prev_qty + qty
        self.avg_cost[symbol] = (prev_cost + quote_usdc) / (prev_qty + qty)
        self.cash_usdc -= spend
        return self._record(symbol, "BUY", qty, price, fee)

    def market_sell(self, symbol: str, qty: Decimal, price: Decimal) -> dict:
        held = self.positions.get(symbol, D("0"))
        qty = min(qty, held)
        if qty <= 0:
            raise ValueError("Paper: keine Position")
        gross = qty * price
        fee = gross * self.taker_fee_rate
        self.cash_usdc += gross - fee
        self.positions[symbol] = held - qty
        if self.positions[symbol] == 0:
            self.avg_cost.pop(symbol, None)
        return self._record(symbol, "SELL", qty, price, fee)

    def _record(
        self, symbol: str, side: Side, qty: Decimal, price: Decimal, fee: Decimal
    ) -> dict:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "side": side,
            "qty": str(qty),
            "price": str(price),
            "fee": str(fee),
            "cash_after": str(self.cash_usdc),
        }
        if self.journal:
            self.journal.parent.mkdir(parents=True, exist_ok=True)
            with self.journal.open("a") as f:
                f.write(json.dumps(row) + "\n")
        return row

    def equity(self, prices: dict[str, Decimal]) -> Decimal:
        total = self.cash_usdc
        for symbol, qty in self.positions.items():
            total += qty * prices.get(symbol, self.avg_cost.get(symbol, D("0")))
        return total


# --------------------------------------------------------------------------
# Execution agent
# --------------------------------------------------------------------------


class ExecutionAgent:
    """Routes orders. Paper mode always works. Live mode is refused unless the
    user has confirmed limits; even then it only PREPARES the order and hands
    the confirmation phrase back — the real order still needs the connector's
    own LIVE_TRADING_ENABLED flag and a human confirmation string."""

    def __init__(self, config: RiskConfig, broker: PaperBroker, connector: Any = None):
        self.config, self.broker, self.connector = config, broker, connector

    def execute_paper(
        self, decision: RiskDecision, signal: Signal, price: Decimal
    ) -> dict:
        if signal.side == "BUY":
            return self.broker.market_buy(
                signal.symbol, decision.quote_size_usdc, price
            )
        if signal.side == "SELL":
            qty = self.broker.positions.get(signal.symbol, D("0"))
            return self.broker.market_sell(signal.symbol, qty, price)
        return {"side": "FLAT"}

    def prepare_live(self, decision: RiskDecision, signal: Signal) -> dict:
        if not self.config.live_allowed():
            return {
                "blocked": True,
                "reason": "Live-Trading gesperrt: absolute Kapital-/Verlustgrenze nicht bestätigt.",
            }
        # Even when allowed, we only describe the order; a human still has to
        # drive the connector's execute_real_* with its confirmation phrase.
        return {
            "blocked": False,
            "product_id": signal.symbol,
            "side": signal.side,
            "quote_size": str(decision.quote_size_usdc),
            "note": "Bereit zur manuellen Freigabe über den Connector.",
        }


# --------------------------------------------------------------------------
# Trade reviewer
# --------------------------------------------------------------------------


class TradeReviewer:
    def __init__(self) -> None:
        self.trades: list[dict] = []

    def record(self, row: dict) -> None:
        self.trades.append(row)

    def round_trip_pnl(self, symbol: str) -> Decimal:
        """Realised P&L for matched BUY/SELL on a symbol, fees included."""
        buys = [
            (D(t["qty"]), D(t["price"]), D(t["fee"]))
            for t in self.trades
            if t["symbol"] == symbol and t["side"] == "BUY"
        ]
        sells = [
            (D(t["qty"]), D(t["price"]), D(t["fee"]))
            for t in self.trades
            if t["symbol"] == symbol and t["side"] == "SELL"
        ]
        buy_cost = sum((q * p + f for q, p, f in buys), D("0"))
        sell_proceeds = sum((q * p - f for q, p, f in sells), D("0"))
        return sell_proceeds - buy_cost


# --------------------------------------------------------------------------
# Supervisor
# --------------------------------------------------------------------------


class Supervisor:
    def __init__(
        self,
        config: RiskConfig,
        analyst: MarketAnalyst,
        strategist: Strategist,
        risk: RiskManager,
        execution: ExecutionAgent,
        reviewer: TradeReviewer,
    ):
        self.config = config
        self.analyst, self.strategist = analyst, strategist
        self.risk, self.execution, self.reviewer = risk, execution, reviewer
        self.log: list[dict] = []

    def emergency_stop(self, reason: str) -> None:
        self.risk.emergency_stop(reason)
        self.log.append({"event": "EMERGENCY_STOP", "reason": reason})

    def run_cycle(
        self,
        symbol: str,
        closes: list[Decimal],
        mode: Literal["paper", "live"] = "paper",
    ) -> dict:
        if self.risk.halted:
            return {
                "symbol": symbol,
                "action": "halted",
                "reason": self.risk.halt_reason,
            }
        report = self.analyst.analyse(symbol, closes)
        holding = self.execution.broker.positions.get(symbol, D("0")) > 0
        signal = self.strategist.decide(report, holding)
        entry = {
            "symbol": symbol,
            "trend": report.trend,
            "price": str(report.last_price),
            "signal": signal.side,
            "reason": signal.reason,
        }
        if signal.side is None:
            entry["action"] = "flat"
            self.log.append(entry)
            return entry
        decision = self.risk.evaluate(signal)
        entry["risk"] = decision.reason
        if not decision.approved:
            entry["action"] = "rejected"
            self.log.append(entry)
            return entry
        # Real money stays off unless explicitly allowed; otherwise paper.
        if mode == "live" and self.config.live_allowed():
            entry["action"] = "live_prepared"
            entry["live"] = self.execution.prepare_live(decision, signal)
        else:
            if mode == "live":
                entry["note"] = "Live gesperrt -> Paper ausgeführt"
            fill = self.execution.execute_paper(decision, signal, report.last_price)
            self.reviewer.record(fill)
            entry["action"] = "paper_filled"
            entry["fill"] = fill
        self.log.append(entry)
        return entry
