import pytest

from app.mcp.bridge import invoke_read_calendar, invoke_read_email, invoke_read_recent_emails
from app.mcp.schemas import READ_ONLY_TOOL_NAMES
from app.mcp.server import mcp_read_calendar, mcp_read_email, mcp_read_recent_emails
from app.tools.contracts import ToolError, ToolResult, tool_failure, tool_success


@pytest.mark.asyncio
async def test_mcp_read_calendar_delegates_to_app_tools(monkeypatch):
    expected = tool_success("read_calendar", "mock", [{"id": "evt-1"}])

    async def fake_read_calendar():
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_calendar", fake_read_calendar)

    result = await invoke_read_calendar()

    assert result == expected.to_dict()
    assert result["ok"] is True
    assert result["tool"] == "read_calendar"


@pytest.mark.asyncio
async def test_mcp_read_recent_emails_delegates_to_app_tools(monkeypatch):
    expected = tool_success("read_recent_emails", "mock", [{"id": "msg-1"}])

    async def fake_read_recent_emails():
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_recent_emails", fake_read_recent_emails)

    result = await invoke_read_recent_emails()

    assert result == expected.to_dict()
    assert result["data"][0]["id"] == "msg-1"


@pytest.mark.asyncio
async def test_mcp_read_email_delegates_to_app_tools(monkeypatch):
    expected = tool_success(
        "read_email",
        "mock",
        {"id": "msg-1", "body": {"content_type": "text", "content": "hello"}},
    )

    async def fake_read_email(message_id: str):
        assert message_id == "msg-1"
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_email", fake_read_email)

    result = await invoke_read_email("msg-1")

    assert result == expected.to_dict()


@pytest.mark.asyncio
async def test_mcp_preserves_auth_required(monkeypatch):
    failure = tool_failure(
        "read_calendar",
        "outlook",
        ToolError("auth_required", "Please re-authenticate via /auth/microsoft/login", False),
    )

    async def fake_read_calendar():
        return failure

    monkeypatch.setattr("app.mcp.bridge.tools_read_calendar", fake_read_calendar)

    result = await mcp_read_calendar()

    assert result["ok"] is False
    assert result["error"]["code"] == "auth_required"


@pytest.mark.asyncio
async def test_mcp_provider_error_without_token_leakage(monkeypatch):
    failure = tool_failure(
        "read_email",
        "outlook",
        ToolError("not_found", "Email message not found.", False),
    )

    async def fake_read_email(message_id: str):
        return failure

    monkeypatch.setattr("app.mcp.bridge.tools_read_email", fake_read_email)

    result = await mcp_read_email("missing")

    payload = str(result)
    assert "access_token" not in payload
    assert "refresh_token" not in payload
    assert result["error"]["code"] == "not_found"


def test_only_read_only_tools_exposed():
    assert set(READ_ONLY_TOOL_NAMES) == {
        "read_calendar",
        "read_recent_emails",
        "read_email",
    }
    assert "send_email" not in READ_ONLY_TOOL_NAMES
    assert "create_calendar_event" not in READ_ONLY_TOOL_NAMES


@pytest.mark.asyncio
async def test_registered_mcp_handlers_match_read_only_tools():
    handlers = {
        "read_calendar": mcp_read_calendar,
        "read_recent_emails": mcp_read_recent_emails,
        "read_email": mcp_read_email,
    }
    assert set(handlers) == set(READ_ONLY_TOOL_NAMES)
