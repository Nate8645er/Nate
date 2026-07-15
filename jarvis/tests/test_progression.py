"""Tests für Level-System & echtes Level-Up (Agent 4 — QS)."""

from __future__ import annotations

from pathlib import Path


def test_procedural_level_deterministic_and_in_range():
    from jarvis.core.identity import materialize, mastery_of
    seen = set()
    for a in ["0", "7", "42", "31337", "99999999999", "42/777/31337"]:
        e = materialize(a)
        assert 1 <= e.level <= 99
        assert e.mastery == mastery_of(e.level)
        assert len(e.skills) >= 4 and len(e.tools) >= 2
        # deterministisch: gleicher Abruf -> gleiches Level
        assert materialize(a).level == e.level
        seen.add(e.level)
    assert len(seen) > 1        # Level variieren über Adressen


def test_team_boss_structure():
    """Jedes Unternehmen: 25 Teamleiter (Adr 0..24), jeder Mitarbeiter kennt seinen Chef."""
    from jarvis.core.identity import materialize, team_bosses, TEAMS
    bosses = team_bosses()
    assert len(bosses) == len(TEAMS)
    # Adressen 0..24 sind Chefs, je ein anderes Team
    assert all(b.is_team_boss for b in bosses)
    assert len({b.team for b in bosses}) == len(TEAMS)      # je Team genau einer
    for i, b in enumerate(bosses):
        assert b.address == str(i) and b.boss_address == str(i)
        assert "Teamleiter" in b.role
    # normaler Mitarbeiter: kein Chef, meldet an gleichen-Team-Chef
    e = materialize("31337")
    assert e.is_team_boss is False
    chef = materialize(e.boss_address)
    assert chef.is_team_boss and chef.team == e.team


def test_team_boss_recursive_in_subcompany():
    from jarvis.core.identity import team_bosses, materialize
    bosses = team_bosses("7")
    assert [b.address for b in bosses[:3]] == ["7/0", "7/1", "7/2"]
    assert all(b.is_team_boss for b in bosses)
    # ein Mitarbeiter im Unter-Unternehmen kennt seinen dortigen Chef
    e = materialize("7/500")
    assert e.boss_address.startswith("7/")


def test_mastery_tiers():
    from jarvis.core.identity import mastery_of
    assert mastery_of(5) == "Novize"
    assert mastery_of(25) == "Fortgeschritten"
    assert mastery_of(45) == "Experte"
    assert mastery_of(65) == "Meister"
    assert mastery_of(85) == "Großmeister"


def test_real_levelup_from_work(tmp_path: Path):
    from jarvis.core.progression import Progression, BONUS_SCHWELLE, XP_PRO_AUFGABE
    p = Progression(tmp_path / "f.db")
    addr = "42"
    # genug Aufgaben für +1 Bonus-Level
    n = BONUS_SCHWELLE // XP_PRO_AUFGABE
    up = False
    for _ in range(n):
        r = p.award(addr)
        up = up or r["level_up"]
    assert up is True
    assert p.get(addr)["bonus_level"] >= 1
    assert p.get(addr)["erledigt"] == n
    # effektives Level = Basis + Bonus, gedeckelt bei 99
    assert p.effective_level(50, addr) >= 51
    assert p.effective_level(99, addr) == 99


def test_progression_totals(tmp_path: Path):
    from jarvis.core.progression import Progression
    p = Progression(tmp_path / "f.db")
    p.award("1"); p.award("1"); p.award("2")
    t = p.totals()
    assert t["mitarbeiter_mit_fortschritt"] == 2
    assert t["aufgaben_gesamt"] == 3
    assert len(p.top()) == 2


def test_task_awards_xp_end_to_end(tmp_path: Path):
    """Eine echt erledigte Aufgabe erhöht die Erfahrung des Mitarbeiters."""
    import asyncio

    from jarvis.core.orchestrator import Orchestrator
    o = Orchestrator(tmp_path, max_active=2)

    async def run():
        await o.start()
        t = o.submit("!plugin calc eval expression=6*7")
        for _ in range(50):
            if t.status in ("fertig", "fehler"):
                break
            await asyncio.sleep(0.05)
        await o.stop()
        return t

    t = asyncio.run(run())
    assert t.status == "fertig"
    assert o.progression.get(t.address)["erledigt"] >= 1
