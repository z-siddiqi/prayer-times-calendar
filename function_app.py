import os
import logging
import requests

import azure.functions as func

from typing import Dict, Any
from datetime import datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CALENDAR = os.environ["CALENDAR"]

app = func.FunctionApp()


def fetch_prayer_times(filter: str = "today") -> Dict[str, Any]:
    url = f"https://centralmosque.co.uk/?rest_route=/dpt/v1/prayertime&filter={filter}"
    response = requests.get(url)
    return response.json()[0]


@app.schedule(schedule="0 0 * * * *", arg_name="timer", run_on_startup=True, use_monitor=False)
def prayer_times_calendar(timer: func.TimerRequest) -> None:
    prayer_times = fetch_prayer_times()

    creds = Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": os.environ["PROJECT_ID"],
            "private_key_id": os.environ["PRIVATE_KEY_ID"],
            "private_key": os.environ["PRIVATE_KEY"],
            "client_email": os.environ["CLIENT_EMAIL"],
            "client_id": os.environ["CLIENT_ID"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ["CLIENT_X509_CERT_URL"],
            "universe_domain": "googleapis.com",
        },
        scopes=[
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar",
        ],
    )

    service = build("calendar", "v3", credentials=creds)

    events = [
        ("fajr", prayer_times['fajr_begins']),
        ("dhuhr", prayer_times['zuhr_begins']),
        ("asr", prayer_times['asr_mithl_2']),
        ("maghrib", prayer_times['maghrib_begins']),
        ("isha", prayer_times['isha_begins']),
    ]

    for prayer, time in events:
        try:
            start_time = datetime.strptime(f"{prayer_times['d_date']} {time}", "%Y-%m-%d %H:%M:%S")
            end_time = start_time + timedelta(minutes=15)

            event = {
                'summary': prayer,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Europe/London',
                },
            }

            created_event = service.events().insert(calendarId=CALENDAR, body=event).execute()
            logging.info(f"Event created: {created_event['htmlLink']}")
        except ValueError as e:
            logging.error(f"Error parsing prayer data for {prayer}: {e}")
        except HttpError as error:
            logging.error(f"An error occurred: {error}")
