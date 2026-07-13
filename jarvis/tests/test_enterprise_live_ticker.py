"""Tests fuer den deterministischen Live-Ticker des Enterprise-Pakets."""

from __future__ import annotations

from open_jarvis.enterprise import DEFAULT_SEED, EVENT_TYPES, LiveTicker, employee

EXPECTED_TYPES = {
    "feature",
    "onboarding",
    "projekt",
    "produktivitaet",
    "skill",
    "plugin",
    "tool",
    "sync",
    "partnerschaft",
    "auszeichnung",
}


class TestDeterminismus:
    def test_default_seed(self) -> None:
        assert DEFAULT_SEED == 20260712
        implicit = [LiveTicker().tick() for _ in range(10)]
        explicit = [LiveTicker(20260712).tick() for _ in range(10)]
        # Hinweis: jede Iteration erzeugt einen frischen Ticker -> Tick 1.
        assert implicit[0] == explicit[0]

    def test_gleicher_seed_gleiche_sequenz(self) -> None:
        a = LiveTicker(seed=1234)
        b = LiveTicker(seed=1234)
        assert [a.tick() for _ in range(50)] == [b.tick() for _ in range(50)]

    def test_anderer_seed_andere_sequenz(self) -> None:
        a = LiveTicker(seed=1234)
        b = LiveTicker(seed=4321)
        events_a = [a.tick() for _ in range(50)]
        events_b = [b.tick() for _ in range(50)]
        assert events_a != events_b

    def test_none_entspricht_default_seed(self) -> None:
        a = LiveTicker()
        b = LiveTicker(seed=DEFAULT_SEED)
        assert [a.tick() for _ in range(25)] == [b.tick() for _ in range(25)]


class TestFixpunkte:
    """Konkrete Event-Werte fuer den Default-Seed (Drift-Erkennung)."""

    def test_erstes_event(self) -> None:
        event = LiveTicker().tick()
        assert event == {
            "tick": 1,
            "employee_id": 114432040025,
            "badge": "JRV-0114432040025",
            "text": '🏆 Orion Almeida zum "Mitarbeiter des Zyklus" in Marketing ernannt',
            "type": "auszeichnung",
        }

    def test_zweites_event(self) -> None:
        ticker = LiveTicker()
        ticker.tick()
        event = ticker.tick()
        assert event["tick"] == 2
        assert event["employee_id"] == 760810885420
        assert event["type"] == "skill"
        assert event["text"] == (
            '🧠 Mira Costa hat Skill "UX-Research" auf Level MAX zertifiziert'
        )


class TestEventSchema:
    def test_pflichtfelder(self) -> None:
        event = LiveTicker(seed=99).tick()
        assert set(event) == {"tick", "employee_id", "badge", "text", "type"}

    def test_tick_zaehlt_hoch(self) -> None:
        ticker = LiveTicker(seed=5)
        assert [ticker.tick()["tick"] for _ in range(20)] == list(range(1, 21))

    def test_employee_id_im_gueltigen_bereich(self) -> None:
        ticker = LiveTicker(seed=7)
        for event in ticker.stream(200):
            assert 1 <= event["employee_id"] <= 10**12

    def test_badge_passt_zum_mitarbeiter(self) -> None:
        ticker = LiveTicker(seed=11)
        for event in ticker.stream(25):
            assert event["badge"] == employee(event["employee_id"])["badge"]

    def test_typ_stammt_aus_templates(self) -> None:
        assert set(EVENT_TYPES) == EXPECTED_TYPES
        ticker = LiveTicker(seed=13)
        for event in ticker.stream(100):
            assert event["type"] in EXPECTED_TYPES
            assert isinstance(event["text"], str) and event["text"]


class TestTemplateAbdeckung:
    def test_alle_10_typen_in_500_ticks(self) -> None:
        ticker = LiveTicker()
        seen = {event["type"] for event in ticker.stream(500)}
        assert seen == EXPECTED_TYPES


class TestStream:
    def test_stream_liefert_exakt_count_events(self) -> None:
        ticker = LiveTicker(seed=3)
        events = list(ticker.stream(37))
        assert len(events) == 37

    def test_stream_entspricht_tick_sequenz(self) -> None:
        a = LiveTicker(seed=17)
        b = LiveTicker(seed=17)
        assert list(a.stream(40)) == [b.tick() for _ in range(40)]


class TestAggregateStats:
    def test_leerer_ticker(self) -> None:
        stats = LiveTicker(seed=1).aggregate_stats()
        assert stats["ticks"] == 0
        assert stats["unique_employees"] == 0
        assert sum(stats["events_by_type"].values()) == 0
        assert set(stats["events_by_type"]) == EXPECTED_TYPES

    def test_stats_nach_500_ticks(self) -> None:
        ticker = LiveTicker()
        for _ in ticker.stream(500):
            pass
        stats = ticker.aggregate_stats()
        assert stats["seed"] == DEFAULT_SEED
        assert stats["ticks"] == 500
        assert sum(stats["events_by_type"].values()) == 500
        assert all(count > 0 for count in stats["events_by_type"].values())
        assert 0 < stats["unique_employees"] <= 500
        assert stats["total_workforce"] == 10**12 + 2 * 10**24
