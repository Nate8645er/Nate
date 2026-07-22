"""Deterministic procedural simulation of the Jarvis Ultra mega organization.

The organization is never materialized: with 10**12 direct employees, each
owning a company that again has 10**12 employees and 10**12 developers, the
structure is infinite. Every entity is derived on demand from its address
path with sha256, so the same address always yields the same employee.

Address scheme: an employee is a tuple of indices. ``(7,)`` is direct
employee number 7 of Jarvis HQ, ``(7, 42)`` is employee number 42 of the
company owned by employee ``(7,)``, and so on to arbitrary depth.
"""

from __future__ import annotations

import hashlib
from typing import Any

from jarvis_ultra.catalog import full_loadout, loadout_size

EMPLOYEES_PER_COMPANY: int = 10**12
DEVELOPERS_PER_COMPANY: int = 10**12

FIRST_NAMES: tuple[str, ...] = (
    "Alexander", "Amira", "Anna", "Anton", "Aylin", "Ben", "Björn", "Carla",
    "Clara", "Daniel", "Deniz", "Elena", "Elif", "Emil", "Emma", "Fabian",
    "Felix", "Finn", "Frida", "Greta", "Hanna", "Henry", "Ida", "Jan",
    "Jana", "Jonas", "Julia", "Kai", "Katharina", "Lea", "Leon", "Lina",
    "Lukas", "Luisa", "Marie", "Malik", "Matteo", "Maya", "Mila", "Milan",
    "Mira", "Moritz", "Nadia", "Nele", "Nico", "Nina", "Noah", "Nora",
    "Omar", "Paul", "Paula", "Philipp", "Rania", "Rasmus", "Samira", "Sarah",
    "Selin", "Simon", "Sofia", "Talia", "Theo", "Tim", "Yara", "Zoe",
)

LAST_NAMES: tuple[str, ...] = (
    "Albrecht", "Arnold", "Bauer", "Baumann", "Becker", "Berger", "Brandt",
    "Braun", "Busch", "Dietrich", "Engel", "Fischer", "Frank", "Franke",
    "Fuchs", "Graf", "Groß", "Hartmann", "Hase", "Heller", "Herrmann",
    "Hoffmann", "Huber", "Jäger", "Kaiser", "Keller", "Klein", "Koch",
    "Köhler", "König", "Kraus", "Krüger", "Kuhn", "Lang", "Lehmann",
    "Lorenz", "Ludwig", "Maier", "Martin", "Meyer", "Möller", "Müller",
    "Neumann", "Otto", "Peters", "Pohl", "Richter", "Roth", "Sauer",
    "Schäfer", "Schmidt", "Schneider", "Scholz", "Schröder", "Schulz",
    "Schwarz", "Seidel", "Vogel", "Wagner", "Weber", "Winkler", "Wolf",
    "Ziegler", "Zimmermann",
)

ROLES: tuple[str, ...] = (
    "Chefarchitektin", "Chefarchitekt", "Principal Developer", "KI-Forscherin",
    "KI-Forscher", "Sicherheitschefin", "Sicherheitschef", "DevOps-Lead",
    "Datenwissenschaftlerin", "Datenwissenschaftler", "Produktdesignerin",
    "Produktdesigner", "QA-Direktorin", "QA-Direktor", "Plattform-Ingenieurin",
    "Plattform-Ingenieur", "Cloud-Strategin", "Cloud-Stratege",
    "Robotik-Spezialistin", "Robotik-Spezialist", "UX-Visionärin",
    "UX-Visionär", "Automatisierungs-Expertin", "Automatisierungs-Experte",
    "Systemdenkerin", "Systemdenker", "Release-Managerin", "Release-Manager",
    "Compiler-Virtuosin", "Compiler-Virtuose", "Quanten-Ingenieurin",
    "Quanten-Ingenieur", "Wachstums-Strategin", "Wachstums-Stratege",
    "Innovationsleiterin", "Innovationsleiter", "Sprachmodell-Trainerin",
    "Sprachmodell-Trainer", "Observability-Chefin", "Observability-Chef",
)

COMPANY_HEADS: tuple[str, ...] = (
    "Quantus", "Nova", "Helio", "Astra", "Vertex", "Nimbus", "Orbit",
    "Aurora", "Zenit", "Kern", "Pulsar", "Fluxon", "Vireo", "Solaris",
    "Titan", "Lumen", "Hyperion", "Atlas", "Neuron", "Cortex", "Vektor",
    "Delta", "Fusion", "Gravit", "Ionis", "Kinet", "Lyra", "Meridian",
    "Nexus", "Polaris", "Sigma", "Stratos",
)

COMPANY_CORES: tuple[str, ...] = (
    "Dynamics", "Systems", "Robotics", "Analytics", "Industries", "Labs",
    "Logic", "Networks", "Automation", "Intelligence", "Engineering",
    "Technologies", "Solutions", "Computing", "Mechatronik", "Software",
)

COMPANY_FORMS: tuple[str, ...] = ("AG", "GmbH", "SE", "KGaA")

_SCALE_WORDS: tuple[tuple[int, str], ...] = (
    (10**36, "Sextillion"),
    (10**33, "Quintilliarde"),
    (10**30, "Quintillion"),
    (10**27, "Quadrilliarde"),
    (10**24, "Quadrillion"),
    (10**21, "Trilliarde"),
    (10**18, "Trillion"),
    (10**15, "Billiarde"),
    (10**12, "Billion"),
    (10**9, "Milliarde"),
    (10**6, "Million"),
)


def _digest(*parts: Any) -> bytes:
    """Return a deterministic digest for an entity attribute."""

    key = ":".join(str(part) for part in parts)
    return hashlib.sha256(key.encode("utf-8")).digest()


def _pick(seq: tuple[str, ...], *parts: Any) -> str:
    """Pick a deterministic element of a sequence for the given key parts."""

    return seq[int.from_bytes(_digest(*parts), "big") % len(seq)]


def _number(limit: int, *parts: Any) -> int:
    """Return a deterministic integer in ``[0, limit)`` for the key parts."""

    return int.from_bytes(_digest(*parts), "big") % limit


def _path_id(path: tuple[int, ...]) -> str:
    """Return the dotted address string for a path."""

    return ".".join(str(index) for index in path)


def _validate_path(path: tuple[int, ...]) -> None:
    if not path:
        raise ValueError("path must contain at least one index")
    for index in path:
        if not 0 <= index < EMPLOYEES_PER_COMPANY:
            raise ValueError(f"index {index} outside 0..{EMPLOYEES_PER_COMPANY - 1}")


def employee(path: tuple[int, ...], seed: int = 0) -> dict[str, Any]:
    """Return the deterministic employee at an address path."""

    _validate_path(path)
    address = _path_id(path)
    first = _pick(FIRST_NAMES, seed, address, "first")
    last = _pick(LAST_NAMES, seed, address, "last")
    return {
        "id": f"E-{address}",
        "path": path,
        "depth": len(path),
        "name": f"{first} {last}",
        "role": _pick(ROLES, seed, address, "role"),
        "company_id": f"C-{address}",
        "loadout": full_loadout(),
        "kpis": {
            "commits_heute": 40 + _number(960, seed, address, "commits"),
            "deployments": 1 + _number(24, seed, address, "deploys"),
            "umsatz_eur": 1_000_000 + _number(999_000_000, seed, address, "umsatz"),
        },
    }


def company(path: tuple[int, ...], seed: int = 0) -> dict[str, Any]:
    """Return the company owned by the employee at an address path."""

    _validate_path(path)
    address = _path_id(path)
    head = _pick(COMPANY_HEADS, seed, address, "company-head")
    core = _pick(COMPANY_CORES, seed, address, "company-core")
    form = _pick(COMPANY_FORMS, seed, address, "company-form")
    return {
        "id": f"C-{address}",
        "name": f"{head} {core} {form}",
        "owner_id": f"E-{address}",
        "employees": EMPLOYEES_PER_COMPANY,
        "developers": DEVELOPERS_PER_COMPANY,
        "loadout": full_loadout(),
    }


def org_totals(depth: int) -> dict[str, int]:
    """Return exact big-integer aggregates for the org down to a depth.

    With ``N = EMPLOYEES_PER_COMPANY`` there are ``N**d`` employees at
    depth ``d`` (depth 1 are Jarvis HQ's direct employees). Every employee
    owns exactly one company, and every company employs ``D`` developers,
    so down to ``depth``::

        total_employees  = sum(N**d for d in 1..depth)
        total_companies  = total_employees
        total_developers = total_employees * D
        total_members    = 1 (Jarvis) + employees + developers

    Loadout totals multiply the member count by the catalog size.
    """

    if depth < 1:
        raise ValueError("depth must be >= 1")
    total_employees = sum(EMPLOYEES_PER_COMPANY**level for level in range(1, depth + 1))
    total_companies = total_employees
    total_developers = total_employees * DEVELOPERS_PER_COMPANY
    total_members = 1 + total_employees + total_developers
    return {
        "depth": depth,
        "total_employees": total_employees,
        "total_companies": total_companies,
        "total_developers": total_developers,
        "total_members": total_members,
        "total_loadout_items": total_members * loadout_size(),
    }


def sample_employees(n: int, depth: int = 1, seed: int = 0) -> list[dict[str, Any]]:
    """Return ``n`` deterministic pseudo-random employees at a depth."""

    if n < 0:
        raise ValueError("n must be >= 0")
    if depth < 1:
        raise ValueError("depth must be >= 1")
    samples: list[dict[str, Any]] = []
    for slot in range(n):
        path = tuple(
            _number(EMPLOYEES_PER_COMPANY, seed, "sample", slot, level)
            for level in range(depth)
        )
        samples.append(employee(path, seed=seed))
    return samples


def format_big(n: int) -> str:
    """Format a big integer German-style with a long-scale word when exact.

    Numbers below a million keep plain grouping. Larger numbers get a word
    ("1 Billion", "5 Quadrillionen") when they are a small multiple of a
    named power, otherwise a power-of-ten form like "≈ 10^36".
    """

    if n < 0:
        return f"-{format_big(-n)}"
    grouped = f"{n:,}".replace(",", ".")
    if n < 10**6:
        return grouped
    for scale, word in _SCALE_WORDS:
        if n >= scale and n % scale == 0 and n // scale < 1000:
            factor = n // scale
            plural = "" if factor == 1 else ("n" if word.endswith("e") else "en")
            return f"{factor} {word}{plural} ({grouped})"
    exponent = len(str(n)) - 1
    return f"≈ 10^{exponent} ({grouped})"
