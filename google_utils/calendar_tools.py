from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

try:
    import dateparser  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    dateparser = None

from googleapiclient.discovery import build

from .auth import get_credentials

# Calendar scope for creating events
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _to_iso(dt: datetime | str) -> str:
    """Convert a datetime or natural language string to an ISO 8601 string."""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    if isinstance(dt, str):
        parsed = None
        if dateparser:
            try:
                parsed = dateparser.parse(dt)
            except Exception:
                parsed = None
        if parsed:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.isoformat()
    return dt


def create_event(
    summary: str,
    start_time: datetime | str,
    end_time: datetime | str,
    *,
    time_zone: str = "UTC",
    description: str | None = None,
) -> Any:

    """Create a calendar event on the user's primary calendar."""

    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)

    start_iso = _to_iso(start_time)
    end_iso = _to_iso(end_time)

    event = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": time_zone},
        "end": {"dateTime": end_iso, "timeZone": time_zone},
    }
    if description is not None:
        event["description"] = description

    result = service.events().insert(calendarId="primary", body=event).execute()
    print(f"📅 Created event '{summary}' from {start_iso} to {end_iso}")
    return result


def build_daily_rrule(start: datetime, end: datetime) -> str:
    """Return an RRULE string for daily events between start and end dates."""
    until = end.strftime("%Y%m%dT%H%M%SZ")
    return f"RRULE:FREQ=DAILY;UNTIL={until}"


def build_interval_rrule(interval_days: int, start: datetime, end: datetime) -> str:
    """Return an RRULE string for events repeating every N days."""
    until = end.strftime("%Y%m%dT%H%M%SZ")
    return f"RRULE:FREQ=DAILY;INTERVAL={interval_days};UNTIL={until}"


def create_recurring_event(
    summary: str,
    start_time: datetime | str,
    end_time: datetime | str,
    rrule: str,
    *,
    time_zone: str = "UTC",
    description: str | None = None,
) -> Any:
    """Create a recurring event using an RRULE string."""

    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)

    start_iso = _to_iso(start_time)
    end_iso = _to_iso(end_time)

    event = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": time_zone},
        "end": {"dateTime": end_iso, "timeZone": time_zone},
        "recurrence": [rrule],
    }
    if description is not None:
        event["description"] = description

    result = service.events().insert(calendarId="primary", body=event).execute()
    print(
        f"📅 Created recurring event '{summary}' from {start_iso} to {end_iso}"
    )
    return result

