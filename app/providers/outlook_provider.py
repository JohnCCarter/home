from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from app.providers.base import (
    CalendarEvent,
    CalendarProvider,
    EmailBody,
    EmailDetail,
    EmailMessage,
    EmailProvider,
)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
MESSAGE_SELECT = "id,subject,from,receivedDateTime,bodyPreview,body"


class GraphApiError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _graph_error_message(response: httpx.Response, *, resource: str = "resource") -> str:
    status = response.status_code

    if status == 401:
        if resource in {"mailbox", "calendar", "resource"}:
            return (
                "Microsoft Graph could not access mailbox or calendar. "
                "Your signed-in account may not have an Exchange Online mailbox or license. "
                "For personal Hotmail/Outlook, set AZURE_TENANT_ID=common in .env and sign in again."
            )
        return "Microsoft Graph authentication failed. Please sign in again."

    if status == 403:
        return "Insufficient permission to access this Microsoft Graph resource."

    if status == 404 and resource == "message":
        return "Email message not found."

    if status == 404:
        return "Microsoft Graph resource not found."

    if status == 429:
        return "Microsoft Graph rate limit exceeded. Try again later."

    if status >= 500:
        return "Microsoft Graph service error. Try again later."

    try:
        body = response.json()
        error = body.get("error", {})
        code = error.get("code")
        message = error.get("message")
        if code or message:
            return f"Microsoft Graph error ({status}): {code or 'unknown'} — {message or 'request failed'}"
    except ValueError:
        pass

    return f"Microsoft Graph request failed with status {status}."


class OutlookProvider(CalendarProvider, EmailProvider):
    def __init__(self, access_token: str, client: Optional[httpx.AsyncClient] = None) -> None:
        self._access_token = access_token
        self._client = client

    async def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        resource: str = "resource",
    ) -> Dict[str, Any]:
        headers = {"Authorization": "Bearer " + self._access_token}

        if self._client is not None:
            response = await self._client.get(f"{GRAPH_BASE_URL}{path}", headers=headers, params=params)
            if response.is_error:
                raise GraphApiError(response.status_code, _graph_error_message(response, resource=resource))
            return response.json()

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{GRAPH_BASE_URL}{path}", headers=headers, params=params)
            if response.is_error:
                raise GraphApiError(response.status_code, _graph_error_message(response, resource=resource))
            return response.json()

    async def read_calendar(self) -> List[CalendarEvent]:
        payload = await self._get("/me/events", params={"$top": 10}, resource="calendar")
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
        payload = await self._get(
            "/me/mailFolders/inbox/messages",
            params={"$top": 10},
            resource="mailbox",
        )
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

    async def read_email(self, message_id: str) -> EmailDetail:
        encoded_id = quote(message_id, safe="")
        payload = await self._get(
            f"/me/messages/{encoded_id}",
            params={"$select": MESSAGE_SELECT},
            resource="message",
        )

        received_raw = payload.get("receivedDateTime") or "1970-01-01T00:00:00Z"
        body = payload.get("body") or {}

        return EmailDetail(
            id=payload.get("id", ""),
            subject=payload.get("subject", ""),
            sender=payload.get("from", {}).get("emailAddress", {}).get("address", ""),
            received_at=datetime.fromisoformat(received_raw.replace("Z", "+00:00")),
            body_preview=payload.get("bodyPreview", ""),
            body=EmailBody(
                content_type=body.get("contentType", "text"),
                content=body.get("content", ""),
            ),
        )
