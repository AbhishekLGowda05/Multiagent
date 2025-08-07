# Google API Credentials Setup

To enable email and calendar functionality, you need to set up Google API credentials:

## Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API and Google Calendar API

## Step 2: Create Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Download the JSON file as `credentials.json`
5. Place it in the project root directory: `/Applications/Projects/Int-Assignment/credentials.json`

## Step 3: Required Scopes
The system needs these scopes:
- `https://www.googleapis.com/auth/gmail.send` (send emails)
- `https://www.googleapis.com/auth/gmail.readonly` (read emails)
- `https://www.googleapis.com/auth/gmail.modify` (delete emails)
- `https://www.googleapis.com/auth/calendar` (calendar events)

## Step 4: First Run
On first use, the system will open a browser for authentication and create a `token.pickle` file for future use.

## Alternative: Mock Mode
If you want to test without Google API, the system can run in mock mode by setting environment variable:
```bash
export MOCK_GOOGLE_APIS=true
```
