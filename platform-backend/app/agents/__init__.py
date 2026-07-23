"""agents/ — Agent-Runtime, Werkzeuge, Genehmigung, Orchestrator (Phase 4, implementiert).

- tools.py        : ToolRegistry + Risikoklassen (Freigabe ab „wirkt nach außen")
- approval.py     : Genehmigungs-Queue (mandanten-scoped, serialisierbar)
- spec.py         : deklaratives AgentSpec + harte Limits
- runtime.py      : schrittweise Ausführung, Zustand DB-fähig, Budget/Approval erzwungen
- orchestrator.py : Zerlegung → Delegation → Prüfung → Wiederholung → Eskalation

LLM/Planer/Prüfer sind injizierbar → ohne echtes Modell testbar.
"""
