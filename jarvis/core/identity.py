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

    @property
    def display(self) -> str:
        return f"{self.name} ({self.role}, {self.team})"


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

    team, roles = TEAMS[segments[-1] % len(TEAMS)]
    role = roles[rng.randrange(len(roles))]
    name = f"{_FIRST[rng.randrange(len(_FIRST))]} {_LAST[rng.randrange(len(_LAST))]}-{segments[-1] % 1000:03d}"
    skills = tuple(rng.sample(_SKILL_POOL, k=4))
    goals = tuple(rng.sample(_GOAL_POOL, k=2))
    company = f"{name.split()[1].split('-')[0]} Ventures #{segments[-1] % 100_000}"

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
        depth=len(segments) - 1,
    )


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
