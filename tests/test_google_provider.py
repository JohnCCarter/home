"""GoogleProvider.read_calendar — offline via httpx.MockTransport.

Calendar-only (read-only). Verifies Google field mapping (items/summary/
dateTime|date), all-day handling, skip-on-missing, error mapping, and that
write methods stay disabled. No deps.py / token_store wiring — proven in isolation.
"""

from datetime import datetime, timezone

import httpx
import pytest

from app.providers.base import DISABLED_WRITE_MESSAGE
from app.providers.google_provider import GoogleApiError, GoogleProvider


@pytest.mark.asyncio
async def test_read_calendar_timed_event():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/calendar/v3/calendars/primary/events"
        return httpx.Response(
            status_code=200,
            json={
                "items": [
                    {
                        "id": "evt-1",
                        "summary": "Team Meeting",
                        "start": {"dateTime": "2026-06-15T09:00:00Z"},
                        "end": {"dateTime": "2026-06-15T09:30:00Z"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GoogleProvider(access_token="token", client=client)
        events = await provider.read_calendar()

    assert len(events) == 1
    assert events[0].id == "evt-1"
    assert events[0].subject == "Team Meeting"
    assert events[0].start == datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_read_calendar_all_day_event():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "items": [
                    {
                        "id": "evt-allday",
                        "summary": "Holiday",
                        "start": {"date": "2026-06-15"},
                        "end": {"date": "2026-06-16"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GoogleProvider(access_token="token", client=client)
        events = await provider.read_calendar()

    assert len(events) == 1
    assert events[0].id == "evt-allday"
    assert events[0].start == datetime(2026, 6, 15, 0, 0)
    assert events[0].end == datetime(2026, 6, 16, 0, 0)


@pytest.mark.asyncio
async def test_read_calendar_skips_items_missing_start_or_end():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "items": [
                    {"id": "bad-1", "summary": "No start", "end": {"date": "2026-06-16"}},
                    {"id": "bad-2", "summary": "Empty start", "start": {}, "end": {"date": "2026-06-16"}},
                    {
                        "id": "good",
                        "summary": "Good",
                        "start": {"dateTime": "2026-06-15T09:00:00Z"},
                        "end": {"dateTime": "2026-06-15T09:30:00Z"},
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GoogleProvider(access_token="token", client=client)
        events = await provider.read_calendar()

    assert len(events) == 1
    assert events[0].id == "good"


@pytest.mark.asyncio
async def test_read_calendar_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=401, json={"error": {"message": "Invalid Credentials"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = GoogleProvider(access_token="token", client=client)
        with pytest.raises(GoogleApiError) as exc:
            await provider.read_calendar()

    assert exc.value.status_code == 401
    assert "sign in again" in exc.value.message


@pytest.mark.asyncio
async def test_write_actions_disabled():
    provider = GoogleProvider(access_token="token")

    with pytest.raises(NotImplementedError, match=DISABLED_WRITE_MESSAGE):
        await provider.create_event()
