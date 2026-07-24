"""Prometheus-Exporter für Compute-Metriken (Auftrag §5.5).

Erzeugt aus DeviceMetrics ein Prometheus-Text-Exposition-Format. Rein und
testbar; kein laufender Scrape nötig. Der /metrics-Endpunkt kann diese Registry
im FastAPI-App bereitstellen.
"""

from __future__ import annotations

from collections.abc import Iterable

from prometheus_client import CollectorRegistry, Gauge, generate_latest

from .hal import DeviceMetrics


def build_registry(metrics: Iterable[DeviceMetrics]) -> CollectorRegistry:
    reg = CollectorRegistry()
    util = Gauge("gpu_utilization_pct", "GPU-Auslastung in Prozent", ["device"], registry=reg)
    mem_used = Gauge("gpu_memory_used_mb", "Belegter Gerätespeicher (MB)", ["device"], registry=reg)
    mem_total = Gauge("gpu_memory_total_mb", "Gesamter Gerätespeicher (MB)", ["device"], registry=reg)
    temp = Gauge("gpu_temperature_celsius", "Temperatur (°C)", ["device"], registry=reg)
    power = Gauge("gpu_power_watts", "Leistungsaufnahme (W)", ["device"], registry=reg)

    for m in metrics:
        if m.utilization_pct is not None:
            util.labels(m.device_id).set(m.utilization_pct)
        if m.memory_used_mb is not None:
            mem_used.labels(m.device_id).set(m.memory_used_mb)
        if m.memory_total_mb is not None:
            mem_total.labels(m.device_id).set(m.memory_total_mb)
        if m.temperature_c is not None:
            temp.labels(m.device_id).set(m.temperature_c)
        if m.power_w is not None:
            power.labels(m.device_id).set(m.power_w)
    return reg


def render_metrics(metrics: Iterable[DeviceMetrics]) -> bytes:
    """Prometheus-Text-Format (für den /metrics-Endpunkt)."""
    return generate_latest(build_registry(metrics))
