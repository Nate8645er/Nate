"""Phase 10 tests: trading modes, absolute limits, and the eight-step team
meeting. No network, no real orders."""

from decimal import Decimal as D

import pytest

from trading_team import RiskConfig, RiskManager, paper_risk_config
from trading_team.meeting import Decision, hold_meeting
from trading_team.modes import AbsoluteLimits, ModeController, ModeError, TradingMode


def uptrend(n=60, start=100.0, step=0.5):
    return [D(str(start + i * step)) for i in range(n)]


def downtrend(n=60, start=130.0, step=0.5):
    return [D(str(start - i * step)) for i in range(n)]


def confirmed_limits():
    return AbsoluteLimits(total_capital_usdc=D("17.10"), max_daily_loss_usdc=D("2"),
                          max_total_loss_usdc=D("5"), max_slippage_pct=D("1"),
                          max_open_exposure_usdc=D("17.10"), confirmed=True)


# ---- modes ---------------------------------------------------------------


def test_default_mode_is_paper_and_autonomous_is_locked():
    c = ModeController(AbsoluteLimits())
    assert c.mode is TradingMode.PAPER
    with pytest.raises(ModeError, match="gesperrt"):
        c.set_mode(TradingMode.LIVE_AUTONOMOUS)


def test_live_manual_needs_confirmed_complete_limits():
    c = ModeController(AbsoluteLimits())
    with pytest.raises(ModeError, match="Risikolimits"):
        c.set_mode(TradingMode.LIVE_MANUAL)
    c2 = ModeController(confirmed_limits())
    c2.set_mode(TradingMode.LIVE_MANUAL)
    assert c2.mode is TradingMode.LIVE_MANUAL


def test_limits_can_only_be_tightened():
    lim = confirmed_limits()
    tighter = lim.tightened(total_capital_usdc=D("5"), max_daily_loss_usdc=D("1"))
    assert tighter.total_capital_usdc == D("5")
    looser = lim.tightened(total_capital_usdc=D("1000"))
    assert looser.total_capital_usdc == D("17.10")  # clamped, never raised
    with pytest.raises(ModeError):
        lim.tightened(confirmed=True)


def test_live_execution_needs_exact_approval_phrase():
    c = ModeController(confirmed_limits())
    c.set_mode(TradingMode.LIVE_MANUAL)
    ok, _ = c.may_execute_live("BUY", "BTC-USDC", "10.00", "LIVE BUY BTC-USDC 10.00")
    assert ok is True
    bad, reason = c.may_execute_live("BUY", "BTC-USDC", "10.00", "LIVE BUY BTC-USDC 17.00")
    assert bad is False and "Freigabe" in reason
    none, _ = c.may_execute_live("BUY", "BTC-USDC", "10.00", None)
    assert none is False


def test_paper_mode_never_allows_live_execution():
    c = ModeController(confirmed_limits())
    ok, reason = c.may_execute_live("BUY", "BTC-USDC", "5.00", "LIVE BUY BTC-USDC 5.00")
    assert ok is False and "PAPER" in reason


def test_emergency_stop_forces_paper_and_blocks_everything():
    c = ModeController(confirmed_limits())
    c.set_mode(TradingMode.LIVE_MANUAL)
    c.trigger_emergency_stop("manueller Not-Aus")
    assert c.mode is TradingMode.PAPER
    ok, reason = c.may_execute_live("BUY", "BTC-USDC", "5.00", "LIVE BUY BTC-USDC 5.00")
    assert ok is False and "Not-Aus" in reason
    with pytest.raises(ModeError, match="Not-Aus"):
        c.set_mode(TradingMode.LIVE_MANUAL)


def test_position_size_capped_by_capital_balance_and_exposure():
    c = ModeController(confirmed_limits())
    assert c.max_position_usdc(D("1000")) == D("17.10")      # capital ceiling
    assert c.max_position_usdc(D("4.00")) == D("4.00")       # real balance
    assert c.max_position_usdc(D("1000"), D("17.10")) == D("0")  # fully exposed


# ---- meeting -------------------------------------------------------------


def run(closes, *, risk=None, controller=None, available=D("17.10"), approval=None):
    return hold_meeting("BTC-USDC", closes,
                        risk=risk or RiskManager(paper_risk_config()),
                        controller=controller or ModeController(AbsoluteLimits()),
                        available_usdc=available, approval=approval)


def test_meeting_records_every_agent_and_is_traceable():
    res = run(uptrend())
    agents = {s.agent for s in res.statements}
    assert "MarketAnalyst" in agents and "Strategist" in agents
    assert "RiskManager" in agents
    assert all(s.rationale for s in res.statements)  # every statement is justified


def test_risk_veto_blocks_the_order_and_ends_the_meeting():
    tiny = RiskManager(RiskConfig(allocated_capital_usdc=D("0.10"), min_order_usdc=D("1")))
    res = run(uptrend(), risk=tiny)
    if res.consensus == "BUY" and res.agreed:
        assert res.final is Decision.VETO
        assert res.prepared_order is None


def test_meeting_accepts_no_trade_without_consensus():
    res = run(downtrend())
    assert res.final in (Decision.NO_TRADE, Decision.VETO, Decision.SELL)
    if res.final is Decision.NO_TRADE:
        assert res.prepared_order is None


def test_paper_mode_prepares_but_never_executes():
    res = run(uptrend())
    assert res.executed is False
    if res.prepared_order:
        assert "PAPER" in res.execution_note


def test_order_size_never_exceeds_real_balance():
    res = run(uptrend(), available=D("3.00"))
    if res.prepared_order:
        assert D(res.prepared_order["quote_size"]) <= D("3.00")


def test_order_below_minimum_is_no_trade():
    res = run(uptrend(), available=D("0.50"))
    assert res.prepared_order is None
    assert res.final is Decision.NO_TRADE


def test_live_manual_with_matching_approval_opens_the_gate():
    c = ModeController(confirmed_limits())
    c.set_mode(TradingMode.LIVE_MANUAL)
    dry = run(uptrend(), controller=c)
    if dry.prepared_order:
        phrase = dry.prepared_order["approval_phrase"]
        res = run(uptrend(), controller=c, approval=phrase)
        assert "Freigegeben" in res.execution_note
        # still not sent from inside the meeting
        assert res.executed is False


def test_emergency_stop_closes_the_gate_in_the_meeting():
    c = ModeController(confirmed_limits())
    c.set_mode(TradingMode.LIVE_MANUAL)
    c.trigger_emergency_stop("Test")
    res = run(uptrend(), controller=c)
    assert res.executed is False
    # If the meeting ever reaches the gate, the gate must be shut.
    gate = [s for s in res.statements if s.agent == "Gate"]
    if gate:
        assert gate[0].decision is Decision.NO_TRADE
        assert "Not-Aus" in res.execution_note


def test_meeting_serialises_for_the_dashboard():
    d = run(uptrend()).to_dict()
    assert "statements" in d and "final" in d
    assert all({"step", "agent", "decision", "rationale"} <= set(s) for s in d["statements"])
