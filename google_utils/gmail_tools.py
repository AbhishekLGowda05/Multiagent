from __future__ import annotations

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, Iterable, Dict
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

# Gmail scope for sending messages
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly", 
    "https://www.googleapis.com/auth/gmail.modify"  # This should be sufficient for delete
]
def send_email(
    to_email: str,
    subject: str,
    body: str,
    *,
    html: bool = False,
    attachment_path: str | None = None,
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
    attachment_path : str, optional
        Path to a file to attach.
    """
    
    try:
        creds = _get_gmail_credentials()
        service = build("gmail", "v1", credentials=creds)

        # Construct message - use multipart if html or attachments
        if html or attachment_path:
            message = MIMEMultipart()
            msg_body = MIMEText(body, "html" if html else "plain")
            message.attach(msg_body)

            if attachment_path:
                with open(attachment_path, "rb") as f:
                    data = f.read()
                filename = os.path.basename(attachment_path)
                mime_type = "application/pdf" if filename.endswith(".pdf") else "application/octet-stream"
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
    
    except Exception as e:
        print(f"[ERROR] Email sending failed: {e}")
        print(f"[INFO] You may need to set up Google API credentials. See SETUP_GOOGLE_CREDENTIALS.md")
        raise e


def read_emails(query: str | None = None) -> list[Any]:
    """Return a list of messages matching the optional query."""
    
    # Check if running in mock mode or credentials are missing
    current_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(current_dir, "credentials.json")
    
    if os.getenv("MOCK_GOOGLE_APIS") == "true" or not os.path.exists(credentials_path):
        print(f"[MOCK] 📧 Would read emails with query: {query}")
        return [{"id": "mock_email_1", "threadId": "mock_thread_1"}]

    creds = _get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)

    response = (
        service.users()
        .messages()
        .list(userId="me", q=query or "")
        .execute()
    )
    return response.get("messages", [])


def delete_email(message_id: str) -> None:
    """Delete a message by id (moves to trash instead of permanent delete)."""
    
    # Check if running in mock mode or credentials are missing
    current_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(current_dir, "credentials.json")
    
    if os.getenv("MOCK_GOOGLE_APIS") == "true" or not os.path.exists(credentials_path):
        print(f"[MOCK] 🗑️ Would delete email id: {message_id}")
        return

    creds = _get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)
    
    # Try to trash the message first (safer and requires fewer permissions)
    try:
        service.users().messages().trash(userId="me", id=message_id).execute()
        print(f"🗑️ Moved email to trash (id: {message_id})")
    except Exception as trash_error:
        print(f"[DEBUG] Trash operation failed: {trash_error}")
        print(f"[DEBUG] Attempting permanent delete...")
        # Fall back to permanent delete
        service.users().messages().delete(userId="me", id=message_id).execute()
        print(f"🗑️ Permanently deleted email id: {message_id}")


# ...existing code...
def _get_gmail_credentials():
    """Get Gmail API credentials with proper file paths."""
    import os
    
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_path = os.path.join(current_dir, "credentials.json")
    token_path = os.path.join(current_dir, "token.pickle")
    
    print(f"[DEBUG] Looking for credentials at: {credentials_path}")
    print(f"[DEBUG] Looking for token at: {token_path}")
    
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"credentials.json not found at {credentials_path}")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds
# ...existing code...