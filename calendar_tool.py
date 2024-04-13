import datetime
import os
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


load_dotenv()
calendar_id_global = os.getenv('CALENDAR_ID')


def authenticate():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "private/credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

    return creds


def create_event_today(name, cinema_nr, time):    
    today = datetime.date.today()
    start_time = str(today) + 'T' + time[0:2] + ':' + time[2:] + ":00"
    end_minutes = int(time[2:]) + 15

    if end_minutes == 60:
        end_hours = int(time[0:2]) + 1
        end_minutes = 0
    else:
       end_hours = int(time[0:2])
    end_time = str(today) + 'T' + str(end_hours) + ':' + str(end_minutes) + ":00"
    
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': name,
        'location': str(cinema_nr),
        'description': '',
        'start': {
            'dateTime': start_time,
            'timeZone': 'Europe/Vienna',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/Vienna',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 15},
            ],
        },
    }

    event = service.events().insert(calendarId=calendar_id_global, body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    


def clear_calendar():
    creds = authenticate()
    service = build('calendar', 'v3', credentials=creds)

    # Retrieve events from the calendar
    events_result = service.events().list(calendarId=calendar_id_global).execute()
    events = events_result.get('items', [])

    # Delete each event
    for event in events:
        service.events().delete(calendarId=calendar_id_global, eventId=event['id']).execute()
        print('Event deleted: %s' % (event.get('htmlLink')))



#create_event_today("test", 1, '1400')
#clear_calendar()