from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.providers.base import (
    CalendarEvent,
    CalendarProvider,
    ProviderApiError,
)

# Calendar-only: matches the read-only scope calendar.events.readonly. Gmail is a
# separate later slice, so this provider implements CalendarProvider only — write
# methods inherit NotImplementedError from the base.
GOOGLE_CALENDAR_BASE_URL = "https://www.googleapis.com/calendar/v3"


class GoogleApiError(ProviderApiError):
    """Google API error — a provider-specific ProviderApiError."""


def _google_error_message(response: httpx.Response) -> str:
    status = response.status_code

    if status == 401:
        return "Google authentication failed. Please sign in again at /auth/google/login."

    if status == 403:
        return "Insufficient permission to access this Google Calendar resource."

    if status == 404:
        return "Google Calendar resource not found."

    if status == 429:
        return "Google API rate limit exceeded. Try again later."

    if status >= 500:
        return "Google API service error. Try again later."

    try:
        error = (response.json() or {}).get("error", {})
        message = error.get("message")
        if message:
            return f"Google API error ({status}): {message}"
    except ValueError:
        pass

    return f"Google API request failed with status {status}."


def _parse_event_datetime(slot: Optional[Dict[str, Any]]) -> Optional[datetime]:
    """Google start/end is either a timed `dateTime` (RFC3339) or an all-day `date`
    (YYYY-MM-DD). Try dateTime first; the date-only path needs no Z handling."""
    if not slot:
        return None

    timed = slot.get("dateTime")
    if timed:
        return datetime.fromisoformat(timed.replace("Z", "+00:00"))

    all_day = slot.get("date")
    if all_day:
        return datetime.fromisoformat(all_day)

    return None


class GoogleProvider(CalendarProvider):
    def __init__(self, access_token: str, client: Optional[httpx.AsyncClient] = None) -> None:
        self._access_token = access_token
        self._client = client

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": "Bearer " + self._access_token}

        if self._client is not None:
            response = await self._client.get(
                f"{GOOGLE_CALENDAR_BASE_URL}{path}", headers=headers, params=params
            )
            if response.is_error:
                raise GoogleApiError(response.status_code, _google_error_message(response))
            return response.json()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{GOOGLE_CALENDAR_BASE_URL}{path}", headers=headers, params=params
            )
            if response.is_error:
                raise GoogleApiError(response.status_code, _google_error_message(response))
            return response.json()

    async def read_calendar(self) -> List[CalendarEvent]:
        # No singleEvents=true: this returns recurring-event masters, not expanded
        # instances. Outlook's /me/events has the same accepted limitation, so this
        # is a conscious parity choice — instance expansion is a later refinement.
        payload = await self._get("/calendars/primary/events", params={"maxResults": 10})
        events: List[CalendarEvent] = []

        for item in payload.get("items", []):
            start = _parse_event_datetime(item.get("start"))
            end = _parse_event_datetime(item.get("end"))
            if start is None or end is None:
                continue
            events.append(
                CalendarEvent(
                    id=item.get("id", ""),
                    subject=item.get("summary", ""),
                    start=start,
                    end=end,
                )
            )

        return events
