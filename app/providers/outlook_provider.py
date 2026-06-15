from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from app.providers.base import CalendarEvent, CalendarProvider, EmailMessage, EmailProvider

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


class GraphApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _graph_error_message(response: httpx.Response) -> str:
    if response.status_code in (401, 403):
        return (
            "Microsoft Graph could not access mailbox or calendar. "
            "Your signed-in account may not have an Exchange Online mailbox or license. "
            "For personal Hotmail/Outlook, set AZURE_TENANT_ID=common in .env and sign in again."
        )

    try:
        body = response.json()
        error = body.get("error", {})
        code = error.get("code")
        message = error.get("message")
        if code or message:
            return f"Microsoft Graph error ({response.status_code}): {code or 'unknown'} — {message or 'request failed'}"
    except ValueError:
        pass

    return f"Microsoft Graph request failed with status {response.status_code}."


class OutlookProvider(CalendarProvider, EmailProvider):
    def __init__(self, access_token: str, client: Optional[httpx.AsyncClient] = None) -> None:
        self._access_token = access_token
        self._client = client

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": "Bearer " + self._access_token}

        if self._client is not None:
            response = await self._client.get(f"{GRAPH_BASE_URL}{path}", headers=headers, params=params)
            if response.is_error:
                raise GraphApiError(response.status_code, _graph_error_message(response))
            return response.json()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GRAPH_BASE_URL}{path}", headers=headers, params=params)
            if response.is_error:
                raise GraphApiError(response.status_code, _graph_error_message(response))
            return response.json()

    async def read_calendar(self) -> List[CalendarEvent]:
        payload = await self._get("/me/events", params={"$top": 10})
        events: List[CalendarEvent] = []

        for item in payload.get("value", []):
            start_raw = (item.get("start") or {}).get("dateTime")
            end_raw = (item.get("end") or {}).get("dateTime")
            if not start_raw or not end_raw:
                continue
            events.append(
                CalendarEvent(
                    id=item.get("id", ""),
                    subject=item.get("subject", ""),
                    start=datetime.fromisoformat(start_raw.replace("Z", "+00:00")),
                    end=datetime.fromisoformat(end_raw.replace("Z", "+00:00")),
                )
            )

        return events

    async def read_recent_emails(self) -> List[EmailMessage]:
        payload = await self._get("/me/mailFolders/inbox/messages", params={"$top": 10})
        messages: List[EmailMessage] = []

        for item in payload.get("value", []):
            received_raw = item.get("receivedDateTime") or "1970-01-01T00:00:00Z"
            messages.append(
                EmailMessage(
                    id=item.get("id", ""),
                    subject=item.get("subject", ""),
                    sender=item.get("from", {}).get("emailAddress", {}).get("address", ""),
                    received_at=datetime.fromisoformat(received_raw.replace("Z", "+00:00")),
                )
            )

        return messages
