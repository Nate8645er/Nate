"""Terminal live ticker over the Jarvis Ultra mega organization.

Run from the project root::

    python -m jarvis_ultra.live_ticker --ticks 20 --interval 0.5

Every event is derived deterministically from ``--seed`` and the tick
number, so the same invocation always replays the same feed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from jarvis_ultra.catalog import all_plugins, all_skills, all_tools, loadout_summary
from jarvis_ultra.mega_org import (
    DEVELOPERS_PER_COMPANY,
    EMPLOYEES_PER_COMPANY,
    _number,
    _pick,
    company,
    format_big,
    org_totals,
    sample_employees,
)

EVENT_TYPES: tuple[str, ...] = (
    "einstellung",
    "deployment",
    "skill_aktiviert",
    "plugin_geladen",
    "tool_ausgefuehrt",
    "unternehmen_gegruendet",
    "umsatz_meldung",
    "befoerderung",
)

AGGREGATE_EVERY = 10

_COLORS = {
    "einstellung": "\x1b[32m",
    "deployment": "\x1b[36m",
    "skill_aktiviert": "\x1b[35m",
    "plugin_geladen": "\x1b[34m",
    "tool_ausgefuehrt": "\x1b[33m",
    "unternehmen_gegruendet": "\x1b[96m",
    "umsatz_meldung": "\x1b[92m",
    "befoerderung": "\x1b[93m",
}
_RESET = "\x1b[0m"


def build_event(tick: int, slot: int, seed: int, depth: int) -> dict[str, Any]:
    """Build one deterministic ticker event for a tick and slot."""

    key = (seed, "event", tick, slot)
    event_type = _pick(EVENT_TYPES, *key)
    event_depth = 1 + _number(depth, *key, "depth")
    person = sample_employees(1, depth=event_depth, seed=seed * 100_003 + tick * 101 + slot)[0]
    firm = company(person["path"], seed=seed)
    plugins, skills, tools = all_plugins(), all_skills(), all_tools()
    if event_type == "einstellung":
        text = (
            f"EINSTELLUNG · {person['name']} ({person['role']}) tritt {firm['name']} bei — "
            f"Loadout sofort aktiv: {loadout_summary()}"
        )
    elif event_type == "deployment":
        version = f"v{1 + _number(9, *key, 'maj')}.{_number(30, *key, 'min')}.{_number(100, *key, 'patch')}"
        text = f"DEPLOYMENT · {firm['name']}: Release {version} durch {person['name']} ({person['role']})"
    elif event_type == "skill_aktiviert":
        skill = _pick(tuple(skills), *key, "skill")
        text = f"SKILL AKTIVIERT · {person['name']} nutzt Skill '{skill}' bei {firm['name']}"
    elif event_type == "plugin_geladen":
        plugin = _pick(tuple(plugins), *key, "plugin")
        text = f"PLUGIN GELADEN · '{plugin}' bei {firm['name']} durch {person['name']}"
    elif event_type == "tool_ausgefuehrt":
        tool = _pick(tuple(tools), *key, "tool")
        text = f"TOOL AUSGEFÜHRT · {person['name']} startet Tool '{tool}' ({firm['name']})"
    elif event_type == "unternehmen_gegruendet":
        text = (
            f"GRÜNDUNG · {person['name']} gründet {firm['name']} — "
            f"{format_big(EMPLOYEES_PER_COMPANY)} Mitarbeiter, "
            f"{format_big(DEVELOPERS_PER_COMPANY)} Developer"
        )
    elif event_type == "umsatz_meldung":
        text = f"UMSATZ · {firm['name']} meldet {person['kpis']['umsatz_eur']:,} EUR heute".replace(",", ".")
    else:
        new_role = _pick(("CTO", "CEO", "Chief AI Officer", "VP Engineering", "Head of Research"), *key, "promo")
        text = f"BEFÖRDERUNG · {person['name']} wird {new_role} bei {firm['name']}"
    return {
        "tick": tick,
        "type": event_type,
        "employee_id": person["id"],
        "employee": person["name"],
        "role": person["role"],
        "company_id": firm["id"],
        "company": firm["name"],
        "depth": event_depth,
        "text": text,
    }


def aggregate_lines(depth: int) -> list[str]:
    """Return the German aggregate block for the configured depth."""

    totals = org_totals(depth)
    return [
        f"═══ MEGA-ORG GESAMTSTAND (bis Tiefe {depth}) ═══",
        f"  Mitarbeiter:      {format_big(totals['total_employees'])}",
        f"  Unternehmen:      {format_big(totals['total_companies'])}",
        f"  Developer:        {format_big(totals['total_developers'])}",
        f"  Mitglieder ges.:  {format_big(totals['total_members'])}",
        f"  Loadout-Items:    {format_big(totals['total_loadout_items'])}",
        f"  Pro Kopf:         {loadout_summary()}",
    ]


def run_ticker(ticks: int, interval: float, seed: int, depth: int, as_json: bool, stream: Any = None) -> int:
    """Run the ticker loop; ``ticks == 0`` means run until interrupted."""

    out = stream if stream is not None else sys.stdout
    use_color = as_json is False and hasattr(out, "isatty") and out.isatty()
    tick = 0
    try:
        while ticks == 0 or tick < ticks:
            events = [build_event(tick, slot, seed, depth) for slot in range(1 + _number(3, seed, "count", tick))]
            for event in events:
                if as_json:
                    print(json.dumps(event, ensure_ascii=False), file=out)
                else:
                    prefix = f"[TICK {tick:04d}]"
                    color = _COLORS.get(event["type"], "") if use_color else ""
                    reset = _RESET if color else ""
                    print(f"{prefix} {color}{event['text']}{reset}  [{event['employee_id']}]", file=out)
            if not as_json and tick > 0 and tick % AGGREGATE_EVERY == 0:
                for line in aggregate_lines(depth):
                    print(line, file=out)
            tick += 1
            if interval > 0:
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
    if not as_json:
        for line in aggregate_lines(depth):
            print(line, file=out)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the live ticker."""

    parser = argparse.ArgumentParser(prog="jarvis_ultra.live_ticker", description="Jarvis Ultra Mega-Org Live-Ticker")
    parser.add_argument("--ticks", type=int, default=20, help="Anzahl Ticks (0 = endlos)")
    parser.add_argument("--interval", type=float, default=0.5, help="Sekunden zwischen Ticks")
    parser.add_argument("--seed", type=int, default=0, help="Deterministischer Seed")
    parser.add_argument("--depth", type=int, default=3, help="Org-Tiefe für Events und Gesamtstand")
    parser.add_argument("--json", action="store_true", help="Ein JSON-Event pro Zeile ausgeben")
    args = parser.parse_args(argv)
    if args.ticks < 0:
        parser.error("--ticks must be >= 0")
    if args.depth < 1:
        parser.error("--depth must be >= 1")
    return run_ticker(args.ticks, args.interval, args.seed, args.depth, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
