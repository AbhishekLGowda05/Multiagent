from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Any

from googleapiclient.discovery import build

from .auth import get_credentials

# Gmail scope for sending messages
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def send_email(to_email: str, subject: str, body: str) -> Any:
    """Send an email using the Gmail API."""
    creds = get_credentials(GMAIL_SCOPES)
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    return service.users().messages().send(userId="me", body=create_message).execute()
