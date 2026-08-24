"""GUI tests.

The core suite runs without PySide6 and without a display: it covers the lazy
package import and the pure-Python animation/layout math in
:mod:`jarvis.gui.logic`. An optional offscreen smoke test runs only when
PySide6 (and a working Qt platform plugin) is available; it executes in a
subprocess so a Qt abort can never take down the test run.
"""

from __future__ import annotations

import importlib
import math
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from jarvis.gui import logic

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# -- package import (must work without PySide6) ----------------------------------------


def test_import_gui_package() -> None:
    module = importlib.import_module("jarvis.gui")
    assert module.__all__ == ["run_gui"]


def test_unknown_attribute_raises() -> None:
    module = importlib.import_module("jarvis.gui")
    with pytest.raises(AttributeError):
        _ = module.does_not_exist


def test_import_without_pyside6() -> None:
    """Importing jarvis.gui must succeed even when PySide6 is uninstallable."""
    script = textwrap.dedent(
        """
        import sys

        class _BlockPySide6:
            def find_spec(self, name, path=None, target=None):
                if name == "PySide6" or name.startswith("PySide6."):
                    raise ImportError("PySide6 blocked for test")
                return None

        sys.meta_path.insert(0, _BlockPySide6())
        import jarvis.gui

        assert jarvis.gui.__all__ == ["run_gui"]
        from jarvis.gui import logic

        assert logic.layout_mode(2000) == "wide"
        try:
            jarvis.gui.run_gui
        except ImportError as exc:
            assert "PySide6" in str(exc)
        else:
            raise SystemExit("expected ImportError when PySide6 is missing")
        print("NO-QT OK")
        """
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "NO-QT OK" in result.stdout


# -- scalar helpers ---------------------------------------------------------------------


def test_clamp() -> None:
    assert logic.clamp(-1.0) == 0.0
    assert logic.clamp(2.0) == 1.0
    assert logic.clamp(0.5) == 0.5
    assert logic.clamp(5.0, 0.0, 10.0) == 5.0


def test_smooth_level_attack_and_release() -> None:
    # Rising: fast attack.
    up = logic.smooth_level(0.0, 1.0, attack=0.5, release=0.1)
    assert up == pytest.approx(0.5)
    # Falling: slow release.
    down = logic.smooth_level(1.0, 0.0, attack=0.5, release=0.1)
    assert down == pytest.approx(0.9)


def test_smooth_level_converges() -> None:
    value = 0.0
    for _ in range(200):
        value = logic.smooth_level(value, 0.8)
    assert value == pytest.approx(0.8, abs=1e-3)


def test_breathing_bounds_and_period() -> None:
    for t in (0.0, 0.7, 1.9, 3.3, 10.0):
        level = logic.breathing(t, period=4.0, floor=0.08, amplitude=0.10)
        assert 0.08 <= level <= 0.18 + 1e-9
    assert logic.breathing(1.0, period=4.0) == pytest.approx(logic.breathing(5.0, period=4.0))
    assert logic.breathing(3.0, period=0.0) == pytest.approx(0.08)


def test_advance_angle_wraps_and_boosts() -> None:
    assert logic.advance_angle(359.0, 10.0, 1.0, boost=0.0, boost_gain=0.0) == pytest.approx(9.0)
    plain = logic.advance_angle(0.0, 10.0, 1.0, boost=0.0)
    boosted = logic.advance_angle(0.0, 10.0, 1.0, boost=1.0, boost_gain=2.0)
    assert boosted == pytest.approx(plain * 3.0)
    # Negative speed rotates backwards but stays in [0, 360).
    reverse = logic.advance_angle(5.0, -10.0, 1.0)
    assert 0.0 <= reverse < 360.0
    assert reverse == pytest.approx(355.0)


def test_layout_mode() -> None:
    assert logic.layout_mode(1920) == "wide"
    assert logic.layout_mode(1080) == "wide"
    assert logic.layout_mode(1079) == "narrow"
    assert logic.layout_mode(640) == "narrow"
    assert logic.layout_mode(800, threshold=700) == "wide"


# -- spectrum helpers ---------------------------------------------------------------------


def test_decay_spectrum_attack_and_decay() -> None:
    bars = [0.0, 1.0]
    result = logic.decay_spectrum(bars, [1.0, 0.0], attack=0.5, decay=0.1)
    assert result[0] == pytest.approx(0.5)  # rising fast
    assert result[1] == pytest.approx(0.9)  # falling slowly


def test_decay_spectrum_length_mismatch_and_clamping() -> None:
    result = logic.decay_spectrum([0.5, 0.5, 0.5], [2.0], attack=1.0, decay=1.0)
    assert len(result) == 3
    assert result[0] == pytest.approx(1.0)  # target clamped to 1.0
    assert result[1] == pytest.approx(0.0)  # missing targets treated as 0
    assert all(0.0 <= v <= 1.0 for v in result)


def test_spread_level_bounds() -> None:
    bars = logic.spread_level(0.8, 32, t=1.234)
    assert len(bars) == 32
    assert all(0.0 <= b <= 0.8 for b in bars)
    assert len({round(b, 6) for b in bars}) > 1  # shimmers, not uniform


def test_spread_level_zero_and_empty() -> None:
    assert logic.spread_level(0.0, 8, t=2.0) == [0.0] * 8
    assert logic.spread_level(0.5, 0, t=2.0) == []


def test_spread_level_deterministic() -> None:
    assert logic.spread_level(0.6, 16, 3.0) == logic.spread_level(0.6, 16, 3.0)


def test_resample() -> None:
    assert logic.resample([], 4) == [0.0] * 4
    assert logic.resample([0.5], 3) == [0.5] * 3
    up = logic.resample([0.0, 1.0], 5)
    assert up == pytest.approx([0.0, 0.25, 0.5, 0.75, 1.0])
    down = logic.resample([0.0, 0.5, 1.0], 2)
    assert down == pytest.approx([0.0, 1.0])
    assert logic.resample([0.2, 0.4], 0) == []
    assert all(0.0 <= v <= 1.0 for v in logic.resample([5.0, -3.0], 4))


# -- particle field ---------------------------------------------------------------------


def test_particle_field_count_capped() -> None:
    field = logic.ParticleField(10_000, 800, 600, seed=1)
    assert len(field.particles) == logic.MAX_PARTICLES
    assert len(logic.ParticleField(5, 800, 600, seed=1).particles) == 5
    assert len(logic.ParticleField(-3, 800, 600, seed=1).particles) == 0


def test_particle_field_step_moves_and_wraps() -> None:
    field = logic.ParticleField(20, 200, 100, seed=42)
    before = [(p.x, p.y) for p in field.particles]
    for _ in range(50):
        field.step(0.1)
    after = [(p.x, p.y) for p in field.particles]
    assert before != after
    for x, y in after:
        assert 0.0 <= x < 200.0
        assert 0.0 <= y < 100.0


def test_particle_field_step_clamps_dt() -> None:
    field = logic.ParticleField(10, 300, 300, seed=7)
    field.step(1e9)  # absurd dt (after a long pause) must not explode positions
    for particle in field.particles:
        assert 0.0 <= particle.x < 300.0
        assert 0.0 <= particle.y < 300.0


def test_particle_field_connections() -> None:
    field = logic.ParticleField(0, 100, 100, seed=0)
    field.particles = [
        logic.Particle(x=10.0, y=10.0, vx=0.0, vy=0.0, size=1.0),
        logic.Particle(x=13.0, y=14.0, vx=0.0, vy=0.0, size=1.0),  # distance 5
        logic.Particle(x=90.0, y=90.0, vx=0.0, vy=0.0, size=1.0),  # far away
    ]
    pairs = field.connections(10.0)
    assert len(pairs) == 1
    i, j, strength = pairs[0]
    assert (i, j) == (0, 1)
    assert strength == pytest.approx(0.5)
    assert field.connections(0.0) == []


def test_particle_field_resize_rescales() -> None:
    field = logic.ParticleField(0, 100, 100, seed=0)
    field.particles = [logic.Particle(x=50.0, y=25.0, vx=0.0, vy=0.0, size=1.0)]
    field.resize(200, 400)
    assert field.particles[0].x == pytest.approx(100.0)
    assert field.particles[0].y == pytest.approx(100.0)
    assert field.width == 200.0
    assert field.height == 400.0


# -- activity feed ------------------------------------------------------------------------


def test_activity_feed_ring_buffer() -> None:
    feed = logic.ActivityFeed(capacity=3)
    for index in range(5):
        feed.append(f"line {index}")
    assert len(feed) == 3
    assert feed.items() == ["line 2", "line 3", "line 4"]
    # items() returns a copy, not the internal list.
    feed.items().append("mutation")
    assert len(feed) == 3


def test_activity_feed_minimum_capacity() -> None:
    feed = logic.ActivityFeed(capacity=0)
    feed.append("a")
    feed.append("b")
    assert feed.items() == ["b"]


def test_format_event() -> None:
    assert logic.format_event("voice.level", {"level": 0.5}) is None
    line = logic.format_event("agent.tool_call", {"agent": "coder", "tool": "python_run"})
    assert line is not None
    assert "coder" in line
    assert "python_run" in line
    result_line = logic.format_event("agent.tool_result", {"tool": "web_search"})
    assert result_line is not None
    assert "web_search" in result_line
    started = logic.format_event("app.started", {"subsystems": ["voice", "vision"]})
    assert started is not None
    assert "voice, vision" in started
    assert logic.format_event("app.started", {"subsystems": []}) == "systems online: core"
    assert logic.format_event("agent.finished", {}) == "agent finished"
    assert logic.format_event("custom.topic", {}) == "custom.topic"


def test_spread_and_decay_pipeline_stays_bounded() -> None:
    """Full animation pipeline: bars always remain valid alphas/lengths."""
    bars = [0.0] * 48
    for frame in range(120):
        t = frame / 60.0
        targets = logic.spread_level(abs(math.sin(t * 2.0)), 48, t)
        bars = logic.decay_spectrum(bars, targets)
        assert all(0.0 <= b <= 1.0 for b in bars)


# -- optional offscreen smoke test ---------------------------------------------------------

_SMOKE_SCRIPT = """
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from jarvis.core.config import JarvisConfig
from jarvis.gui.main_window import JarvisMainWindow


class StubBridge(QObject):
    delta = Signal(str)
    answer = Signal(str)
    event = Signal(str, object)
    level = Signal(float)
    started = Signal(object)
    error = Signal(str)

    def send_text(self, text: str) -> None:
        self.delta.emit("echo: " + text)

    def shutdown(self) -> None:
        pass


app = QApplication([])
config = JarvisConfig()
bridge = StubBridge()
window = JarvisMainWindow(config, bridge)

# Exercise the signal wiring end to end.
bridge.started.emit({"agents": ["jarvis", "coder"], "subsystems": ["voice"]})
bridge.event.emit("agent.tool_call", {"agent": "coder", "tool": "python_run"})
bridge.level.emit(0.75)
bridge.delta.emit("Good evening")
bridge.delta.emit(", sir.")
bridge.answer.emit("Good evening, sir.")
bridge.error.emit("simulated fault")

# Paint in wide mode, then in narrow mode.
window.resize(1400, 800)
pixmap = window.grab()
assert not pixmap.isNull() and pixmap.width() > 0, "wide-mode grab failed"
window.resize(900, 700)
pixmap = window.grab()
assert not pixmap.isNull() and pixmap.width() > 0, "narrow-mode grab failed"
print("SMOKE OK")
"""


def test_main_window_offscreen_smoke() -> None:
    """Create the HUD with a stub bridge and paint it once (offscreen)."""
    pytest.importorskip("PySide6")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, "-c", _SMOKE_SCRIPT],
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
        timeout=120,
        check=False,
    )
    if result.returncode != 0 and any(
        marker in result.stderr
        for marker in ("could not be loaded", "libEGL", "libGL", "xcb")
    ):
        pytest.skip(f"Qt offscreen platform unavailable: {result.stderr[-200:]}")
    assert result.returncode == 0, result.stderr
    assert "SMOKE OK" in result.stdout
