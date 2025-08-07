from datetime import datetime, timedelta
from google_utils.calendar_tools import create_event

start = datetime.now() + timedelta(minutes=10)
end = start + timedelta(hours=1)

create_event("API Test Event", start, end, description="Testing Google Calendar API")
