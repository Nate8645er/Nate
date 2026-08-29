"""Deterministischer Live-Ticker des JARVIS Enterprise OS.

Erzeugt Event-Meldungen ueber die 1.000.000.000.000 direkten Mitarbeiter
und deren Unternehmen. Jedes Event wird ausschliesslich aus ``(seed, tick)``
abgeleitet (SplitMix64-Runden) — zwei Ticker mit demselben Seed liefern
exakt dieselbe Event-Sequenz.
"""

from __future__ import annotations

from typing import Iterator

from open_jarvis.enterprise import catalog
from open_jarvis.enterprise.workforce import (
    EMPLOYEES_DIRECT,
    MASK,
    TOTAL_WORKFORCE,
    employee_identity,
    mix64,
)

#: Fester Default-Seed (2026-07-12), wenn kein Seed uebergeben wird.
DEFAULT_SEED: int = 20260712

#: Reihenfolge der Event-Typen — Index == Template-Nummer aus der SPEC minus 1.
EVENT_TYPES: tuple[str, ...] = (
    "feature",
    "onboarding",
    "projekt",
    "produktivitaet",
    "skill",
    "plugin",
    "tool",
    "sync",
    "partnerschaft",
    "auszeichnung",
)


def _fmt_de(value: int) -> str:
    """Ganzzahl mit deutschen Tausendertrennpunkten formatieren."""

    return f"{value:,}".replace(",", ".")


class LiveTicker:
    """Deterministischer Event-Ticker fuer die JARVIS Enterprise-Workforce.

    :param seed: Start-Seed der Event-Sequenz. ``None`` verwendet den
        festen Default-Seed :data:`DEFAULT_SEED`.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.seed: int = DEFAULT_SEED if seed is None else seed
        self._tick: int = 0
        self._type_counts: dict[str, int] = {name: 0 for name in EVENT_TYPES}
        self._seen_employees: set[int] = set()

    # -- Event-Ableitung ---------------------------------------------------

    def event_for_tick(self, tick: int) -> dict[str, object]:
        """Event fuer eine Tick-Nummer berechnen (ohne internen Zustand)."""

        e = mix64((self.seed & MASK) ^ mix64(tick))
        emp_id = (e % EMPLOYEES_DIRECT) + 1
        t_hash = mix64(e)
        e_type = t_hash % len(EVENT_TYPES)
        d1 = mix64(t_hash)
        d2 = mix64(d1)
        d3 = mix64(d2)

        emp = employee_identity(emp_id)
        text = self._render(e_type, emp, d1, d2, d3)

        return {
            "tick": tick,
            "employee_id": emp_id,
            "badge": emp["badge"],
            "text": text,
            "type": EVENT_TYPES[e_type],
        }

    def _render(
        self,
        e_type: int,
        emp: dict[str, object],
        d1: int,
        d2: int,
        d3: int,
    ) -> str:
        """Event-Text fuer einen Template-Typ deterministisch erzeugen."""

        name = emp["name"]
        role = emp["role"]
        department = emp["department"]
        company = emp["company_name"]

        if e_type == 0:
            return (
                f"🚀 {name} ({role}, {department}) hat bei {company} "
                f"ein neues Feature ausgeliefert"
            )
        if e_type == 1:
            n = (d1 % 99_000) + 1_000
            return f"🏢 {company}: {_fmt_de(n)} neue Entwickler im Onboarding"
        if e_type == 2:
            code = f"PRJ-{d1 % 0x1000000:06X}"
            return f"✅ {name} hat Projekt {code} erfolgreich abgeschlossen"
        if e_type == 3:
            pct = (d1 % 48) + 2
            return f"📈 {company} meldet +{pct}% Produktivität in {department}"
        if e_type == 4:
            skill = catalog.all_skills()[d1 % 200]
            return f'🧠 {name} hat Skill "{skill}" auf Level MAX zertifiziert'
        if e_type == 5:
            plugin = catalog.all_plugins()[d1 % 128]
            return f'🔌 Plugin "{plugin}" bei {company} konzernweit ausgerollt'
        if e_type == 6:
            tool = catalog.all_tools()[d1 % 192]
            major = (d2 % 9) + 1
            minor = d3 % 100
            return (
                f'🛠️ Tool "{tool}" auf Version {major}.{minor} '
                f"aktualisiert bei {company}"
            )
        if e_type == 7:
            k = (d1 % 900_000_000) + 100_000_000
            return (
                f"🛰️ JARVIS synchronisiert {_fmt_de(k)} Unternehmens-Knoten "
                f"im Orbit-Cluster"
            )
        if e_type == 8:
            partner_id = (d1 % EMPLOYEES_DIRECT) + 1
            if partner_id == emp["id"]:
                partner_id = (partner_id % EMPLOYEES_DIRECT) + 1
            company2 = employee_identity(partner_id)["company_name"]
            return f"🤝 {company} startet Partnerschaft mit {company2}"
        return f'🏆 {name} zum "Mitarbeiter des Zyklus" in {department} ernannt'

    # -- Oeffentliche API --------------------------------------------------

    def tick(self) -> dict[str, object]:
        """Naechstes Event erzeugen und interne Statistik fortschreiben."""

        self._tick += 1
        event = self.event_for_tick(self._tick)
        self._type_counts[str(event["type"])] += 1
        self._seen_employees.add(int(event["employee_id"]))  # type: ignore[arg-type]
        return event

    def stream(self, count: int) -> Iterator[dict[str, object]]:
        """Genau ``count`` aufeinanderfolgende Events als Generator liefern."""

        for _ in range(count):
            yield self.tick()

    def aggregate_stats(self) -> dict[str, object]:
        """Aggregierte Statistik ueber alle bisher erzeugten Events."""

        return {
            "seed": self.seed,
            "ticks": self._tick,
            "events_by_type": dict(self._type_counts),
            "unique_employees": len(self._seen_employees),
            "total_workforce": TOTAL_WORKFORCE,
        }
