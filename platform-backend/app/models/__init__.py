"""models/ — Modell-Router: eine Entscheidung lokal ↔ Cloud, dann Ausführung.

Die *Entscheidung* ist reine, testbare Logik (ohne Netz/GPU). Die *Ausführung*
delegiert an LiteLLM (Adapter). Der bestehende TS-Router (lib/agents/providers.ts)
bleibt unangetastet; dieser hier bedient nur die neue Backend-Schicht.
"""
