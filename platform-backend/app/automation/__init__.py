"""automation/ — Durable Workflows, Trigger, Scheduler (Phase 5, implementiert).

- engine.py           : LocalWorkflowEngine (durable/wiederaufnehmbar/idempotent, Retry)
- triggers.py         : Interval/Daily/Event/Webhook + IdempotencyGuard (reine Feuer-Logik)
- temporal_adapter.py : Abbildung auf Temporal-SDK (voller Betrieb braucht Server)

24/7-Ausführung = Temporal-Workflows in Produktion; die lokale Engine
modelliert die Garantien testbar ohne Server.
"""
