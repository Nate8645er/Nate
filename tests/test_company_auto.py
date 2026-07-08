"""Tests für den Auto-Modus des virtuellen Unternehmens."""

from pathlib import Path

from jarvis.core.agents import AgentRegistry
from jarvis.core.company import Company


def _registry(namen: list[str]) -> AgentRegistry:
    registry = AgentRegistry([Path("/gibt/es/nicht")])
    registry.agents = {
        name: ({"description": f"Abteilung {name}"}, f"Du bist {name}.")
        for name in namen
    }
    return registry


class FakeClient:
    """Antwortet als Orchestrator mit einer Abteilungs-Auswahl."""

    def __init__(self, auswahl: str):
        self.auswahl = auswahl
        self.system_prompts: list[str] = []

    def chat(self, prompt=None, messages=None):
        system = messages[0]["content"] if messages else ""
        self.system_prompts.append(system)
        if "ultra-orchestrator" in system:
            return self.auswahl
        return f"Beitrag ({system[:20]})"


def test_auto_pipeline_waehlt_abteilungen_und_ceo_schliesst_ab():
    registry = _registry([
        "ultra-orchestrator", "ultra-ceo", "ultra-marketing",
        "ultra-finance", "ultra-qa",
    ])
    client = FakeClient("ultra-marketing, ultra-finance")
    company = Company(client, registry, pipeline="auto")

    results = company.run("Plane den Launch eines Produkts")
    rollen = [rolle for rolle, _ in results]
    assert rollen == ["ultra-marketing", "ultra-finance", "ultra-ceo"]


def test_auto_faellt_bei_unlesbarer_auswahl_auf_standard_zurueck():
    registry = _registry([
        "ultra-orchestrator", "ultra-architect", "ultra-fullstack", "ultra-qa",
    ])
    client = FakeClient("Dafür würde ich niemanden empfehlen!")
    company = Company(client, registry, pipeline="auto")

    rollen = [rolle for rolle, _ in company.run("irgendwas")]
    # Standard-Pipeline (soweit vorhanden), kein Absturz
    assert rollen == ["ultra-orchestrator", "ultra-architect",
                      "ultra-fullstack", "ultra-qa"]


def test_feste_pipeline_funktioniert_wie_bisher():
    registry = _registry(["ultra-qa", "ultra-docs"])
    client = FakeClient("egal")
    company = Company(client, registry, pipeline=["ultra-qa", "ultra-docs"])
    rollen = [rolle for rolle, _ in company.run("prüfe das")]
    assert rollen == ["ultra-qa", "ultra-docs"]
