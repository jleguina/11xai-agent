import datetime
import os
import pickle
from typing import Any

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings
from app.integrations.google_auth import GoogleService, get_google_service


def gcal_authenticate(
    client_config: dict[str, dict[str, str | list[str]]],
    scopes: list[str],
) -> Any:
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, scopes)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build("calendar", "v3", credentials=creds)


def test_gcal(service: Any) -> None:
    try:
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' = UTC time
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    except HttpError as error:
        print("An error occurred: %s" % error)


def schedule_event(
    service: Any,
    summary: str,
    start_time: str,
    end_time: str,
    attendees: list[str] = [],
    timezone: str = "UTC",
) -> str:
    event = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_time,
            "timeZone": timezone,
        },
        "attendees": [{"email": attendee} for attendee in attendees],
        "conferenceData": {
            "createRequest": {
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
                "requestId": "randomString",
            }
        },
    }

    event = (
        service.events()
        .insert(calendarId="primary", body=event, conferenceDataVersion=1)
        .execute()
    )

    return event["id"]


def delete_event(service: Any, event_id: str) -> None:
    service.events().delete(calendarId="primary", eventId=event_id).execute()


if __name__ == "__main__":
    # Authenticate with Google Calendar API
    service = get_google_service(
        service_name=GoogleService.GCAL,
        client_config=settings.GOOGLE_CLIENT_CONFIG,
        scopes=settings.GOOGLE_SCOPES,
    )
    # Schedule an event for tomorrow at 2:30 PM
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=30, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(hours=1)
    summary = "Dummy meeting"

    event_id = schedule_event(
        service,
        summary,
        start_time.isoformat(),
        end_time.isoformat(),
        attendees=["javierleguina98@gmail.com", "aalixmeunier@gmail.com"],
    )

    delete_event(service, event_id)
