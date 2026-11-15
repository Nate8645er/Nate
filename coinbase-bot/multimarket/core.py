"""Core data model and engines for the multi-market extension.

Dependency-free. Real execution stays off: the only broker here is a paper
broker. Market-cap categorisation, memecoin risk scoring and the liquidity
model are honest about missing data (UNKNOWN, not SAFE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# --------------------------------------------------------------------------
# Token model + market-cap categories
# --------------------------------------------------------------------------


class MarketCapCategory(Enum):
    CAT1_OVER_100M = "über 100M USD"
    CAT2_10M_100M = "10–100M USD"
    CAT3_1M_10M = "1–10M USD"
    CAT4_500K_1M = "500k–1M USD"
    CAT5_100K_500K = "100k–500k USD"
    CAT6_UNDER_100K = "unter 100k USD"
    UNKNOWN = "unbekannt"


@dataclass(frozen=True)
class Token:
    address: str
    symbol: str
    name: str
    network: str
    source: str
    created_at: Optional[str] = None
    price_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    fdv_usd: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    liquidity_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    trades_24h: Optional[int] = None
    buyers_24h: Optional[int] = None
    sellers_24h: Optional[int] = None
    holders: Optional[int] = None
    top_holder_pct: Optional[float] = None
    price_change_24h_pct: Optional[float] = None
    pool_address: Optional[str] = None

    def dedup_key(self) -> str:
        return f"{self.network}:{self.address}".lower()


def categorize_market_cap(mc_usd: Optional[float]) -> MarketCapCategory:
    if mc_usd is None or mc_usd <= 0:
        return MarketCapCategory.UNKNOWN
    if mc_usd >= 100_000_000:
        return MarketCapCategory.CAT1_OVER_100M
    if mc_usd >= 10_000_000:
        return MarketCapCategory.CAT2_10M_100M
    if mc_usd >= 1_000_000:
        return MarketCapCategory.CAT3_1M_10M
    if mc_usd >= 500_000:
        return MarketCapCategory.CAT4_500K_1M
    if mc_usd >= 100_000:
        return MarketCapCategory.CAT5_100K_500K
    return MarketCapCategory.CAT6_UNDER_100K


def valuation(token: Token) -> dict:
    """Prefer true market cap (circulating supply). Fall back to FDV, but mark
    the valuation uncertain when circulating supply is unknown. Low market cap
    is never, by itself, a buy signal — this only classifies."""
    mc = token.market_cap_usd
    uncertain = False
    basis = "market_cap"
    if mc is None or mc <= 0:
        mc = token.fdv_usd
        basis = "fdv"
        uncertain = True
    if token.circulating_supply is None:
        uncertain = True
    return {
        "value_usd": mc,
        "basis": basis,
        "uncertain": uncertain,
        "category": categorize_market_cap(mc),
        "fdv_usd": token.fdv_usd,
    }


# --------------------------------------------------------------------------
# Memecoin risk analysis
# --------------------------------------------------------------------------


class RiskLevel(Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RiskReport:
    level: RiskLevel
    veto: bool
    sell_feasible: Optional[bool]
    flags: list
    notes: list


@dataclass
class OnChain:
    """On-chain facts a caller may supply (from an RPC/scanner). Missing -> UNKNOWN."""

    mint_authority_active: Optional[bool] = None
    freeze_authority_active: Optional[bool] = None
    honeypot: Optional[bool] = None  # True = sells blocked
    token2022_transfer_fee: Optional[bool] = None
    top_holder_pct: Optional[float] = None
    dev_holding_pct: Optional[float] = None
    wash_trading_suspected: Optional[bool] = None
    sell_tax_pct: Optional[float] = None


def assess_memecoin_risk(
    token: Token,
    onchain: Optional[OnChain] = None,
    min_exit_liquidity_usd: float = 5_000.0,
) -> RiskReport:
    """Return a risk report. Missing data yields UNKNOWN, never SAFE. Critical
    conditions (honeypot, active mint/freeze authority, no exit liquidity,
    extreme sell tax) set veto=True for a binding RiskManager stop."""
    flags: list = []
    notes: list = []
    oc = onchain or OnChain()

    sell_feasible: Optional[bool]
    liq = token.liquidity_usd
    if oc.honeypot is True:
        sell_feasible = False
        flags.append("HONEYPOT")
    elif liq is None:
        sell_feasible = None
        notes.append("Exit-Liquidität unbekannt")
    elif liq < min_exit_liquidity_usd:
        sell_feasible = False
        flags.append("NO_EXIT_LIQUIDITY")
    else:
        sell_feasible = True

    if oc.mint_authority_active is True:
        flags.append("MINT_AUTHORITY_ACTIVE")
    if oc.freeze_authority_active is True:
        flags.append("FREEZE_AUTHORITY_ACTIVE")
    if oc.sell_tax_pct is not None and oc.sell_tax_pct >= 20:
        flags.append("HIGH_SELL_TAX")
    conc = oc.top_holder_pct if oc.top_holder_pct is not None else token.top_holder_pct
    if conc is not None and conc >= 50:
        flags.append("TOP_HOLDER_CONCENTRATION")
    if oc.dev_holding_pct is not None and oc.dev_holding_pct >= 20:
        flags.append("DEV_CONCENTRATION")
    if oc.token2022_transfer_fee is True:
        flags.append("TOKEN2022_TRANSFER_FEE")
    if oc.wash_trading_suspected is True:
        flags.append("WASH_TRADING")

    critical = {
        "HONEYPOT",
        "NO_EXIT_LIQUIDITY",
        "MINT_AUTHORITY_ACTIVE",
        "FREEZE_AUTHORITY_ACTIVE",
        "HIGH_SELL_TAX",
    }
    high = {
        "TOP_HOLDER_CONCENTRATION",
        "DEV_CONCENTRATION",
        "TOKEN2022_TRANSFER_FEE",
        "WASH_TRADING",
    }

    observed = sum(1 for v in vars(oc).values() if v is not None) + (
        1 if liq is not None else 0
    )

    if any(f in critical for f in flags):
        level = RiskLevel.CRITICAL
    elif observed == 0:
        level = RiskLevel.UNKNOWN
        notes.append("Keine On-Chain-Daten verfügbar -> UNKNOWN (nicht SAFE)")
    elif any(f in high for f in flags):
        level = RiskLevel.HIGH
    elif flags:
        level = RiskLevel.CAUTION
    elif sell_feasible is True and observed >= 2:
        level = RiskLevel.SAFE
    else:
        level = RiskLevel.UNKNOWN

    veto = level == RiskLevel.CRITICAL or sell_feasible is False
    return RiskReport(level, veto, sell_feasible, flags, notes)


def should_veto(report: RiskReport) -> bool:
    """Binding: the RiskManager must refuse a token whose report vetoes."""
    return report.veto


# --------------------------------------------------------------------------
# Adapter status registry
# --------------------------------------------------------------------------


class AdapterStatus(Enum):
    READ_ONLY = "READ ONLY"
    PAPER = "PAPER"
    LIVE_BLOCKED = "LIVE BLOCKED"
    LIVE_READY = "LIVE READY"  # technically prepared only; never auto-executes


@dataclass(frozen=True)
class Adapter:
    name: str
    market: str
    status: AdapterStatus
    note: str


ADAPTERS = [
    Adapter(
        "coinbase_spot",
        "Coinbase Advanced Trade",
        AdapterStatus.PAPER,
        "Verifizierter Connector vorhanden; Live separat gesperrt (LIVE_BLOCKED).",
    ),
    Adapter(
        "solana_dex_paper",
        "Solana DEX",
        AdapterStatus.PAPER,
        "Nur Simulation; keine Wallet-Signatur, keine Keys.",
    ),
    Adapter(
        "jupiter_quote",
        "Jupiter",
        AdapterStatus.READ_ONLY,
        "Quote/Simulation; keine Ausführung.",
    ),
    Adapter(
        "pumpfun_market",
        "Pump.fun / PumpSwap",
        AdapterStatus.READ_ONLY,
        "Nur Marktdaten.",
    ),
]


# --------------------------------------------------------------------------
# Liquidity-aware micro-cap paper broker
# --------------------------------------------------------------------------


@dataclass
class FillResult:
    status: str  # "filled" | "partial" | "no_trade" | "failed"
    filled_usd: float
    avg_price: float
    slippage_pct: float
    price_impact_pct: float
    fee_usd: float
    reason: str = ""


class MicroCapPaperBroker:
    """Realistic paper execution for thin markets. Position size is capped by
    pool liquidity; slippage grows with the order's share of liquidity (price
    impact); orders beyond the slippage tolerance fail; too little liquidity is
    NO TRADE. Paper gains cannot come from perfect fills."""

    def __init__(
        self,
        *,
        max_pool_fraction: float = 0.02,
        min_liquidity_usd: float = 5_000.0,
        base_spread_pct: float = 0.3,
        taker_fee_pct: float = 0.25,
        priority_fee_usd: float = 0.02,
        max_slippage_pct: float = 5.0,
        impact_coeff: float = 1.0,
    ):
        self.max_pool_fraction = max_pool_fraction
        self.min_liquidity_usd = min_liquidity_usd
        self.base_spread_pct = base_spread_pct
        self.taker_fee_pct = taker_fee_pct
        self.priority_fee_usd = priority_fee_usd
        self.max_slippage_pct = max_slippage_pct
        self.impact_coeff = impact_coeff

    def estimate(
        self,
        side: str,
        requested_usd: float,
        price: float,
        liquidity_usd: Optional[float],
        tolerated_slippage_pct: Optional[float] = None,
    ) -> FillResult:
        tol = (
            self.max_slippage_pct
            if tolerated_slippage_pct is None
            else tolerated_slippage_pct
        )
        if liquidity_usd is None or liquidity_usd < self.min_liquidity_usd:
            return FillResult(
                "no_trade",
                0.0,
                price,
                0.0,
                0.0,
                0.0,
                reason=f"Liquidität {liquidity_usd} < Minimum {self.min_liquidity_usd}",
            )
        cap_usd = liquidity_usd * self.max_pool_fraction
        fill_usd = min(requested_usd, cap_usd)
        partial = fill_usd < requested_usd
        impact_pct = self.impact_coeff * (fill_usd / liquidity_usd) * 100
        slippage_pct = self.base_spread_pct + impact_pct
        if slippage_pct > tol:
            return FillResult(
                "failed",
                0.0,
                price,
                slippage_pct,
                impact_pct,
                0.0,
                reason=f"Slippage {slippage_pct:.2f}% über Toleranz {tol:.2f}%",
            )
        sign = 1 if side.upper() == "BUY" else -1
        avg_price = price * (1 + sign * slippage_pct / 100)
        fee = fill_usd * self.taker_fee_pct / 100 + self.priority_fee_usd
        return FillResult(
            "partial" if partial else "filled",
            fill_usd,
            avg_price,
            slippage_pct,
            impact_pct,
            fee,
            reason="Teilausführung durch Liquiditätslimit" if partial else "",
        )


# --------------------------------------------------------------------------
# Virtual portfolios
# --------------------------------------------------------------------------


@dataclass
class Portfolio:
    name: str
    market: str
    cash_usd: float
    trades: list = field(default_factory=list)

    def record(self, entry: dict) -> None:
        self.trades.append(entry)

    def metrics(self) -> dict:
        pnls = [t["pnl"] for t in self.trades if "pnl" in t]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gp, gl = sum(wins), -sum(losses)
        failed = sum(
            1 for t in self.trades if t.get("status") in ("failed", "no_trade")
        )
        return {
            "name": self.name,
            "market": self.market,
            "trades": len(pnls),
            "win_rate_pct": (len(wins) / len(pnls) * 100) if pnls else 0.0,
            "profit_factor": (gp / gl) if gl > 0 else (999.0 if gp > 0 else 0.0),
            "net_pnl": sum(pnls),
            "failed_or_no_trade": failed,
        }
