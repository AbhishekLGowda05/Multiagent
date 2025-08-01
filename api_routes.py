from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from googleapiclient.discovery import build

from google_utils.gmail_tools import send_email
from google_utils.calendar_tools import create_event, CALENDAR_SCOPES
from google_utils.auth import get_credentials

# Additional Gmail scopes for reading and deleting messages
GMAIL_MODIFY_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

app = FastAPI()


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class EventRequest(BaseModel):
    summary: str
    start_time: datetime
    end_time: datetime
    time_zone: str = "UTC"
    description: Optional[str] = None


@app.post("/email/send")
def send_email_endpoint(req: EmailRequest) -> Any:
    """Send an email using the helper utility."""
    result = send_email(req.to, req.subject, req.body)
    return result


@app.get("/email/read")
def read_email(q: Optional[str] = None, limit: int = 10) -> List[dict[str, Any]]:
    """Read messages from the user's Gmail inbox."""
    creds = get_credentials(GMAIL_MODIFY_SCOPES)
    service = build("gmail", "v1", credentials=creds)

    response = (
        service.users()
        .messages()
        .list(userId="me", q=q, maxResults=limit)
        .execute()
    )
    messages = []
    for msg_meta in response.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_meta["id"], format="full")
            .execute()
        )
        messages.append({"id": msg["id"], "snippet": msg.get("snippet")})
    return messages


@app.delete("/email/{message_id}")
def delete_email(message_id: str) -> dict[str, str]:
    """Delete a Gmail message by ID."""
    creds = get_credentials(GMAIL_MODIFY_SCOPES)
    service = build("gmail", "v1", credentials=creds)
    try:
        service.users().messages().delete(userId="me", id=message_id).execute()
    except Exception as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "deleted", "id": message_id}


@app.post("/calendar/create")
def create_calendar_event(req: EventRequest) -> Any:
    """Create a calendar event via the helper utility."""
    result = create_event(
        req.summary,
        req.start_time,
        req.end_time,
        time_zone=req.time_zone,
        description=req.description,
    )
    return result


@app.delete("/calendar/{event_id}")
def delete_calendar_event(event_id: str) -> dict[str, str]:
    """Delete a calendar event by ID."""
    creds = get_credentials(CALENDAR_SCOPES)
    service = build("calendar", "v3", credentials=creds)
    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
    except Exception as exc:  # pragma: no cover - network errors
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "deleted", "id": event_id}

