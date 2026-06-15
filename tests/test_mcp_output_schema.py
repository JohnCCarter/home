"""Tests for MCP tool output schemas / structuredContent.

All fixtures are synthetic — no real mailbox, calendar, or body content.
"""

import pytest

from app.mcp.schemas import READ_ONLY_TOOL_NAMES
from app.mcp.server import mcp
from app.tools.contracts import ToolError, tool_failure, tool_success


async def _output_schema_for(name: str) -> dict | None:
    tools = await mcp.list_tools()
    for tool in tools:
        if tool.name == name:
            return tool.outputSchema
    raise AssertionError(f"tool {name!r} not found")


def _defs(schema: dict) -> dict:
    return schema.get("$defs", {})


# --- outputSchema present (non-null) ---------------------------------------


@pytest.mark.asyncio
async def test_read_calendar_has_output_schema():
    assert await _output_schema_for("read_calendar") is not None


@pytest.mark.asyncio
async def test_read_recent_emails_has_output_schema():
    assert await _output_schema_for("read_recent_emails") is not None


@pytest.mark.asyncio
async def test_read_email_has_output_schema():
    assert await _output_schema_for("read_email") is not None


# --- envelope top-level props ----------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["read_calendar", "read_recent_emails", "read_email"])
async def test_output_schema_has_envelope_props(name):
    schema = await _output_schema_for(name)
    props = set(schema.get("properties", {}).keys())
    assert {"ok", "tool", "provider", "data", "error"} <= props


# --- nested data shapes -----------------------------------------------------


@pytest.mark.asyncio
async def test_calendar_schema_has_event_fields():
    schema = await _output_schema_for("read_calendar")
    event = _defs(schema).get("CalendarEventModel", {})
    assert {"id", "subject", "start", "end"} <= set(event.get("properties", {}).keys())


@pytest.mark.asyncio
async def test_email_summary_schema_has_fields():
    schema = await _output_schema_for("read_recent_emails")
    summary = _defs(schema).get("EmailSummaryModel", {})
    assert {"id", "subject", "sender", "received_at"} <= set(summary.get("properties", {}).keys())


@pytest.mark.asyncio
async def test_email_detail_schema_has_body_fields():
    schema = await _output_schema_for("read_email")
    detail = _defs(schema).get("EmailDetailModel", {})
    detail_props = set(detail.get("properties", {}).keys())
    assert {"body", "body_preview"} <= detail_props
    assert "EmailBodyModel" in _defs(schema)


# --- call_tool success -> structuredContent matches synthetic dict ----------


@pytest.mark.asyncio
async def test_read_calendar_structured_content(monkeypatch):
    events = [
        {
            "id": "evt-1",
            "subject": "Synthetic standup",
            "start": "2026-06-16T09:00:00+00:00",
            "end": "2026-06-16T09:30:00+00:00",
        }
    ]
    expected = tool_success("read_calendar", "mock", events)

    async def fake():
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_calendar", fake)

    _content, structured = await mcp.call_tool("read_calendar", {})
    assert structured == expected.to_dict()


@pytest.mark.asyncio
async def test_read_recent_emails_structured_content(monkeypatch):
    messages = [
        {
            "id": "msg-1",
            "subject": "Synthetic subject",
            "sender": "noreply@example.com",
            "received_at": "2026-06-15T20:00:00+00:00",
        }
    ]
    expected = tool_success("read_recent_emails", "mock", messages)

    async def fake():
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_recent_emails", fake)

    _content, structured = await mcp.call_tool("read_recent_emails", {})
    assert structured == expected.to_dict()


@pytest.mark.asyncio
async def test_read_email_structured_content(monkeypatch):
    detail = {
        "id": "msg-1",
        "subject": "Synthetic subject",
        "sender": "noreply@example.com",
        "received_at": "2026-06-15T20:00:00+00:00",
        "body_preview": "synthetic preview",
        "body": {"content_type": "text", "content": "synthetic body"},
    }
    expected = tool_success("read_email", "mock", detail)

    async def fake(message_id: str):
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_email", fake)

    _content, structured = await mcp.call_tool("read_email", {"message_id": "msg-1"})
    assert structured == expected.to_dict()


# --- error case preserved ---------------------------------------------------


@pytest.mark.asyncio
async def test_auth_required_structured_content(monkeypatch):
    failure = tool_failure(
        "read_recent_emails",
        "outlook",
        ToolError("auth_required", "Please re-authenticate via /auth/microsoft/login", False),
    )

    async def fake():
        return failure

    monkeypatch.setattr("app.mcp.bridge.tools_read_recent_emails", fake)

    _content, structured = await mcp.call_tool("read_recent_emails", {})
    assert structured["ok"] is False
    assert structured["data"] is None
    assert structured["error"]["code"] == "auth_required"


# --- only read-only tools exposed ------------------------------------------


@pytest.mark.asyncio
async def test_only_read_only_tools_exposed():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert names == set(READ_ONLY_TOOL_NAMES)
    assert "send_email" not in names
    assert "delete_email" not in names
