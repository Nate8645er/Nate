"""Timer plugin: countdown timers that announce themselves over the event bus."""

from __future__ import annotations

import asyncio
import itertools
import time

from jarvis.plugins.api import Plugin, PluginContext, PluginManifest


class TimerPlugin(Plugin):
    manifest = PluginManifest(
        name="timer",
        version="1.0.0",
        description="Countdown timers with event-bus announcements (spoken if voice is active)",
        author="JARVIS",
        tags=["timer", "utility"],
    )

    def __init__(self) -> None:
        self._context: PluginContext | None = None
        self._timers: dict[int, tuple[str, float, asyncio.Task]] = {}
        self._ids = itertools.count(1)

    async def setup(self, context: PluginContext) -> None:
        self._context = context
        context.register_tool(
            "timer_set",
            "Start a countdown timer. When it finishes, JARVIS announces the label.",
            self.set_timer,
            parameters={
                "type": "object",
                "properties": {
                    "seconds": {"type": "integer", "description": "Duration in seconds"},
                    "label": {"type": "string", "description": "What the timer is for"},
                },
                "required": ["seconds"],
            },
            tags={"timer", "utility", "tasks"},
        )
        context.register_tool(
            "timer_list", "List running timers with remaining seconds.", self.list_timers,
            tags={"timer", "utility"},
        )
        context.register_tool(
            "timer_cancel",
            "Cancel a running timer by id.",
            self.cancel_timer,
            parameters={
                "type": "object",
                "properties": {"timer_id": {"type": "integer"}},
                "required": ["timer_id"],
            },
            tags={"timer", "utility"},
        )

    async def set_timer(self, seconds: int, label: str = "timer") -> str:
        if seconds <= 0 or seconds > 24 * 3600:
            return "Error: seconds must be between 1 and 86400"
        timer_id = next(self._ids)
        ends_at = time.monotonic() + seconds

        async def countdown() -> None:
            try:
                await asyncio.sleep(seconds)
                self._timers.pop(timer_id, None)
                if self._context is not None:
                    await self._context.events.publish(
                        "timer.finished", {"id": timer_id, "label": label}
                    )
            except asyncio.CancelledError:
                pass

        task = asyncio.get_running_loop().create_task(countdown())
        self._timers[timer_id] = (label, ends_at, task)
        return f"Timer #{timer_id} ('{label}') set for {seconds}s"

    def list_timers(self) -> str:
        if not self._timers:
            return "No timers running."
        now = time.monotonic()
        return "\n".join(
            f"#{timer_id}: {label} — {max(0, int(ends - now))}s remaining"
            for timer_id, (label, ends, _) in sorted(self._timers.items())
        )

    def cancel_timer(self, timer_id: int) -> str:
        entry = self._timers.pop(timer_id, None)
        if entry is None:
            return f"No timer #{timer_id}"
        entry[2].cancel()
        return f"Timer #{timer_id} cancelled"

    async def teardown(self) -> None:
        for _, _, task in self._timers.values():
            task.cancel()
        self._timers.clear()
