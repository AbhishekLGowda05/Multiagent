from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Any

from googleapiclient.discovery import build

from .auth import get_credentials

# Gmail scope for sending messages
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def send_email(to_email: str, subject: str, body: str) -> Any:
    """Send an email using the Gmail API.

    Parameters
    ----------
    to_email : str
        Destination email address.
    subject : str
        Email subject line.
    body : str
        Plain text body of the email.
    """

    # Obtain OAuth2 credentials and build the Gmail service
    creds = get_credentials(GMAIL_SCOPES)
    service = build("gmail", "v1", credentials=creds)

    # Construct a MIME message and encode it for transmission
    message = MIMEText(body)
    message["To"] = to_email
    message["From"] = "me"
    message["Subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    result = service.users().messages().send(userId="me", body=create_message).execute()

    # Basic logging to verify the email was sent
    print(f"📧 Sent email to {to_email}. Message id: {result.get('id')}")
    return result
