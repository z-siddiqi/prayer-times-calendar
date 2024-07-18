import os
import requests

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CALENDAR = os.environ["CALENDAR"]
KEYFILE = os.path.join(os.environ["LAMBDA_TASK_ROOT"], "private-key.json")
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar",
]


def fetch_prayer_times():
    url = "https://centralmosque.co.uk/?rest_route=/dpt/v1/prayertime&filter=today"
    response = requests.get(url)
    prayer_times = response.json()[0]
    return prayer_times


def lambda_handler(event, context):
    creds = Credentials.from_service_account_file(KEYFILE, scopes=SCOPES)

    service = build("calendar", "v3", credentials=creds)

    prayer_times = fetch_prayer_times()

    events = [
        f"fajr on {prayer_times['d_date']} at {prayer_times['fajr_begins']}",
        f"dhuhr on {prayer_times['d_date']} at {prayer_times['zuhr_begins']}",
        f"asr on {prayer_times['d_date']} at {prayer_times['asr_mithl_2']}",
        f"maghrib on {prayer_times['d_date']} at {prayer_times['maghrib_begins']}",
        f"isha on {prayer_times['d_date']} at {prayer_times['isha_begins']}",
    ]

    for event in events:
        try:
            event = service.events().quickAdd(calendarId=CALENDAR, text=event).execute()
            print(f"Event created: {event['htmlLink']}")
        except HttpError as error:
            print(f"An error occurred: {error}")
