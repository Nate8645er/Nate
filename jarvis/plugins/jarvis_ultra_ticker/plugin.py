"""Open.Jarvis plugin exposing the Jarvis Ultra mega-org live ticker."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_FALLBACK = "Jarvis Ultra Kern nicht gefunden — jarvis_ultra Paket fehlt."


def _ultra() -> Any:
    """Import the sibling jarvis_ultra package lazily and safely."""

    project_root = str(Path(__file__).resolve().parents[2])
    if project_root not in sys.path:
        sys.path.append(project_root)
    try:
        import jarvis_ultra
    except ImportError:
        return None
    return jarvis_ultra


def _notify(context: Any, message: str, level: str = "info") -> None:
    """Notify without ever raising out of a lifecycle hook."""

    try:
        context.notify(message, level)
    except Exception:
        pass


def on_load(context: Any) -> None:
    """Register the ticker commands."""

    try:
        for name, description in (
            ("ticker", "Live-Ticker Burst über die Mega-Organisation"),
            ("mega org status", "Gesamtstand der Mega-Organisation"),
            ("loadout", "Voller Plugin/Skill/Tool Loadout"),
        ):
            context.register_command(name, {"description": description})
    except Exception:
        pass


def on_enable(context: Any) -> None:
    """Announce readiness."""

    ultra = _ultra()
    if ultra is None:
        _notify(context, _FALLBACK, "warning")
        return
    _notify(context, f"Mega-Org Live-Ticker aktiv — {ultra.loadout_summary()}")


def on_command(command: str, context: Any) -> None:
    """Answer ticker, status, and loadout commands."""

    lowered = str(command).lower()
    if not any(term in lowered for term in ("ticker", "mega org", "status", "loadout")):
        return
    ultra = _ultra()
    if ultra is None:
        _notify(context, _FALLBACK, "warning")
        return
    from jarvis_ultra.live_ticker import aggregate_lines, build_event

    if "loadout" in lowered:
        _notify(context, ultra.loadout_summary())
        return
    if "ticker" in lowered and "status" not in lowered:
        for slot in range(3):
            _notify(context, build_event(0, slot, seed=0, depth=3)["text"])
        totals = ultra.org_totals(3)
        _notify(context, f"Mitglieder gesamt (Tiefe 3): {ultra.format_big(totals['total_members'])}")
        return
    for line in aggregate_lines(3):
        _notify(context, line)


def on_shutdown(context: Any) -> None:
    """Say goodbye politely."""

    _notify(context, "Mega-Org Live-Ticker beendet.")
