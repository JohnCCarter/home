from dataclasses import asdict
from typing import Any, List

from fastapi import FastAPI

from app.auth.microsoft import router as microsoft_auth_router
from app.auth.token_store import load_tokens
from app.providers.base import CalendarEvent, EmailMessage
from app.providers.mock_provider import MockProvider
from app.providers.outlook_provider import OutlookProvider

app = FastAPI(title="genesis-core-home-agent")
app.include_router(microsoft_auth_router)


async def _get_provider():
    tokens = load_tokens()
    access_token = tokens.get("access_token") if tokens else None
    if access_token:
        return OutlookProvider(access_token=access_token)
    return MockProvider()


def _serialize(items: List[Any]) -> List[dict]:
    return [asdict(item) for item in items]


@app.get("/calendar")
async def get_calendar() -> List[dict]:
    provider = await _get_provider()
    events: List[CalendarEvent] = await provider.read_calendar()
    return _serialize(events)


@app.get("/mail")
async def get_mail() -> List[dict]:
    provider = await _get_provider()
    emails: List[EmailMessage] = await provider.read_recent_emails()
    return _serialize(emails)
