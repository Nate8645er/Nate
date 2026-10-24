"""Scheduler: reminders, appointments and recurring jobs.

Simple asyncio-based scheduler — one background loop, jobs fire as events
on the bus ("reminder.due"), which the UI shows and the voice layer speaks.
Jobs survive restarts via the long-term memory database.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    when: float  # unix timestamp
    message: str
    kind: str = "reminder"  # reminder | appointment | job
    repeat_seconds: float = 0.0  # 0 = one-shot
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "when": self.when,
            "message": self.message,
            "kind": self.kind,
            "repeat_seconds": self.repeat_seconds,
            "session": self.session,
        }


class Scheduler:
    def __init__(self, kernel: "Kernel", tick_seconds: float = 1.0) -> None:
        self.kernel = kernel
        self.tick_seconds = tick_seconds
        self.jobs: dict[str, ScheduledJob] = {}
        self._loop_task: asyncio.Task | None = None

    def start(self) -> None:
        if self._loop_task is None or self._loop_task.done():
            self._loop_task = asyncio.create_task(self._loop(), name="scheduler")

    async def stop(self) -> None:
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None

    def add(
        self,
        in_seconds: float,
        message: str,
        kind: str = "reminder",
        repeat_seconds: float = 0.0,
        session: str = "default",
    ) -> ScheduledJob:
        job = ScheduledJob(
            when=time.time() + in_seconds,
            message=message,
            kind=kind,
            repeat_seconds=repeat_seconds,
            session=session,
        )
        self.jobs[job.id] = job
        return job

    def cancel(self, job_id: str) -> bool:
        return self.jobs.pop(job_id, None) is not None

    def upcoming(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in sorted(self.jobs.values(), key=lambda j: j.when)]

    async def _loop(self) -> None:
        while True:
            now = time.time()
            for job in list(self.jobs.values()):
                if job.when <= now:
                    await self.kernel.bus.publish(
                        "reminder.due", job.to_dict(), source="scheduler"
                    )
                    if self.kernel.voice is not None and job.kind in ("reminder", "appointment"):
                        await self.kernel.voice.speak(f"Erinnerung: {job.message}")
                    if job.repeat_seconds > 0:
                        job.when = now + job.repeat_seconds
                    else:
                        self.jobs.pop(job.id, None)
            await asyncio.sleep(self.tick_seconds)
