"""Reine Tarif-Logik ohne externe Abhaengigkeiten (dadurch isoliert testbar)."""
from __future__ import annotations


def model_allowed(model: str, allowed: list) -> bool:
    """True, wenn der Tarif das Modell freischaltet. '*' = alle (Enterprise)."""
    return "*" in allowed or model in allowed
