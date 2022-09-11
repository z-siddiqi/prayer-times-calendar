import os
import requests

from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CALENDAR = os.environ["CALENDAR"]
KEYFILE = os.path.join(os.environ["LAMBDA_TASK_ROOT"], "private-key.json")
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar",
]


def fetch_prayer_times(date):
    url = "https://www.masjidnow.com/api/v2/salah_timings/daily.json"
    params = {
        "masjid_id": os.environ["MASJID"],
        "day": date.day,
        "month": date.month,
        "year": date.year,
    }
    response = requests.get(url, params=params)
    prayer_times = response.json()["masjid"]["salah_timing"]
    return prayer_times


def lambda_handler(event, context):
    creds = Credentials.from_service_account_file(KEYFILE, scopes=SCOPES)

    service = build("calendar", "v3", credentials=creds)

    prayer_times = fetch_prayer_times(datetime.today())

    events = [
        f"fajr today at {prayer_times['fajr_adhan']}",
        f"dhuhr today at {prayer_times['dhuhr_adhan']}",
        f"asr today at {prayer_times['asr_adhan_extra']}",
        f"maghrib today at {prayer_times['maghrib_adhan']}",
        f"isha today at {prayer_times['isha_adhan']}",
    ]

    for event in events:
        try:
            event = service.events().quickAdd(calendarId=CALENDAR, text=event).execute()
            print(f"Event created: {event['htmlLink']}")
        except HttpError as error:
            print(f"An error occurred: {error}")
