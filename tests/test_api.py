import base64
from email.mime.text import MIMEText

import pytest

from google_utils import gmail_tools, calendar_tools


class DummyExecute:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self.data


class DummyGmailMessages:
    def __init__(self):
        self.sent = []
        self.deleted = []
        self.query = None

    def send(self, userId=None, body=None):
        self.sent.append(body)
        return DummyExecute({"id": "msg1"})

    def list(self, userId=None, q=""):
        self.query = q
        return DummyExecute({"messages": [{"id": "msg1"}, {"id": "msg2"}]})

    def delete(self, userId=None, id=None):
        self.deleted.append(id)
        return DummyExecute({})


class DummyGmailUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages


class DummyGmailService:
    def __init__(self):
        self.msg = DummyGmailMessages()

    def users(self):
        return DummyGmailUsers(self.msg)


def patch_gmail(monkeypatch):
    service = DummyGmailService()
    monkeypatch.setattr(gmail_tools, "get_credentials", lambda scopes: None)
    monkeypatch.setattr(gmail_tools, "build", lambda *a, **k: service)
    return service


class DummyCalendarEvents:
    def __init__(self):
        self.inserted = []
        self.deleted = []

    def insert(self, calendarId=None, body=None):
        self.inserted.append(body)
        return DummyExecute({"id": "evt1"})

    def delete(self, calendarId=None, eventId=None):
        self.deleted.append(eventId)
        return DummyExecute({})


class DummyCalendarService:
    def __init__(self):
        self.ev = DummyCalendarEvents()

    def events(self):
        return self.ev


def patch_calendar(monkeypatch):
    service = DummyCalendarService()
    monkeypatch.setattr(calendar_tools, "get_credentials", lambda scopes: None)
    monkeypatch.setattr(calendar_tools, "build", lambda *a, **k: service)
    return service


def test_send_email_with_chart_data(monkeypatch):
    service = patch_gmail(monkeypatch)

    body = "Here is a chart"
    result = gmail_tools.send_email("user@example.com", "Report", body)

    msg = MIMEText(body)
    msg["To"] = "user@example.com"
    msg["From"] = "me"
    msg["Subject"] = "Report"
    expected_raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    assert result == {"id": "msg1"}
    assert service.msg.sent[0] == {"raw": expected_raw}


def test_read_and_delete_emails(monkeypatch):
    service = patch_gmail(monkeypatch)

    messages = gmail_tools.read_emails("test")
    assert messages == [{"id": "msg1"}, {"id": "msg2"}]
    assert service.msg.query == "test"

    gmail_tools.delete_email("msg1")
    assert "msg1" in service.msg.deleted


def test_create_and_delete_events(monkeypatch):
    service = patch_calendar(monkeypatch)

    event = calendar_tools.create_event(
        "Meeting",
        "2024-01-01T00:00:00Z",
        "2024-01-01T01:00:00Z",
    )
    assert event == {"id": "evt1"}
    assert service.ev.inserted[0]["summary"] == "Meeting"

    calendar_tools.delete_event("evt1")
    assert "evt1" in service.ev.deleted


def test_create_recurring_event(monkeypatch):
    service = patch_calendar(monkeypatch)

    rec = ["RRULE:FREQ=DAILY;COUNT=2"]
    calendar_tools.create_event(
        "Daily Standup",
        "2024-01-01T00:00:00Z",
        "2024-01-01T01:00:00Z",
        recurrence=rec,
    )
    assert service.ev.inserted[0]["recurrence"] == rec

