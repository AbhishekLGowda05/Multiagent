from __future__ import annotations

import os
from typing import Any
from datetime import datetime, timezone, timedelta

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
    title: str,
    start_time: datetime | str,
    end_time: datetime | str,
    *,
    time_zone: str = "UTC",
    description: str | None = None,
    recurrence: list[str] | None = None,
) -> Any:
    """Create a calendar event on the user's primary calendar."""
    
    # Check if running in mock mode or credentials are missing  
    if os.getenv("MOCK_GOOGLE_APIS") == "true" or not os.path.exists("credentials.json"):
        print(f"[MOCK] 📅 Would create event: {title}")
        print(f"[MOCK] 📅 Start: {start_time}")
        print(f"[MOCK] 📅 End: {end_time}")
        return {"id": f"mock_event_{hash(title + str(start_time))}", "status": "mock_created"}
    
    try:
        creds = get_credentials(CALENDAR_SCOPES)
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": title,
            "start": {"dateTime": _to_iso(start_time), "timeZone": time_zone},
            "end": {"dateTime": _to_iso(end_time), "timeZone": time_zone},
        }
        if description:
            event["description"] = description
        if recurrence:
            event["recurrence"] = recurrence

        result = (
            service.events()
            .insert(calendarId="primary", body=event)
            .execute()
        )
        print(f"📅 Created event: {title}. Event ID: {result['id']}")
        return result
    except Exception as e:
        print(f"[ERROR] Calendar event creation failed: {e}")
        print(f"[INFO] You may need to set up Google API credentials. See SETUP_GOOGLE_CREDENTIALS.md")
        raise e

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
        event["recurrence"] = recurrence

    if recurrence is not None:
        event["recurrence"] = (
            recurrence if isinstance(recurrence, list) else [recurrence]
        )

    
    result = service.events().insert(calendarId="primary", body=event).execute()
    print(
        f"📅 Created recurring event '{summary}' from {start_iso} to {end_iso}"
    )
    return result


def create_recurring_event(
    summary: str,
    start_time: datetime | str,
    end_time: datetime | str,
    recurrence_rule: str,
    *,
    time_zone: str = "UTC",
    description: str | None = None,
) -> Any:
    """Create a recurring calendar event with custom recurrence rules."""
    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)

    start_iso = _to_iso(start_time)
    end_iso = _to_iso(end_time)

    event = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": time_zone},
        "end": {"dateTime": end_iso, "timeZone": time_zone},
        "recurrence": [recurrence_rule],
    }
    
    if description is not None:
        event["description"] = description

    result = service.events().insert(calendarId="primary", body=event).execute()
    print(f"📅 Created recurring event '{summary}' with rule: {recurrence_rule}")
    return result


def build_daily_rrule(count: int = 30) -> str:
    """Build a daily recurrence rule for Google Calendar.
    
    Args:
        count: Number of occurrences (default: 30 days)
    
    Returns:
        RFC 5545 RRULE string for daily recurrence
    """
    return f"RRULE:FREQ=DAILY;COUNT={count}"


def build_weekly_rrule(count: int = 12, by_day: str | None = None) -> str:
    """Build a weekly recurrence rule for Google Calendar.
    
    Args:
        count: Number of occurrences (default: 12 weeks)
        by_day: Day of week (e.g., 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU')
    
    Returns:
        RFC 5545 RRULE string for weekly recurrence
    """
    rule = f"RRULE:FREQ=WEEKLY;COUNT={count}"
    if by_day:
        rule += f";BYDAY={by_day}"
    return rule


def build_monthly_rrule(count: int = 12, by_month_day: int | None = None) -> str:
    """Build a monthly recurrence rule for Google Calendar.
    
    Args:
        count: Number of occurrences (default: 12 months)
        by_month_day: Day of month (1-31)
    
    Returns:
        RFC 5545 RRULE string for monthly recurrence
    """
    rule = f"RRULE:FREQ=MONTHLY;COUNT={count}"
    if by_month_day:
        rule += f";BYMONTHDAY={by_month_day}"
    return rule


def build_interval_rrule(frequency: str, interval: int, count: int = 10) -> str:
    """Build a custom interval recurrence rule for Google Calendar.
    
    Args:
        frequency: DAILY, WEEKLY, MONTHLY, or YEARLY
        interval: Interval between recurrences (e.g., 2 for every 2 weeks)
        count: Number of occurrences
    
    Returns:
        RFC 5545 RRULE string for interval-based recurrence
    """
    return f"RRULE:FREQ={frequency.upper()};INTERVAL={interval};COUNT={count}"


def build_weekly_rrule(count: int = 12, by_day: str | None = None) -> str:
    """Build a weekly recurrence rule for Google Calendar.
    
    Args:
        count: Number of occurrences (default: 12 weeks)
        by_day: Day of week (e.g., 'MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU')
    
    Returns:
        RFC 5545 RRULE string for weekly recurrence
    """
    rule = f"RRULE:FREQ=WEEKLY;COUNT={count}"
    if by_day:
        rule += f";BYDAY={by_day}"
    return rule


def build_monthly_rrule(count: int = 12, by_month_day: int | None = None) -> str:
    """Build a monthly recurrence rule for Google Calendar.
    
    Args:
        count: Number of occurrences (default: 12 months)
        by_month_day: Day of month (1-31)
    
    Returns:
        RFC 5545 RRULE string for monthly recurrence
    """
    rule = f"RRULE:FREQ=MONTHLY;COUNT={count}"
    if by_month_day:
        rule += f";BYMONTHDAY={by_month_day}"
    return rule


def build_date_range_rrule(start_date: str, end_date: str, frequency: str = "DAILY") -> str:
    """Build a recurrence rule for a specific date range.
    
    Args:
        start_date: Start date in ISO format
        end_date: End date in ISO format (converted to UNTIL format)
        frequency: DAILY, WEEKLY, MONTHLY
    
    Returns:
        RFC 5545 RRULE string with date range
    """
    # Convert end_date to UNTIL format (YYYYMMDDTHHMMSSZ)
    if end_date.endswith('Z'):
        until_date = end_date.replace('-', '').replace(':', '')
    else:
        until_date = end_date.replace('-', '').replace(':', '') + 'Z'
    
    return f"RRULE:FREQ={frequency.upper()};UNTIL={until_date}"


def create_recurring_events_for_month(
    summary: str,
    month: int,
    year: int,
    hour: int,
    minute: int,
    interval_days: int = 1,
    description: str = ""
) -> dict:
    """Create recurring events for an entire month.
    
    Args:
        summary: Event title
        month: Month number (1-12)
        year: Year
        hour: Hour (0-23)
        minute: Minute (0-59)
        interval_days: Interval between events (1 = daily, 4 = every 4 days)
        description: Event description
    
    Returns:
        Result from Google Calendar API
    """
    from calendar import monthrange
    
    # Get the last day of the month
    _, last_day = monthrange(year, month)
    
    # Create start and end datetime
    start_time = datetime(year, month, 1, hour, minute)
    end_time = datetime(year, month, last_day, hour + 1, minute)  # +1 hour duration
    
    # Build recurrence rule
    if interval_days == 1:
        recurrence_rule = f"RRULE:FREQ=DAILY;UNTIL={end_time.strftime('%Y%m%dT%H%M%SZ')}"
    else:
        recurrence_rule = f"RRULE:FREQ=DAILY;INTERVAL={interval_days};UNTIL={end_time.strftime('%Y%m%dT%H%M%SZ')}"
    
    return create_recurring_event(
        summary,
        start_time.isoformat() + "Z",
        (start_time + timedelta(hours=1)).isoformat() + "Z",
        recurrence_rule,
        description=description
    )


def list_events(max_results: int = 10) -> list:
    """List calendar events."""
    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)
    
    events_result = service.events().list(
        calendarId="primary", 
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    
    return events_result.get("items", [])


def delete_event(event_id: str) -> None:
    """Delete a calendar event by id."""

    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    print(f"🗑️ Deleted event id: {event_id}")

