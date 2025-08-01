from __future__ import annotations

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, Iterable, Dict

from googleapiclient.discovery import build

from .auth import get_credentials

# Gmail scope for sending messages
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def send_email(
    to_email: str,
    subject: str,
    body: str,
    *,
    html: bool = False,
    attachments: Iterable[Dict[str, Any]] | None = None,
) -> Any:
    """Send an email using the Gmail API with optional HTML and attachments.

    Parameters
    ----------
    to_email : str
        Destination email address.
    subject : str
        Email subject line.
    body : str
        Email body text or HTML.
    html : bool, optional
        If ``True``, send the body as HTML.
    attachments : iterable of dict, optional
        Attachments with keys ``filename``, ``mime_type`` and ``data`` (bytes).
    """

    # Obtain OAuth2 credentials and build the Gmail service
    creds = get_credentials(GMAIL_SCOPES)
    service = build("gmail", "v1", credentials=creds)

    # Construct message - use multipart if html or attachments
    if html or attachments:
        message = MIMEMultipart()
        msg_body = MIMEText(body, "html" if html else "plain")
        message.attach(msg_body)

        if attachments:
            for att in attachments:
                data = att.get("data")
                filename = att.get("filename", "attachment")
                mime_type = att.get("mime_type", "application/octet-stream")
                maintype, subtype = mime_type.split("/", 1)
                part = MIMEBase(maintype, subtype)
                part.set_payload(data)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{filename}\"",
                )
                part.add_header("Content-Type", mime_type)
                message.attach(part)
    else:
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
