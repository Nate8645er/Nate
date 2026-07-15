"""Prozedurale Identitäten: 100 Milliarden adressierbare virtuelle Mitarbeiter.

Kein Mitarbeiter wird gespeichert — jede Identität wird deterministisch aus
ihrer Adresse berechnet und erst bei Aktivierung materialisiert. Dadurch ist
der volle Adressraum (100 Mrd. pro Organisationsebene) nutzbar, ohne auch nur
ein Byte pro inaktivem Mitarbeiter zu verbrauchen.

Adressen sind hierarchisch:
    "17"        -> Mitarbeiter 17 der Wurzelorganisation
    "17/423"    -> Mitarbeiter 423 des virtuellen Unternehmens von Nr. 17
    "17/423/9"  -> eine Ebene tiefer, beliebig rekursiv

Jede Ebene adressiert wieder ADDRESS_SPACE Mitarbeiter — die Gesamtstruktur
ist damit theoretisch unbegrenzt, praktisch begrenzt nur durch die Hardware,
die gleichzeitig AKTIVE Agenten ausführt.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

ADDRESS_SPACE = 100_000_000_000  # 100 Milliarden pro Ebene

TEAMS: list[tuple[str, list[str]]] = [
    ("Führung", ["CEO", "COO", "CTO", "CFO", "Chief of Staff"]),
    ("Softwareentwicklung", ["Software-Entwickler", "Senior Engineer", "Code-Reviewer"]),
    ("KI-Entwicklung", ["KI-Entwickler", "ML-Engineer", "Prompt-Engineer"]),
    ("Python-Team", ["Python-Entwickler", "Backend-Entwickler"]),
    ("Rust-Team", ["Rust-Entwickler", "Systems-Engineer"]),
    ("C++-Team", ["C++-Entwickler", "Performance-Engineer"]),
    ("Java-Team", ["Java-Entwickler", "Enterprise-Entwickler"]),
    ("Web-Team", ["Frontend-Entwickler", "Fullstack-Entwickler", "UI-Entwickler"]),
    ("Mobile-Team", ["Android-Entwickler", "iOS-Entwickler"]),
    ("Cybersecurity", ["Security-Analyst", "Penetration-Tester", "CISO"]),
    ("DevOps", ["DevOps-Engineer", "SRE", "Release-Manager"]),
    ("Cloud", ["Cloud-Architekt", "Infrastruktur-Engineer"]),
    ("Datenanalyse", ["Data-Scientist", "Data-Engineer", "Analyst"]),
    ("Business", ["Business-Analyst", "Stratege", "Produktmanager"]),
    ("Marketing", ["Marketing-Manager", "Content-Stratege", "SEO-Spezialist"]),
    ("Sales", ["Sales-Manager", "Account-Manager"]),
    ("Recherche", ["Researcher", "Wissensmanager"]),
    ("Dokumentation", ["Technical Writer", "Dokumentations-Manager"]),
    ("Qualitätsmanagement", ["QA-Engineer", "Test-Manager", "Auditor"]),
    ("Finanzanalyse", ["Finanzanalyst", "Controller"]),
    ("Automatisierung", ["Automatisierungs-Engineer", "RPA-Entwickler"]),
    ("Smart-Home", ["IoT-Engineer", "Smart-Home-Integrator"]),
    ("Robotik", ["Robotik-Engineer", "Embedded-Entwickler"]),
    ("UI/UX", ["UX-Designer", "UI-Designer", "Design-Lead"]),
    ("Projektmanagement", ["Projektmanager", "Scrum-Master", "Koordinator"]),
]

_FIRST = ["Ada", "Alan", "Grace", "Linus", "Margaret", "Nikola", "Marie", "Kai",
          "Lena", "Jonas", "Mira", "Elias", "Nova", "Rio", "Sam", "Yuna",
          "Iris", "Felix", "Tara", "Omar", "Nina", "Levi", "Zoe", "Aris"]
_LAST = ["Vector", "Turing", "Hopper", "Quant", "Nexus", "Cipher", "Delta",
         "Orion", "Lumen", "Atlas", "Vega", "Kern", "Falk", "Stein", "Nord",
         "Blitz", "Sturm", "Klar", "Frei", "Wolf", "Berg", "Strom"]

_SKILL_POOL = ["Analyse", "Codegenerierung", "Testen", "Dokumentation",
               "Recherche", "Planung", "Review", "Automatisierung",
               "Datenverarbeitung", "Kommunikation", "Fehlersuche", "Design"]

# Werkzeug-Kompetenzen (welche JARVIS-Werkzeuge ein Mitarbeiter beherrscht) —
# mehr davon je höher das Level.
_TOOL_POOL = ["dateien", "shell", "web", "browser", "code", "modelle", "skills",
              "recherche", "planung", "sicherheit", "automatisierung", "pc"]

_MASTERY = [(80, "Großmeister"), (60, "Meister"), (40, "Experte"),
            (20, "Fortgeschritten"), (0, "Novize")]

# Führungs-/Senior-Rollen bekommen einen Level-Bonus.
_SENIOR_MARK = ("CEO", "COO", "CTO", "CFO", "Chief", "Lead", "Senior",
                "Manager", "Architekt", "CISO", "Master")


def mastery_of(level: int) -> str:
    for schwelle, name in _MASTERY:
        if level >= schwelle:
            return name
    return "Novize"


def xp_for_level(level: int) -> int:
    """Erfahrungspunkte, die zu einem Level gehören (steigende Kurve)."""
    return level * level * 50

_GOAL_POOL = ["Aufgaben präzise und nachvollziehbar erledigen",
              "Ergebnisse dokumentieren und mit dem Team teilen",
              "Fehler früh erkennen und Lösungen vorschlagen",
              "Qualität vor Geschwindigkeit stellen",
              "Wissen im Langzeitgedächtnis ablegen"]


@dataclass(frozen=True)
class VirtualEmployee:
    """Eine deterministisch materialisierte virtuelle Identität."""

    address: str
    name: str
    team: str
    role: str
    specialization: str
    skills: tuple[str, ...]
    goals: tuple[str, ...]
    priority: int              # 1 (höchste) .. 5
    company: str               # eigenes virtuelles Unternehmen dieses Mitarbeiters
    depth: int = 0
    sub_employees: int = field(default=ADDRESS_SPACE)  # adressierbar in SEINEM Unternehmen
    level: int = 1             # 1..99, prozedural (Basis-Level)
    xp: int = 0               # Basis-Erfahrung zum Level
    mastery: str = "Novize"    # Novize .. Großmeister
    tools: tuple[str, ...] = ()  # beherrschte Werkzeuge (mehr je höher das Level)
    is_team_boss: bool = False   # ist dieser Mitarbeiter Teamleiter?
    boss_address: str = ""       # Adresse des eigenen Teamleiters (Chef)

    @property
    def display(self) -> str:
        return f"{self.name} ({self.role}, {self.team})"

    @property
    def rang(self) -> str:
        """Kurzform für Anzeige: 'Meister Lvl 72'."""
        return f"{self.mastery} Lvl {self.level}"


def validate_address(address: str) -> list[int]:
    """Prüft eine hierarchische Adresse und liefert ihre Segmente."""
    parts = address.strip().strip("/").split("/")
    segments = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"Ungültiges Adress-Segment: {part!r}")
        n = int(part)
        if not 0 <= n < ADDRESS_SPACE:
            raise ValueError(f"Segment {n} außerhalb des Adressraums (0..{ADDRESS_SPACE - 1})")
        segments.append(n)
    if not segments:
        raise ValueError("Leere Adresse")
    return segments


def materialize(address: str) -> VirtualEmployee:
    """Berechnet die vollständige Identität für eine Adresse — deterministisch.

    Gleiche Adresse -> immer exakt derselbe Mitarbeiter, ohne Speicherung.
    """
    segments = validate_address(address)
    canonical = "/".join(str(s) for s in segments)
    seed = int.from_bytes(hashlib.sha256(canonical.encode()).digest()[:8], "big")
    rng = random.Random(seed)

    last = segments[-1]
    team_index = last % len(TEAMS)
    team, roles = TEAMS[team_index]
    # --- Team-Struktur: die ersten len(TEAMS) Adressen jedes Unternehmens
    #     (0..24) sind die Teamleiter — je einer pro Team. Alle anderen gehören
    #     zu einem Team und melden an dessen Chef (deterministisch, 0 Byte). ---
    is_team_boss = last < len(TEAMS)
    parent = "/".join(str(s) for s in segments[:-1])
    boss_addr = f"{parent}/{team_index}" if parent else str(team_index)

    if is_team_boss:
        role = f"Teamleiter {team}"
    else:
        role = roles[rng.randrange(len(roles))]
    name = f"{_FIRST[rng.randrange(len(_FIRST))]} {_LAST[rng.randrange(len(_LAST))]}-{last % 1000:03d}"
    goals = tuple(rng.sample(_GOAL_POOL, k=2))
    company = f"{name.split()[1].split('-')[0]} Ventures #{last % 100_000}"
    depth = len(segments) - 1

    # --- Prozedurales Level & Meisterschaft (deterministisch, 0 Byte) ---
    base = 1 + ((seed >> 8) % 90)                       # 1..90
    if is_team_boss:
        base += 15                                      # Teamleiter führen -> höheres Level
    elif any(mark in role for mark in _SENIOR_MARK):
        base += 9                                       # Führungs-/Senior-Bonus
    base += min(depth * 3, 9)                           # tiefer = eigener Gründer
    level = max(1, min(99, base))
    mastery = mastery_of(level)
    # mehr Skills & Werkzeuge, je höher das Level
    n_skills = min(len(_SKILL_POOL), 4 + level // 30)   # 4..7
    n_tools = min(len(_TOOL_POOL), 2 + level // 20)     # 2..7
    skills = tuple(rng.sample(_SKILL_POOL, k=n_skills))
    tools = tuple(rng.sample(_TOOL_POOL, k=n_tools))

    return VirtualEmployee(
        address=canonical,
        name=name,
        team=team,
        role=role,
        specialization=f"{team} / {skills[0]}",
        skills=skills,
        goals=goals,
        priority=1 + (seed % 5),
        company=company,
        depth=depth,
        level=level,
        xp=xp_for_level(level),
        mastery=mastery,
        tools=tools,
        is_team_boss=is_team_boss,
        boss_address=boss_addr,
    )


def team_bosses(company_address: str = "") -> list[VirtualEmployee]:
    """Die Teamleiter eines Unternehmens — je einer pro Team (Adressen 0..24).

    company_address="" -> Wurzelorganisation; sonst z. B. "7" für die Firma
    von Mitarbeiter 7. Deterministisch, kein Speicher.
    """
    prefix = f"{company_address.strip('/')}/" if company_address.strip("/") else ""
    return [materialize(f"{prefix}{i}") for i in range(len(TEAMS))]


def address_for_task(description: str, team_hint: str | None = None) -> str:
    """Wählt deterministisch eine passende Adresse für eine Aufgabe.

    Enthält die Aufgabe ein Team-Stichwort, wird ein Mitarbeiter aus dem
    passenden Team-Segment gewählt; sonst entscheidet der Hash der Aufgabe.
    """
    text = (team_hint or description).lower()
    team_index = None
    for i, (team, _) in enumerate(TEAMS):
        if team.lower().split("-")[0] in text or team.lower() in text:
            team_index = i
            break
    h = int.from_bytes(hashlib.sha256(description.encode()).digest()[:8], "big")
    if team_index is None:
        n = h % ADDRESS_SPACE
    else:
        # Adressen sind auf Teams gestreift: n % len(TEAMS) == team_index
        n = (h % (ADDRESS_SPACE // len(TEAMS))) * len(TEAMS) + team_index
        n %= ADDRESS_SPACE
    return str(n)
