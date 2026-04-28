"""Thin wrapper around Google Calendar API."""

import json
import os
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _service():
    here = Path(__file__).parent
    token = here / "token.json"
    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_info(json.loads(token.read_text()), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cred_file = here / "credentials.json"
            if not cred_file.exists():
                raise FileNotFoundError(
                    f"Place your OAuth client JSON at {cred_file}. See README."
                )
            creds = InstalledAppFlow.from_client_secrets_file(
                str(cred_file), SCOPES
            ).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def list_calendars() -> List[dict]:
    items = _service().calendarList().list().execute().get("items", [])
    return [{"id": c["id"], "summary": c.get("summary")} for c in items]


def create_event(calendar_id: str, summary: str, start: str, end: str) -> str:
    body = {"summary": summary, "start": {"dateTime": start}, "end": {"dateTime": end}}
    event = _service().events().insert(calendarId=calendar_id, body=body).execute()
    return event["id"]
