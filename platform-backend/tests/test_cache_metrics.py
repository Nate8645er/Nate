"""Tests: Ergebnis-Cache, Tenant-Budget, Prometheus-Exporter."""

from app.compute.hal import DeviceMetrics
from app.compute.metrics import render_metrics
from app.models.cache import ResultCache, TenantBudget, cache_key


# ---- Cache-Key ----
def test_cache_key_stabil_und_ordnungsunabhaengig():
    a = cache_key("m", [{"role": "user", "content": "hi"}], {"t": 0.2})
    b = cache_key("m", [{"role": "user", "content": "hi"}], {"t": 0.2})
    c = cache_key("m", [{"role": "user", "content": "ho"}], {"t": 0.2})
    assert a == b and a != c
    assert len(a) == 64  # sha256 hex


# ---- ResultCache ----
def test_cache_get_put_und_ttl():
    t = {"v": 100.0}
    cache = ResultCache(ttl_seconds=10, _now=lambda: t["v"])
    cache.put("k", "wert")
    assert cache.get("k") == "wert"
    t["v"] = 111.0  # TTL abgelaufen
    assert cache.get("k") is None


def test_cache_eviction_bei_maxgroesse():
    cache = ResultCache(ttl_seconds=1e9, max_entries=2)
    cache.put("a", 1); cache.put("b", 2); cache.put("c", 3)
    assert len(cache) == 2
    assert cache.get("a") is None  # ältester verdrängt


# ---- TenantBudget ----
def test_budget_erlaubt_bis_limit_und_verbraucht():
    b = TenantBudget(daily_limit_tokens=1000)
    assert b.remaining("t1") == 1000
    assert b.allow("t1", 400) is True
    b.charge("t1", 400)
    assert b.remaining("t1") == 600
    assert b.allow("t1", 700) is False   # überschreitet Rest
    assert b.allow("t1", 600) is True


def test_budget_trennt_tenants():
    b = TenantBudget(daily_limit_tokens=100)
    b.charge("a", 100)
    assert b.remaining("a") == 0
    assert b.remaining("b") == 100       # anderer Tenant unberührt


# ---- Prometheus-Exporter ----
def test_render_metrics_enthaelt_gauges():
    m = DeviceMetrics(device_id="cuda:0", utilization_pct=42.0, memory_used_mb=2048,
                      memory_total_mb=24564, temperature_c=55.0, power_w=120.0)
    text = render_metrics([m]).decode("utf-8")
    assert "gpu_utilization_pct" in text
    assert 'device="cuda:0"' in text
    assert "gpu_temperature_celsius" in text
    assert "42.0" in text


def test_render_metrics_ueberspringt_none():
    m = DeviceMetrics(device_id="cpu:0", utilization_pct=None, memory_used_mb=None,
                      memory_total_mb=16000, temperature_c=None, power_w=None)
    text = render_metrics([m]).decode("utf-8")
    assert "gpu_memory_total_mb" in text
    # utilization war None -> kein Sample mit cpu:0 für utilization
    assert 'gpu_utilization_pct{device="cpu:0"}' not in text
