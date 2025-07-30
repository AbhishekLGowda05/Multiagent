from __future__ import annotations

from typing import Any

from googleapiclient.discovery import build

from .auth import get_credentials

# Calendar scope for creating events
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def create_event(summary: str, start_time: str, end_time: str) -> Any:
    """Create a calendar event on the user's primary calendar."""
    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    return service.events().insert(calendarId="primary", body=event).execute()
