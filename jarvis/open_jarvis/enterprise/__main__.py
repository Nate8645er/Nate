"""Terminal-Live-Ticker des JARVIS Enterprise OS.

Aufruf::

    python3 -m open_jarvis.enterprise [--ticks N] [--interval SEK]
                                      [--seed N] [--summary]

``--ticks 0`` (oder weggelassen) laeuft endlos, bis Strg+C gedrueckt wird.
``--summary`` gibt nur die globalen Kennzahlen als JSON aus.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from open_jarvis.enterprise.live_ticker import DEFAULT_SEED, LiveTicker
from open_jarvis.enterprise.workforce import workforce_summary


def _fmt_de(value: int) -> str:
    """Ganzzahl mit deutschen Tausendertrennpunkten formatieren."""

    return f"{value:,}".replace(",", ".")


def _print_header(seed: int, ticks: int, interval: float) -> None:
    """Kopfzeilen mit den globalen Kennzahlen ausgeben."""

    summary = workforce_summary()
    line = "=" * 78
    print(line)
    print("  JARVIS ENTERPRISE — LIVE-TICKER")
    print(line)
    print(f"  Mitarbeiter direkt:          {_fmt_de(summary['employees_direct'])}")
    print(f"  Mitarbeiter je Unternehmen:  {_fmt_de(summary['company_employees'])}")
    print(f"  Entwickler je Unternehmen:   {_fmt_de(summary['company_developers'])}")
    print(f"  Entwickler gesamt:           {_fmt_de(summary['total_developers'])}")
    print(f"  Gesamt-Workforce:            {_fmt_de(summary['total_workforce'])}")
    print(
        f"  Katalog: {summary['skills']} Skills | {summary['plugins']} Plugins | "
        f"{summary['tools']} Tools (je {summary['skill_categories']} Kategorien)"
    )
    ticks_label = "endlos" if ticks <= 0 else _fmt_de(ticks)
    print(f"  Seed: {seed} | Intervall: {interval}s | Ticks: {ticks_label}")
    print("-" * 78)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Kommandozeilen-Argumente des Live-Tickers parsen."""

    parser = argparse.ArgumentParser(
        prog="python3 -m open_jarvis.enterprise",
        description="JARVIS Enterprise Live-Ticker (deterministisch, offline).",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=0,
        help="Anzahl Events (0 = endlos, Standard: 0)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Pause zwischen Events in Sekunden (Standard: 1.0)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=f"Seed der Event-Sequenz (Standard: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="nur die globalen Kennzahlen als JSON ausgeben",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Einstiegspunkt des Terminal-Live-Tickers."""

    args = _parse_args(argv)

    if args.summary:
        print(json.dumps(workforce_summary(), ensure_ascii=False, indent=2))
        return 0

    ticker = LiveTicker(seed=args.seed)

    try:
        _print_header(ticker.seed, args.ticks, args.interval)
        emitted = 0
        while args.ticks <= 0 or emitted < args.ticks:
            event = ticker.tick()
            emitted += 1
            print(f"#{event['tick']:>6}  {event['badge']}  {event['text']}", flush=True)
            if args.interval > 0:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        stats = ticker.aggregate_stats()
        print()
        print(
            f"Live-Ticker beendet nach {_fmt_de(int(stats['ticks']))} Events "
            f"({_fmt_de(int(stats['unique_employees']))} Mitarbeiter gesehen)."
        )
        return 0
    except BrokenPipeError:
        # Lesende Seite (z. B. `| head`) hat die Pipe geschlossen — kein Fehler.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
