from datetime import datetime, timezone

import pytest

from app.providers.base import CalendarEvent, EmailBody, EmailDetail, EmailMessage
from app.providers.mock_provider import MockProvider
from app.providers.outlook_provider import GraphApiError
from app.tools.calendar_tools import read_calendar
from app.tools.contracts import ToolError, map_graph_error, tool_failure, tool_success
from app.tools.deps import AuthRequiredError
from app.tools.email_tools import read_email, read_recent_emails


@pytest.mark.asyncio
async def test_read_calendar_returns_standard_tool_result(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    monkeypatch.setattr("app.tools.calendar_tools.get_provider_with_name", fake_get_provider)

    result = await read_calendar()

    assert result.ok is True
    assert result.tool == "read_calendar"
    assert result.provider == "mock"
    assert result.error is None
    assert isinstance(result.data, list)
    assert result.data[0]["id"] == "mock-event-1"
    payload = result.to_dict()
    assert payload["ok"] is True
    assert "access_token" not in str(payload)


@pytest.mark.asyncio
async def test_read_recent_emails_returns_standard_tool_result(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    monkeypatch.setattr("app.tools.email_tools.get_provider_with_name", fake_get_provider)

    result = await read_recent_emails()

    assert result.ok is True
    assert result.tool == "read_recent_emails"
    assert result.provider == "mock"
    assert result.data[0]["id"] == "mock-email-1"


@pytest.mark.asyncio
async def test_read_email_returns_standard_tool_result(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    monkeypatch.setattr("app.tools.email_tools.get_provider_with_name", fake_get_provider)

    result = await read_email("mock-email-1")

    assert result.ok is True
    assert result.tool == "read_email"
    assert result.data["body"]["content"] == "Mock email body content"


@pytest.mark.asyncio
async def test_provider_401_maps_to_auth_required(monkeypatch):
    async def fake_get_provider():
        raise AuthRequiredError()

    monkeypatch.setattr("app.tools.calendar_tools.get_provider_with_name", fake_get_provider)

    result = await read_calendar()

    assert result.ok is False
    assert result.error.code == "auth_required"
    assert "re-authenticate" in result.error.message


@pytest.mark.asyncio
async def test_provider_403_maps_to_permission_denied(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    async def fake_read_calendar(self):
        raise GraphApiError(403, "Insufficient permission")

    monkeypatch.setattr("app.tools.calendar_tools.get_provider_with_name", fake_get_provider)
    monkeypatch.setattr(MockProvider, "read_calendar", fake_read_calendar)

    result = await read_calendar()

    assert result.ok is False
    assert result.error.code == "permission_denied"


@pytest.mark.asyncio
async def test_provider_400_on_read_email_maps_to_not_found(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    async def fake_read_email(self, message_id: str):
        raise GraphApiError(400, "Email message not found.")

    monkeypatch.setattr("app.tools.email_tools.get_provider_with_name", fake_get_provider)
    monkeypatch.setattr(MockProvider, "read_email", fake_read_email)

    result = await read_email("nonexistent-id")

    assert result.ok is False
    assert result.error.code == "not_found"


@pytest.mark.asyncio
async def test_provider_404_maps_to_not_found(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    monkeypatch.setattr("app.tools.email_tools.get_provider_with_name", fake_get_provider)

    result = await read_email("missing-id")

    assert result.ok is False
    assert result.error.code == "not_found"


@pytest.mark.asyncio
async def test_provider_429_maps_to_rate_limited(monkeypatch):
    provider = MockProvider()

    async def fake_get_provider():
        return provider, "mock"

    async def fake_read_recent_emails(self):
        raise GraphApiError(429, "Rate limit exceeded")

    monkeypatch.setattr("app.tools.email_tools.get_provider_with_name", fake_get_provider)
    monkeypatch.setattr(MockProvider, "read_recent_emails", fake_read_recent_emails)

    result = await read_recent_emails()

    assert result.ok is False
    assert result.error.code == "rate_limited"
    assert result.error.retryable is True


def test_tool_result_does_not_leak_tokens_or_secrets():
    error = map_graph_error(GraphApiError(401, "Please sign in again"))
    result = tool_failure("read_email", "outlook", error)
    payload = result.to_dict()

    assert "access_token" not in str(payload)
    assert "refresh_token" not in str(payload)
    assert "client_secret" not in str(payload)


def test_map_graph_error_provider_error_for_5xx():
    error = map_graph_error(GraphApiError(503, "Service unavailable"))
    assert error.code == "provider_error"
    assert error.retryable is True


def test_read_email_validation_error_for_empty_message_id():
    import asyncio

    result = asyncio.run(read_email("   "))
    assert result.ok is False
    assert result.error.code == "validation_error"


def test_tool_success_shape():
    event = CalendarEvent(
        id="evt-1",
        subject="Team sync",
        start=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
        end=datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc),
    )
    result = tool_success("read_calendar", "mock", [{"id": event.id}])
    assert result.to_dict() == {
        "ok": True,
        "tool": "read_calendar",
        "provider": "mock",
        "data": [{"id": "evt-1"}],
        "error": None,
    }
