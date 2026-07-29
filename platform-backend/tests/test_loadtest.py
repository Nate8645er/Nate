"""Tests: Lasttest-Logik (Perzentile, Zusammenfassung) — rein/offline."""

from app.observability.loadtest import LoadResult, percentile, summarize


def test_percentile_grenzen_und_interpolation():
    vals = [1.0, 2.0, 3.0, 4.0]
    assert percentile(vals, 0) == 1.0
    assert percentile(vals, 100) == 4.0
    assert percentile(vals, 50) == 2.5  # linear interpoliert
    assert percentile([], 95) == 0.0
    assert percentile([7.0], 95) == 7.0


def test_summarize_zaehlt_ok_und_fehler():
    res = summarize([(True, 10.0), (True, 20.0), (False, 0.0)], duration_s=2.0)
    assert res.total == 3 and res.ok == 2 and res.failed == 1
    # Latenzen nur von erfolgreichen Requests.
    assert sorted(res.latencies_ms) == [10.0, 20.0]


def test_summary_enthaelt_perzentile_und_rps():
    res = LoadResult(total=4, ok=4, failed=0, duration_s=2.0, latencies_ms=[1, 2, 3, 4])
    s = res.summary()
    assert s["requests"] == 4 and s["failed"] == 0
    assert s["rps"] == 2.0
    assert s["latency_ms"]["p50"] == 2.5
    assert s["latency_ms"]["max"] == 4.0


def test_rps_bei_nulldauer_kein_crash():
    res = LoadResult(total=1, ok=1, failed=0, duration_s=0.0, latencies_ms=[5.0])
    assert res.rps == 0.0
