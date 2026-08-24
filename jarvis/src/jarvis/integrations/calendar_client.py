"""Calendar integrations: a local ICS file plus optional Google Calendar.

:class:`LocalCalendarClient` keeps a single ``calendar.ics`` file in the app
data directory. Parsing and writing use a small pure-stdlib implementation of
the RFC 5545 subset needed for VEVENT blocks (DTSTART/DTEND/SUMMARY/
DESCRIPTION/UID with basic text escaping). No external calendar library is
used. Naive timestamps are interpreted as UTC.

:class:`GoogleCalendarClient` talks to the Google Calendar REST API for the
primary calendar.

Environment variables:

* ``GOOGLE_OAUTH_TOKEN`` -- OAuth2 access token with calendar scope
  (enables ``gcal_list_events`` / ``gcal_add_event``). The local calendar
  needs no environment variables and is always available.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env, register_tool

_ICS_DT_FORMATS = ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y%m%d")


def _escape_text(value: str) -> str:
    """Apply RFC 5545 TEXT escaping."""
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _unescape_text(value: str) -> str:
    """Reverse RFC 5545 TEXT escaping."""
    result: list[str] = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            result.append("\n" if nxt in ("n", "N") else nxt)
            i += 2
        else:
            result.append(ch)
            i += 1
    return "".join(result)


def _parse_ics_datetime(value: str) -> datetime | None:
    value = value.strip()
    for fmt in _ICS_DT_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=UTC)
    return None


def _format_ics_datetime(value: datetime) -> str:
    return _as_utc(value).strftime("%Y%m%dT%H%M%SZ")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _unfold(text: str) -> list[str]:
    """Undo RFC 5545 line folding (continuation lines start with a space/tab)."""
    lines: list[str] = []
    for raw in text.splitlines():
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw.rstrip("\r"))
    return lines


@dataclass(slots=True)
class CalendarEvent:
    """A single parsed VEVENT."""

    uid: str
    summary: str
    description: str
    start: datetime | None
    end: datetime | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "summary": self.summary,
            "description": self.description,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
        }


class LocalCalendarClient:
    """Reads and appends VEVENTs in one local ``.ics`` file (no env vars needed)."""

    service = "calendar"

    def __init__(self, path: Path) -> None:
        self.path = path

    # -- ICS handling -----------------------------------------------------------

    def _parse(self) -> list[CalendarEvent]:
        if not self.path.is_file():
            return []
        events: list[CalendarEvent] = []
        current: dict[str, str] | None = None
        for line in _unfold(self.path.read_text(encoding="utf-8")):
            if line == "BEGIN:VEVENT":
                current = {}
            elif line == "END:VEVENT" and current is not None:
                events.append(
                    CalendarEvent(
                        uid=current.get("UID", ""),
                        summary=_unescape_text(current.get("SUMMARY", "")),
                        description=_unescape_text(current.get("DESCRIPTION", "")),
                        start=_parse_ics_datetime(current.get("DTSTART", "")),
                        end=_parse_ics_datetime(current.get("DTEND", "")),
                    )
                )
                current = None
            elif current is not None and ":" in line:
                key, _, value = line.partition(":")
                current[key.split(";", 1)[0].upper()] = value
        return events

    def _write_vevent(self, vevent_lines: list[str]) -> None:
        skeleton = "\r\n".join(
            ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//JARVIS//EN", "END:VCALENDAR", ""]
        )
        text = self.path.read_text(encoding="utf-8") if self.path.is_file() else skeleton
        marker = "END:VCALENDAR"
        index = text.rfind(marker)
        if index < 0:
            text = skeleton
            index = text.rfind(marker)
        block = "\r\n".join(vevent_lines) + "\r\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text[:index] + block + text[index:], encoding="utf-8")

    # -- operations -----------------------------------------------------------

    def list_events(self, days: int = 7, limit: int = 25) -> list[dict[str, Any]]:
        """Return events starting within the next *days* days, soonest first."""
        now = datetime.now(UTC)
        horizon = now + timedelta(days=max(1, int(days)))
        upcoming = [
            event
            for event in self._parse()
            if event.start is not None and now <= event.start <= horizon
        ]
        upcoming.sort(key=lambda event: event.start or now)
        return [event.as_dict() for event in upcoming[: max(1, int(limit))]]

    def add_event(
        self,
        summary: str,
        start: str,
        end: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """Append a VEVENT. *start*/*end* are ISO 8601; *end* defaults to +1 hour."""
        try:
            start_dt = _as_utc(datetime.fromisoformat(start))
            end_dt = _as_utc(datetime.fromisoformat(end)) if end else start_dt + timedelta(hours=1)
        except ValueError as exc:
            raise IntegrationError(f"calendar: invalid ISO datetime: {exc}", cause=exc) from exc
        uid = f"{uuid.uuid4()}@jarvis"
        lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{_format_ics_datetime(datetime.now(UTC))}",
            f"DTSTART:{_format_ics_datetime(start_dt)}",
            f"DTEND:{_format_ics_datetime(end_dt)}",
            f"SUMMARY:{_escape_text(summary)}",
        ]
        if description:
            lines.append(f"DESCRIPTION:{_escape_text(description)}")
        lines.append("END:VEVENT")
        self._write_vevent(lines)
        return CalendarEvent(uid, summary, description, start_dt, end_dt).as_dict()

    # -- tools -----------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        register_tool(
            app,
            name="calendar_list_events",
            description="List events from the local JARVIS calendar for the next N days.",
            handler=self.list_events,
            parameters={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 7, "minimum": 1},
                    "limit": {"type": "integer", "default": 25, "minimum": 1},
                },
            },
            service=self.service,
        )
        register_tool(
            app,
            name="calendar_add_event",
            description=(
                "Add an event to the local JARVIS calendar. Times are ISO 8601 "
                "(naive values are treated as UTC); end defaults to start + 1 hour."
            ),
            handler=self.add_event,
            parameters={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start": {"type": "string", "description": "ISO 8601 start time"},
                    "end": {"type": "string", "description": "ISO 8601 end time (optional)"},
                    "description": {"type": "string"},
                },
                "required": ["summary", "start"],
            },
            service=self.service,
            capability="files.write",
        )


class GoogleCalendarClient(IntegrationClient):
    """Google Calendar REST client for the primary calendar.

    Environment variables:

    * ``GOOGLE_OAUTH_TOKEN`` -- OAuth2 bearer token with
      ``https://www.googleapis.com/auth/calendar`` scope.
    """

    service = "gcal"

    def __init__(self, token: str, **kwargs: Any) -> None:
        super().__init__(
            base_url="https://www.googleapis.com/calendar/v3", token=token, **kwargs
        )

    @classmethod
    def from_env(cls) -> Self | None:
        token = env("GOOGLE_OAUTH_TOKEN")
        return cls(token) if token else None

    async def list_events(self, days: int = 7, limit: int = 25) -> list[dict[str, Any]]:
        """List upcoming primary-calendar events within the next *days* days."""
        now = datetime.now(UTC)
        response = await self._request(
            "GET",
            "/calendars/primary/events",
            params={
                "timeMin": now.isoformat(),
                "timeMax": (now + timedelta(days=max(1, int(days)))).isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": str(max(1, min(int(limit), 100))),
            },
        )
        items = response.json().get("items", [])
        return [
            {
                "id": item.get("id"),
                "summary": item.get("summary", ""),
                "start": item.get("start", {}).get("dateTime")
                or item.get("start", {}).get("date"),
                "end": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date"),
                "location": item.get("location", ""),
            }
            for item in items
        ]

    async def add_event(
        self,
        summary: str,
        start: str,
        end: str | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        """Insert an event into the primary calendar (ISO 8601 times)."""
        try:
            start_dt = _as_utc(datetime.fromisoformat(start))
            end_dt = _as_utc(datetime.fromisoformat(end)) if end else start_dt + timedelta(hours=1)
        except ValueError as exc:
            raise IntegrationError(f"gcal: invalid ISO datetime: {exc}", cause=exc) from exc
        response = await self._request(
            "POST",
            "/calendars/primary/events",
            json={
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_dt.isoformat()},
                "end": {"dateTime": end_dt.isoformat()},
            },
        )
        created = response.json()
        return {"id": created.get("id"), "htmlLink": created.get("htmlLink"), "summary": summary}

    def register_tools(self, app: Any) -> None:
        self._register_tool(
            app,
            name="gcal_list_events",
            description="List upcoming Google Calendar events (primary calendar).",
            handler=self.list_events,
            parameters={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "default": 7, "minimum": 1},
                    "limit": {"type": "integer", "default": 25, "minimum": 1},
                },
            },
        )
        self._register_tool(
            app,
            name="gcal_add_event",
            description="Create an event in the primary Google Calendar (ISO 8601 times).",
            handler=self.add_event,
            parameters={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "start": {"type": "string", "description": "ISO 8601 start time"},
                    "end": {"type": "string", "description": "ISO 8601 end time (optional)"},
                    "description": {"type": "string"},
                },
                "required": ["summary", "start"],
            },
            capability="integrations.send",
        )
