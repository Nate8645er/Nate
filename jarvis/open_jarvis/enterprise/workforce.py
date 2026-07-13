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

# ---------------------------------------------------------------------------
# Mitarbeiter-Typen: Jeder der 10**12 Mitarbeiter ist ein Agent, Assistent,
# Berater usw. Die Gewichte sind Promille (‰) und summieren sich auf 1000,
# sodass die aktiven Zahlen exakt aufgehen: count = permille * 10**9
# (denn 10**12 / 1000 = 10**9). Summe aller Typen = 10**12.
# ---------------------------------------------------------------------------
EMPLOYEE_TYPES: list[tuple[str, int]] = [
    ("Agenten", 240),
    ("Assistenten", 210),
    ("Entwickler", 180),
    ("Berater", 150),
    ("Analysten", 90),
    ("Spezialisten", 70),
    ("Automatisierung", 40),
    ("Sonstige", 20),
]

#: Einheit pro Promille bei 10**12 Mitarbeitern.
_PERMILLE_UNIT: int = EMPLOYEES_DIRECT // 1000  # = 10**9


def mix64(x: int) -> int:
    """SplitMix64-Finalizer: deterministischer 64-Bit-Hash (siehe SPEC)."""

    x = (x + 0x9E3779B97F4A7C15) & MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return (z ^ (z >> 31)) & MASK


def _type_for_permille(value: int) -> str:
    """Ordnet einen Wert 0..999 deterministisch einem Mitarbeiter-Typ zu (kumulativ)."""

    cumulative = 0
    for name, permille in EMPLOYEE_TYPES:
        cumulative += permille
        if value < cumulative:
            return name
    return EMPLOYEE_TYPES[-1][0]


def employee_type(emp_id: int) -> str:
    """Deterministischer Mitarbeiter-Typ (Agent, Assistent, Berater, …)."""

    return str(employee_identity(emp_id)["type"])


def type_distribution() -> list[dict[str, object]]:
    """Verteilung der Mitarbeiter-Typen als exakte aktive Zahlen.

    Alle Mitarbeiter sind aktiv; die Summe der Zahlen ist genau 10**12.
    """

    return [
        {
            "type": name,
            "permille": permille,
            "percent": permille / 10,
            "count": permille * _PERMILLE_UNIT,
        }
        for name, permille in EMPLOYEE_TYPES
    ]


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
    h7 = mix64(h6)

    first = FIRST_NAMES[h1 % 32]
    last = LAST_NAMES[h2 % 32]
    role = ROLES[h3 % 24]
    department = DEPARTMENTS[h4 % 16]
    company_suffix = COMPANY_SUFFIXES[h5 % 16]
    specialization = catalog.all_skills()[h6 % 200]
    emp_type = _type_for_permille(h7 % 1000)

    return {
        "id": emp_id,
        "first": first,
        "last": last,
        "name": f"{first} {last}",
        "badge": f"JRV-{str(emp_id).zfill(13)}",
        "role": role,
        "department": department,
        "specialization": specialization,
        "type": emp_type,
        "company_name": f"{first} {last} {company_suffix}",
    }


def _capability_block(categories: dict[str, list[str]]) -> dict[str, object]:
    """Zaehler + Kategorien-Zugriff fuer einen Katalog-Abschnitt."""

    return {
        "count": sum(len(items) for items in categories.values()),
        "categories": {name: list(items) for name, items in categories.items()},
    }


def _list_block(items: list[str]) -> dict[str, object]:
    """Zaehler + Liste fuer eine flache Faehigkeiten-Liste (Modelle, Agent-Tools, Shopify)."""

    return {"count": len(items), "items": list(items)}


def _full_capabilities() -> dict[str, object]:
    """Der komplette Faehigkeiten-Satz, den JEDER Mitarbeiter/jedes Unternehmen besitzt.

    Enthaelt ALLE Skills, Plugins, Tools sowie die neu installierten Faehigkeiten:
    alle KI-Modelle (inkl. Fable 5), alle Agent-Werkzeuge und die volle
    Shopify-Anbindung.
    """

    return {
        "skills": _capability_block(catalog.SKILL_CATALOG),
        "plugins": _capability_block(catalog.PLUGIN_CATALOG),
        "tools": _capability_block(catalog.TOOL_CATALOG),
        "models": _list_block(catalog.AI_MODELS),
        "agent_tools": _list_block(catalog.AGENT_TOOLS),
        "shopify": _list_block(catalog.SHOPIFY_CAPABILITIES),
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
    capabilities = _full_capabilities()

    record: dict[str, object] = {
        "id": identity["id"],
        "name": identity["name"],
        "badge": identity["badge"],
        "first": identity["first"],
        "last": identity["last"],
        "role": identity["role"],
        "department": identity["department"],
        "specialization": identity["specialization"],
        "type": identity["type"],
    }
    # ALLE Skills/Plugins/Tools + KI-Modelle (inkl. Fable 5) + Agent-Werkzeuge + Shopify.
    record.update(capabilities)
    record["company"] = {
        "name": identity["company_name"],
        "employees": COMPANY_EMPLOYEES,
        "developers": COMPANY_DEVELOPERS,
        # Das Unternehmen und sein 10**12-Developer-Team besitzen denselben
        # kompletten Faehigkeiten-Satz wie der Mitarbeiter selbst.
        **_full_capabilities(),
        "developer_team": {
            "size": COMPANY_DEVELOPERS,
            **_full_capabilities(),
        },
    }
    return record


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
        # Neu installierte Faehigkeiten, die JEDER Mitarbeiter besitzt:
        "models": len(catalog.AI_MODELS),
        "agent_tools": len(catalog.AGENT_TOOLS),
        "shopify_capabilities": len(catalog.SHOPIFY_CAPABILITIES),
    }
