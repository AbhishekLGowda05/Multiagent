from __future__ import annotations

import os
import pickle
from hashlib import sha1
from typing import Sequence

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


DEFAULT_CREDENTIALS_FILE = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")


def _token_path(scopes: Sequence[str], token_dir: str = ".") -> str:
    """Return a token filename based on the requested scopes."""
    scopes_key = sha1(" ".join(sorted(scopes)).encode()).hexdigest()
    return os.path.join(token_dir, f"token_{scopes_key}.pickle")


def get_credentials(
    scopes: Sequence[str],
    credentials_file: str = DEFAULT_CREDENTIALS_FILE,
    token_dir: str = ".",
) -> Credentials:
    """Return OAuth2 credentials, caching tokens for reuse."""
    creds: Credentials | None = None
    token_file = _token_path(scopes, token_dir)

    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)
    return creds
