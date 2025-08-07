from __future__ import print_function
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Gmail & Calendar scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar'
]

def authenticate_google():
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), 'token.pickle')

    # ✅ Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # ✅ Run OAuth if no valid credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
            print(f"🔍 Using credentials file at: {CREDENTIALS_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8080)  # ✅ For web client use

        # ✅ Save token for reuse
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    print("✅ Google authentication complete.")
    return creds

if __name__ == "__main__":
    authenticate_google()
