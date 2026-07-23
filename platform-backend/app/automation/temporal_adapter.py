"""Temporal-Adapter (Auftrag §3: Workflow-Engine = Temporal).

Bindet Temporal hinter dieselben Begriffe wie die lokale Engine. Der VOLLE
Betrieb (durable Ausführung) braucht einen laufenden Temporal-Server + Worker —
in dieser Umgebung nicht vorhanden. Was hier real und getestet ist: die
Abbildung unserer `RetryPolicy` auf die Temporal-SDK-RetryPolicy (der Punkt, an
dem sich Fehler am ehesten einschleichen). Die Verbindungslogik meldet ehrlich
„nicht-konfiguriert", wenn keine Serveradresse gesetzt ist.
"""

from __future__ import annotations

from datetime import timedelta

from .engine import RetryPolicy


def temporal_available() -> bool:
    try:
        import temporalio  # noqa: F401
        return True
    except ImportError:
        return False


def to_temporal_retry(policy: RetryPolicy):
    """Unsere RetryPolicy → temporalio.common.RetryPolicy (real)."""
    from temporalio.common import RetryPolicy as TRetry

    return TRetry(
        maximum_attempts=policy.max_attempts,
        initial_interval=timedelta(seconds=policy.base_delay),
        backoff_coefficient=policy.factor,
    )


class TemporalConfigError(RuntimeError):
    pass


async def connect(address: str | None, namespace: str = "default"):
    """Verbindet zu Temporal. Ehrlich: ohne Adresse -> Fehler statt Schein-Client."""
    if not address:
        raise TemporalConfigError("Temporal: nicht-konfiguriert (TEMPORAL_ADDRESS fehlt)")
    from temporalio.client import Client

    return await Client.connect(address, namespace=namespace)
