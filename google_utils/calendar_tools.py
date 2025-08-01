from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from googleapiclient.discovery import build

from .auth import get_credentials

# Calendar scope for creating events
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _to_iso(dt: datetime | str) -> str:
    """Convert a datetime or ISO string to an ISO 8601 string with UTC"""
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return dt


def create_event(
    summary: str,
    start_time: datetime | str,
    end_time: datetime | str,
    *,
    time_zone: str = "UTC",
    description: str | None = None,
    recurrence: str | list[str] | None = None,
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

    if recurrence is not None:
        event["recurrence"] = (
            recurrence if isinstance(recurrence, list) else [recurrence]
        )

    result = service.events().insert(calendarId="primary", body=event).execute()
    print(f"📅 Created event '{summary}' from {start_iso} to {end_iso}")
    return result
