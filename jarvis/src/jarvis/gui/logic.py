"""Pure-Python animation, layout and feed math for the JARVIS HUD.

Everything in this module is Qt-free so it can be unit-tested without
PySide6 or a display. The widgets in :mod:`jarvis.gui.widgets` are thin
painting shells around these functions.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

# -- scalar helpers -----------------------------------------------------------------


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp ``value`` into ``[lo, hi]``."""
    return lo if value < lo else hi if value > hi else value


def smooth_level(current: float, target: float, attack: float = 0.55, release: float = 0.10) -> float:
    """Move ``current`` towards ``target`` asymmetrically.

    Rises fast (``attack``) and falls slowly (``release``), which reads as a
    natural voice meter: instant response, gentle decay. Both coefficients are
    per-frame blend factors in ``[0, 1]``.
    """
    coefficient = attack if target > current else release
    return clamp(current + (target - current) * clamp(coefficient))


def breathing(t: float, period: float = 4.0, floor: float = 0.08, amplitude: float = 0.10) -> float:
    """Idle "breathing" level: a slow sine between ``floor`` and ``floor + amplitude``."""
    if period <= 0:
        return clamp(floor)
    phase = (t % period) / period * math.tau
    return clamp(floor + amplitude * 0.5 * (1.0 + math.sin(phase)))


def advance_angle(angle: float, speed: float, dt: float, boost: float = 0.0, boost_gain: float = 2.5) -> float:
    """Advance a rotation ``angle`` (degrees) by ``speed`` deg/s over ``dt`` seconds.

    ``boost`` (0..1, e.g. the voice level) multiplies the speed by up to
    ``1 + boost_gain`` so the HUD visibly spins up while JARVIS listens.
    The result is wrapped into ``[0, 360)``; negative speeds rotate backwards.
    """
    factor = 1.0 + clamp(boost) * max(boost_gain, 0.0)
    return (angle + speed * factor * dt) % 360.0


def layout_mode(width: int, threshold: int = 1080) -> str:
    """Decide the responsive layout: ``"wide"`` (chat column right) or ``"narrow"``."""
    return "wide" if width >= threshold else "narrow"


# -- spectrum helpers ---------------------------------------------------------------


def decay_spectrum(
    bars: list[float],
    targets: list[float],
    attack: float = 0.60,
    decay: float = 0.12,
) -> list[float]:
    """Blend spectrum ``bars`` towards ``targets`` with fast attack / slow decay.

    Lengths may differ; the result always has ``len(bars)`` entries and missing
    targets are treated as ``0.0``. All values are clamped to ``[0, 1]``.
    """
    result: list[float] = []
    for index, current in enumerate(bars):
        target = clamp(targets[index]) if index < len(targets) else 0.0
        result.append(smooth_level(clamp(current), target, attack=attack, release=decay))
    return result


def spread_level(level: float, count: int, t: float) -> list[float]:
    """Expand a single loudness ``level`` into ``count`` pseudo-spectrum bars.

    Deterministic in ``(level, count, t)``: each bar gets a phase-shifted
    wobble so the ring shimmers instead of pumping uniformly. Every bar stays
    within ``[0, level]``.
    """
    level = clamp(level)
    if count <= 0 or level <= 0.0:
        return [0.0] * max(count, 0)
    golden = 2.399963  # golden angle in radians, decorrelates neighbouring bars
    bars: list[float] = []
    for index in range(count):
        wobble = 0.5 + 0.5 * math.sin(t * 6.0 + index * golden)
        bars.append(clamp(level * (0.35 + 0.65 * wobble), 0.0, level))
    return bars


def resample(values: list[float], count: int) -> list[float]:
    """Linearly resample ``values`` to ``count`` entries (clamped to ``[0, 1]``)."""
    if count <= 0:
        return []
    if not values:
        return [0.0] * count
    if len(values) == 1:
        return [clamp(values[0])] * count
    result: list[float] = []
    span = len(values) - 1
    for index in range(count):
        position = index * span / max(count - 1, 1)
        low = int(position)
        high = min(low + 1, span)
        fraction = position - low
        result.append(clamp(values[low] * (1.0 - fraction) + values[high] * fraction))
    return result


# -- particle field -----------------------------------------------------------------

MAX_PARTICLES = 96


@dataclass(slots=True)
class Particle:
    """A single drifting star of the background field."""

    x: float
    y: float
    vx: float
    vy: float
    size: float


class ParticleField:
    """Star-field/plexus simulation: drifting points with wrap-around edges."""

    def __init__(
        self,
        count: int,
        width: float,
        height: float,
        seed: int | None = None,
        min_speed: float = 6.0,
        max_speed: float = 24.0,
    ) -> None:
        self.width = max(width, 1.0)
        self.height = max(height, 1.0)
        self._rng = random.Random(seed)
        self._min_speed = min_speed
        self._max_speed = max_speed
        self.particles: list[Particle] = [
            self._spawn() for _ in range(min(max(count, 0), MAX_PARTICLES))
        ]

    def _spawn(self) -> Particle:
        angle = self._rng.uniform(0.0, math.tau)
        speed = self._rng.uniform(self._min_speed, self._max_speed)
        return Particle(
            x=self._rng.uniform(0.0, self.width),
            y=self._rng.uniform(0.0, self.height),
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed,
            size=self._rng.uniform(0.8, 2.4),
        )

    def resize(self, width: float, height: float) -> None:
        """Rescale particle positions proportionally to the new bounds."""
        width = max(width, 1.0)
        height = max(height, 1.0)
        scale_x = width / self.width
        scale_y = height / self.height
        for particle in self.particles:
            particle.x *= scale_x
            particle.y *= scale_y
        self.width = width
        self.height = height

    def step(self, dt: float) -> None:
        """Advance the simulation by ``dt`` seconds, wrapping at the edges."""
        dt = clamp(dt, 0.0, 0.25)  # guard against huge jumps after a pause
        for particle in self.particles:
            particle.x = (particle.x + particle.vx * dt) % self.width
            particle.y = (particle.y + particle.vy * dt) % self.height

    def connections(self, threshold: float) -> list[tuple[int, int, float]]:
        """Return ``(i, j, strength)`` for particle pairs closer than ``threshold``.

        ``strength`` fades linearly from 1.0 (touching) to 0.0 (at threshold),
        ready to be used as a line alpha.
        """
        if threshold <= 0.0:
            return []
        threshold_sq = threshold * threshold
        pairs: list[tuple[int, int, float]] = []
        particles = self.particles
        for i in range(len(particles)):
            for j in range(i + 1, len(particles)):
                dx = particles[i].x - particles[j].x
                dy = particles[i].y - particles[j].y
                dist_sq = dx * dx + dy * dy
                if dist_sq < threshold_sq:
                    pairs.append((i, j, 1.0 - math.sqrt(dist_sq) / threshold))
        return pairs


# -- activity feed ------------------------------------------------------------------


class ActivityFeed:
    """Bounded ring buffer of activity lines for the status panel."""

    def __init__(self, capacity: int = 200) -> None:
        self.capacity = max(capacity, 1)
        self._items: list[str] = []

    def append(self, line: str) -> None:
        """Append a line, evicting the oldest entries beyond ``capacity``."""
        self._items.append(line)
        overflow = len(self._items) - self.capacity
        if overflow > 0:
            del self._items[:overflow]

    def items(self) -> list[str]:
        """Return a copy of the buffered lines, oldest first."""
        return list(self._items)

    def __len__(self) -> int:
        return len(self._items)


_QUIET_TOPICS = ("voice.level",)


def format_event(topic: str, data: dict[str, object]) -> str | None:
    """Render an EventBus event as one activity-feed line.

    Returns ``None`` for high-frequency topics that would flood the feed
    (e.g. ``voice.level``).
    """
    if topic in _QUIET_TOPICS:
        return None
    agent = data.get("agent", "")
    if topic == "agent.tool_call":
        return f"{agent or 'agent'} > tool {data.get('tool', '?')}"
    if topic == "agent.tool_result":
        return f"{agent or 'agent'} < tool {data.get('tool', '?')} done"
    if topic == "agent.finished":
        return f"{agent or 'agent'} finished"
    if topic == "app.started":
        subsystems = data.get("subsystems") or []
        names = ", ".join(str(s) for s in subsystems) if isinstance(subsystems, list) else ""
        return f"systems online: {names or 'core'}"
    if topic == "chat.answer":
        return "answer delivered"
    return topic
