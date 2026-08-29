"""Tests fuer die deterministische Workforce-Engine des Enterprise-Pakets."""

from __future__ import annotations

import pytest

from open_jarvis.enterprise import (
    COMPANY_DEVELOPERS,
    COMPANY_EMPLOYEES,
    EMPLOYEES_DIRECT,
    TOTAL_DEVELOPERS,
    TOTAL_WORKFORCE,
    all_plugins,
    all_skills,
    all_tools,
    catalog_summary,
    employee,
    mix64,
    workforce_summary,
)


class TestKennzahlen:
    def test_direct_employees(self) -> None:
        assert EMPLOYEES_DIRECT == 10**12

    def test_company_sizes(self) -> None:
        assert COMPANY_EMPLOYEES == 10**12
        assert COMPANY_DEVELOPERS == 10**12

    def test_total_workforce(self) -> None:
        assert TOTAL_WORKFORCE == 10**12 + 2 * 10**24

    def test_total_developers(self) -> None:
        assert TOTAL_DEVELOPERS == EMPLOYEES_DIRECT * COMPANY_DEVELOPERS
        assert TOTAL_DEVELOPERS == 10**24


class TestMix64:
    def test_bekannte_splitmix64_werte(self) -> None:
        # Referenzwerte des SplitMix64-Finalizers (Fixpunkte gegen Drift).
        assert mix64(0) == 16294208416658607535
        assert mix64(1) == 10451216379200822465
        assert mix64(42) == 13679457532755275413

    def test_ergebnis_ist_64_bit(self) -> None:
        for x in (0, 1, 7, 10**12, 2**63, 2**64 - 1):
            assert 0 <= mix64(x) <= (1 << 64) - 1

    def test_deterministisch(self) -> None:
        assert mix64(123456789) == mix64(123456789)


class TestEmployeeValidierung:
    def test_untere_grenze_gueltig(self) -> None:
        assert employee(1)["id"] == 1

    def test_obere_grenze_gueltig(self) -> None:
        assert employee(10**12)["id"] == 10**12

    def test_null_ungueltig(self) -> None:
        with pytest.raises(ValueError):
            employee(0)

    def test_zu_gross_ungueltig(self) -> None:
        with pytest.raises(ValueError):
            employee(10**12 + 1)

    def test_negativ_ungueltig(self) -> None:
        with pytest.raises(ValueError):
            employee(-5)


class TestEmployeeDeterminismus:
    def test_gleiche_id_identisches_ergebnis(self) -> None:
        assert employee(7) == employee(7)
        assert employee(999_999_999_999) == employee(999_999_999_999)

    def test_badge_format(self) -> None:
        record = employee(42)
        assert record["badge"] == "JRV-0000000000042"
        assert len(str(record["badge"])) == len("JRV-") + 13


class TestEmployeeFixpunkte:
    """Konkrete Feldwerte — Drift bei Refactorings faellt sofort auf."""

    def test_employee_42(self) -> None:
        record = employee(42)
        assert record["id"] == 42
        assert record["first"] == "Theo"
        assert record["last"] == "Almeida"
        assert record["name"] == "Theo Almeida"
        assert record["badge"] == "JRV-0000000000042"
        assert record["role"] == "Product Manager"
        assert record["department"] == "DevOps & Cloud"
        assert record["specialization"] == "Videoproduktion"
        assert record["company"]["name"] == "Theo Almeida Werke"

    def test_employee_123456789(self) -> None:
        record = employee(123456789)
        assert record["id"] == 123456789
        assert record["first"] == "Max"
        assert record["last"] == "Nguyen"
        assert record["name"] == "Max Nguyen"
        assert record["badge"] == "JRV-0000123456789"
        assert record["role"] == "ML Engineer"
        assert record["department"] == "HR & People"
        assert record["specialization"] == "Threat Modeling"
        assert record["company"]["name"] == "Max Nguyen Systems"


class TestEmployeeKatalog:
    def test_zaehler_und_kategorien(self) -> None:
        record = employee(42)
        assert record["skills"]["count"] == 200
        assert record["plugins"]["count"] == 128
        assert record["tools"]["count"] == 192
        assert len(record["skills"]["categories"]) == 16
        assert len(record["plugins"]["categories"]) == 16
        assert len(record["tools"]["categories"]) == 16

    def test_kategorien_summieren_auf_zaehler(self) -> None:
        record = employee(1)
        for key, expected in (("skills", 200), ("plugins", 128), ("tools", 192)):
            block = record[key]
            assert sum(len(v) for v in block["categories"].values()) == expected

    def test_spezialisierung_stammt_aus_katalog(self) -> None:
        skills = all_skills()
        for emp_id in (1, 42, 123456789, 10**12):
            assert employee(emp_id)["specialization"] in skills

    def test_company_block(self) -> None:
        company = employee(42)["company"]
        assert company["employees"] == 10**12
        assert company["developers"] == 10**12
        assert company["skills"]["count"] == 200
        assert company["plugins"]["count"] == 128
        assert company["tools"]["count"] == 192


class TestWorkforceSummary:
    def test_globale_kennzahlen(self) -> None:
        summary = workforce_summary()
        assert summary["employees_direct"] == 10**12
        assert summary["companies"] == 10**12
        assert summary["company_employees"] == 10**12
        assert summary["company_developers"] == 10**12
        assert summary["total_workforce"] == 10**12 + 2 * 10**24
        assert summary["total_developers"] == 10**24

    def test_katalog_summen(self) -> None:
        summary = workforce_summary()
        assert summary["skills"] == 200
        assert summary["plugins"] == 128
        assert summary["tools"] == 192
        assert summary["skill_categories"] == 16
        assert summary["plugin_categories"] == 16
        assert summary["tool_categories"] == 16

    def test_alle_werte_sind_int(self) -> None:
        for value in workforce_summary().values():
            assert isinstance(value, int)


class TestMitarbeiterTypen:
    def test_verteilung_summiert_auf_10_hoch_12(self) -> None:
        from open_jarvis.enterprise import type_distribution

        dist = type_distribution()
        assert len(dist) == 8
        assert sum(d["count"] for d in dist) == 10**12
        # count = permille * 10**9
        for d in dist:
            assert d["count"] == d["permille"] * 10**9

    def test_typen_namen_und_agenten_anteil(self) -> None:
        from open_jarvis.enterprise import type_distribution

        by_type = {d["type"]: d for d in type_distribution()}
        assert "Agenten" in by_type and "Assistenten" in by_type and "Berater" in by_type
        assert by_type["Agenten"]["count"] == 240_000_000_000

    def test_employee_type_ist_deterministisch_und_gueltig(self) -> None:
        from open_jarvis.enterprise import EMPLOYEE_TYPES, employee, employee_type

        namen = {name for name, _ in EMPLOYEE_TYPES}
        for emp_id in (1, 42, 123456789, 10**12):
            t = employee_type(emp_id)
            assert t in namen
            assert employee(emp_id)["type"] == t

    def test_type_fixpunkte(self) -> None:
        from open_jarvis.enterprise import employee_type

        assert employee_type(42) == "Assistenten"
        assert employee_type(123456789) == "Analysten"


class TestKatalogKonsistenz:
    def test_flache_listen(self) -> None:
        assert len(all_skills()) == 200
        assert len(all_plugins()) == 128
        assert len(all_tools()) == 192

    def test_catalog_summary(self) -> None:
        summary = catalog_summary()
        assert summary == {
            "skills": 200,
            "plugins": 128,
            "tools": 192,
            "skill_categories": 16,
            "plugin_categories": 16,
            "tool_categories": 16,
        }
