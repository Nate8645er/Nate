"""Deterministische Workforce-Engine des JARVIS Enterprise OS.

Bildet 1.000.000.000.000 virtuelle Mitarbeiter ab ("1000 Milliarden"), die
direkt im JARVIS Live-Ticker arbeiten. Jeder dieser Mitarbeiter fuehrt
zusaetzlich ein eigenes Unternehmen mit 10**12 Mitarbeitern und einem
weiteren 10**12 starken Developer-Team.

Alle Ableitungen sind rein deterministisch (SplitMix64-Finalizer) und
benoetigen ausschliesslich die Python-Standardbibliothek. Die JavaScript-
Implementierung im Dashboard MUSS fuer dieselbe Mitarbeiter-ID identische
Ergebnisse liefern (siehe SPEC).
"""

from __future__ import annotations

from open_jarvis.enterprise import catalog

# ---------------------------------------------------------------------------
# Kennzahlen (Konstanten) — immer als Ausdruck berechnen, nie abtippen.
# ---------------------------------------------------------------------------

#: Mitarbeiter direkt im JARVIS Live-Ticker ("1000 Milliarden").
EMPLOYEES_DIRECT: int = 10**12

#: Mitarbeiterzahl jedes Mitarbeiter-Unternehmens.
COMPANY_EMPLOYEES: int = 10**12

#: Groesse des Developer-Teams jedes Mitarbeiter-Unternehmens.
COMPANY_DEVELOPERS: int = 10**12

#: Gesamte Workforce: direkte Mitarbeiter plus alle Unternehmens-Belegschaften.
TOTAL_WORKFORCE: int = EMPLOYEES_DIRECT + EMPLOYEES_DIRECT * (
    COMPANY_EMPLOYEES + COMPANY_DEVELOPERS
)

#: Gesamtzahl aller Entwickler in allen Mitarbeiter-Unternehmen.
TOTAL_DEVELOPERS: int = EMPLOYEES_DIRECT * COMPANY_DEVELOPERS

#: 64-Bit-Maske fuer die SplitMix64-Arithmetik.
MASK: int = (1 << 64) - 1

# ---------------------------------------------------------------------------
# Namenslisten (EXAKT diese Reihenfolge, 0-indiziert — siehe SPEC).
# ---------------------------------------------------------------------------

FIRST_NAMES: list[str] = [
    "Nova", "Aria", "Kai", "Lena", "Milo", "Zara", "Finn", "Nia",
    "Orion", "Maya", "Levi", "Sofia", "Elias", "Luna", "Noah", "Ida",
    "Juna", "Emil", "Ayla", "Ben", "Mira", "Theo", "Lia", "Jonas",
    "Elif", "Max", "Sara", "Adrian", "Yuna", "Felix", "Amara", "Nils",
]

LAST_NAMES: list[str] = [
    "Sterling", "Novak", "Berger", "Nakamura", "Almeida", "Kovacs", "Fischer", "Okafor",
    "Lindgren", "Petrov", "Haller", "Vega", "Tanaka", "Moreau", "Weiss", "Iversen",
    "Costa", "Duran", "Keller", "Osei", "Brandt", "Sato", "Nguyen", "Iqbal",
    "Meier", "Rossi", "Andersson", "Volkov", "Schmid", "Zhao", "Furrer", "Quandt",
]

ROLES: list[str] = [
    "Chief Executive Officer", "Chief Technology Officer", "Chief AI Officer",
    "Principal Engineer", "Staff Developer", "Senior Developer",
    "Full-Stack Developer", "Backend Developer", "Frontend Developer",
    "ML Engineer", "Data Scientist", "DevOps Engineer",
    "Security Engineer", "Cloud Architect", "Product Manager",
    "UX Designer", "QA Engineer", "Site Reliability Engineer",
    "Research Scientist", "Automation Engineer", "Growth Manager",
    "Finance Analyst", "Support Specialist", "Robotics Engineer",
]

DEPARTMENTS: list[str] = [
    "Engineering", "AI Research", "Security", "DevOps & Cloud",
    "Data & Analytics", "Design", "Produkt", "Marketing",
    "Sales", "Finance", "Legal", "HR & People",
    "Support", "Robotik", "Innovation", "Operations",
]

COMPANY_SUFFIXES: list[str] = [
    "Industries", "Technologies", "Dynamics", "Labs",
    "Systems", "Global", "Ventures", "Robotics",
    "Intelligence", "Networks", "Solutions", "Quantum",
    "Aerospace", "Digital", "Werke", "Group",
]


def mix64(x: int) -> int:
    """SplitMix64-Finalizer: deterministischer 64-Bit-Hash (siehe SPEC)."""

    x = (x + 0x9E3779B97F4A7C15) & MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return (z ^ (z >> 31)) & MASK


def _validate_employee_id(emp_id: int) -> None:
    """Prueft, dass die Mitarbeiter-ID im gueltigen Bereich 1..10**12 liegt."""

    if not isinstance(emp_id, int) or isinstance(emp_id, bool):
        raise ValueError(f"Mitarbeiter-ID muss eine ganze Zahl sein: {emp_id!r}")
    if emp_id < 1 or emp_id > EMPLOYEES_DIRECT:
        raise ValueError(
            f"Mitarbeiter-ID {emp_id} ausserhalb des gueltigen Bereichs "
            f"1..{EMPLOYEES_DIRECT}"
        )


def employee_identity(emp_id: int) -> dict[str, object]:
    """Leichtgewichtige Identitaet eines Mitarbeiters (ohne Katalog-Bloecke).

    Liefert nur die deterministisch abgeleiteten Kernfelder — nuetzlich fuer
    den Live-Ticker, der pro Event keine kompletten Katalog-Kopien braucht.
    """

    _validate_employee_id(emp_id)

    h1 = mix64(emp_id)
    h2 = mix64(h1)
    h3 = mix64(h2)
    h4 = mix64(h3)
    h5 = mix64(h4)
    h6 = mix64(h5)

    first = FIRST_NAMES[h1 % 32]
    last = LAST_NAMES[h2 % 32]
    role = ROLES[h3 % 24]
    department = DEPARTMENTS[h4 % 16]
    company_suffix = COMPANY_SUFFIXES[h5 % 16]
    specialization = catalog.all_skills()[h6 % 200]

    return {
        "id": emp_id,
        "first": first,
        "last": last,
        "name": f"{first} {last}",
        "badge": f"JRV-{str(emp_id).zfill(13)}",
        "role": role,
        "department": department,
        "specialization": specialization,
        "company_name": f"{first} {last} {company_suffix}",
    }


def _capability_block(categories: dict[str, list[str]]) -> dict[str, object]:
    """Zaehler + Kategorien-Zugriff fuer einen Katalog-Abschnitt."""

    return {
        "count": sum(len(items) for items in categories.values()),
        "categories": {name: list(items) for name, items in categories.items()},
    }


def employee(emp_id: int) -> dict[str, object]:
    """Vollstaendiger, deterministischer Mitarbeiter-Datensatz.

    Jeder Mitarbeiter besitzt ALLE 200 Skills, ALLE 128 Plugins und ALLE
    192 Tools des Katalogs sowie eine deterministische Spezialisierung.
    Zusaetzlich fuehrt jeder Mitarbeiter ein eigenes Unternehmen mit
    10**12 Mitarbeitern und einem 10**12 starken Developer-Team.

    :raises ValueError: wenn ``emp_id`` ausserhalb von 1..10**12 liegt.
    """

    identity = employee_identity(emp_id)

    return {
        "id": identity["id"],
        "name": identity["name"],
        "badge": identity["badge"],
        "first": identity["first"],
        "last": identity["last"],
        "role": identity["role"],
        "department": identity["department"],
        "specialization": identity["specialization"],
        "skills": _capability_block(catalog.SKILL_CATALOG),
        "plugins": _capability_block(catalog.PLUGIN_CATALOG),
        "tools": _capability_block(catalog.TOOL_CATALOG),
        "company": {
            "name": identity["company_name"],
            "employees": COMPANY_EMPLOYEES,
            "developers": COMPANY_DEVELOPERS,
            "skills": _capability_block(catalog.SKILL_CATALOG),
            "plugins": _capability_block(catalog.PLUGIN_CATALOG),
            "tools": _capability_block(catalog.TOOL_CATALOG),
        },
    }


def workforce_summary() -> dict[str, int]:
    """Alle globalen Kennzahlen der Enterprise-Workforce als ``int``.

    Python rechnet beliebig grosse Ganzzahlen exakt — die Werte werden
    daher nicht gerundet oder als Float ausgegeben.
    """

    summary = catalog.catalog_summary()
    return {
        "employees_direct": EMPLOYEES_DIRECT,
        "companies": EMPLOYEES_DIRECT,
        "company_employees": COMPANY_EMPLOYEES,
        "company_developers": COMPANY_DEVELOPERS,
        "total_workforce": TOTAL_WORKFORCE,
        "total_developers": TOTAL_DEVELOPERS,
        "skills": summary["skills"],
        "plugins": summary["plugins"],
        "tools": summary["tools"],
        "skill_categories": summary["skill_categories"],
        "plugin_categories": summary["plugin_categories"],
        "tool_categories": summary["tool_categories"],
    }
