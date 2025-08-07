import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

def get_credentials(scopes):
    """Get Google API credentials for the given scopes."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), "token.pickle")
    creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
    if os.path.exists(token_path):
        import pickle
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as token:
            import pickle
            pickle.dump(creds, token)
    return creds