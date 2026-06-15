import pytest
import httpx

from app.providers.base import DISABLED_WRITE_MESSAGE
from app.providers.outlook_provider import OutlookProvider


@pytest.mark.asyncio
async def test_read_calendar():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/me/events"
        return httpx.Response(
            status_code=200,
            json={
                "value": [
                    {
                        "id": "evt-1",
                        "subject": "Team Meeting",
                        "start": {"dateTime": "2026-06-15T09:00:00Z"},
                        "end": {"dateTime": "2026-06-15T09:30:00Z"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OutlookProvider(access_token="token", client=client)
        events = await provider.read_calendar()

    assert len(events) == 1
    assert events[0].id == "evt-1"
    assert events[0].subject == "Team Meeting"


@pytest.mark.asyncio
async def test_read_calendar_skips_items_missing_start_or_end():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "value": [
                    {"id": "bad-1", "subject": "No start", "end": {"dateTime": "2026-06-15T09:30:00Z"}},
                    {"id": "bad-2", "subject": "Null start", "start": None, "end": {"dateTime": "2026-06-15T09:30:00Z"}},
                    {
                        "id": "good",
                        "subject": "Good",
                        "start": {"dateTime": "2026-06-15T09:00:00Z"},
                        "end": {"dateTime": "2026-06-15T09:30:00Z"},
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OutlookProvider(access_token="token", client=client)
        events = await provider.read_calendar()

    assert len(events) == 1
    assert events[0].id == "good"


@pytest.mark.asyncio
async def test_read_recent_emails():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1.0/me/mailFolders/inbox/messages"
        return httpx.Response(
            status_code=200,
            json={
                "value": [
                    {
                        "id": "msg-1",
                        "subject": "Status update",
                        "from": {"emailAddress": {"address": "sender@example.com"}},
                        "receivedDateTime": "2026-06-15T08:00:00Z",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OutlookProvider(access_token="token", client=client)
        messages = await provider.read_recent_emails()

    assert len(messages) == 1
    assert messages[0].id == "msg-1"
    assert messages[0].subject == "Status update"


@pytest.mark.asyncio
async def test_read_recent_emails_null_received_datetime():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "value": [
                    {
                        "id": "msg-2",
                        "subject": "No date",
                        "from": {"emailAddress": {"address": "x@example.com"}},
                        "receivedDateTime": None,
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OutlookProvider(access_token="token", client=client)
        messages = await provider.read_recent_emails()

    assert len(messages) == 1
    assert messages[0].id == "msg-2"
    # Should fall back to epoch without raising
    from datetime import datetime, timezone
    assert messages[0].received_at == datetime(1970, 1, 1, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_write_actions_disabled():
    provider = OutlookProvider(access_token="token")

    with pytest.raises(NotImplementedError, match=DISABLED_WRITE_MESSAGE):
        await provider.send_email()

    with pytest.raises(NotImplementedError, match=DISABLED_WRITE_MESSAGE):
        await provider.mark_as_read()

    with pytest.raises(NotImplementedError, match=DISABLED_WRITE_MESSAGE):
        await provider.create_event()
