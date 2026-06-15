import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from app.mcp.http_server import (
    configure_http_settings,
    create_streamable_http_app,
    mcp_http_endpoint,
    run_http_server,
)
from app.mcp.schemas import MCP_HTTP_DEFAULT_PORT, MCP_STREAMABLE_HTTP_PATH, READ_ONLY_TOOL_NAMES
from app.mcp.server import mcp, mcp_read_calendar, mcp_read_recent_emails
from app.tools.contracts import ToolError, tool_failure, tool_success


@pytest.fixture(autouse=True)
def _reset_streamable_session_manager():
    """Give each test a fresh streamable session manager.

    ``StreamableHTTPSessionManager.run()`` can only be called once per instance,
    and ``mcp`` is a module-level singleton, so two tests that mount the
    streamable app would otherwise collide. Reset the cached manager around
    every test.
    """
    mcp._session_manager = None
    yield
    mcp._session_manager = None


def test_http_mcp_app_initializes():
    configure_http_settings("127.0.0.1", 8001)
    app = create_streamable_http_app()
    assert app is not None


def test_http_mcp_route_registered():
    configure_http_settings("127.0.0.1", 8001)
    app = create_streamable_http_app()
    paths = {getattr(route, "path", None) for route in app.routes}
    assert MCP_STREAMABLE_HTTP_PATH in paths


def test_http_mcp_endpoint_url():
    assert mcp_http_endpoint("127.0.0.1", 8001) == "http://127.0.0.1:8001/mcp"


@pytest.mark.asyncio
async def test_http_mcp_exposes_same_read_only_tools():
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}
    assert tool_names == set(READ_ONLY_TOOL_NAMES)
    assert "send_email" not in tool_names
    assert "delete_email" not in tool_names


@pytest.mark.asyncio
async def test_http_mcp_call_tool_delegates_via_bridge(monkeypatch):
    expected = tool_success("read_calendar", "mock", [{"id": "evt-1"}])

    async def fake_read_calendar():
        return expected

    monkeypatch.setattr("app.mcp.bridge.tools_read_calendar", fake_read_calendar)

    result = await mcp_read_calendar()

    assert result == expected.to_dict()


@pytest.mark.asyncio
async def test_http_mcp_preserves_auth_required(monkeypatch):
    failure = tool_failure(
        "read_recent_emails",
        "outlook",
        ToolError("auth_required", "Please re-authenticate via /auth/microsoft/login", False),
    )

    async def fake_read_recent_emails():
        return failure

    monkeypatch.setattr("app.mcp.bridge.tools_read_recent_emails", fake_read_recent_emails)

    result = await mcp_read_recent_emails()

    assert result["ok"] is False
    assert result["error"]["code"] == "auth_required"


@pytest.mark.asyncio
async def test_http_mcp_no_token_leakage_in_tool_response(monkeypatch):
    from app.mcp.server import mcp_read_email

    failure = tool_failure(
        "read_email",
        "outlook",
        ToolError("provider_error", "Graph request failed.", True),
    )

    async def fake_read_email(message_id: str):
        return failure

    monkeypatch.setattr("app.mcp.bridge.tools_read_email", fake_read_email)

    result = await mcp_read_email("msg-1")
    payload = str(result)

    assert "access_token" not in payload
    assert "refresh_token" not in payload
    assert "client_secret" not in payload


def test_http_mcp_does_not_import_providers_directly():
    import app.mcp.http_server as http_server_module

    source = open(http_server_module.__file__, encoding="utf-8").read()
    assert "app.providers" not in source
    assert "OutlookProvider" not in source


def test_run_http_server_uses_streamable_http_transport(monkeypatch):
    captured: dict = {}

    def fake_uvicorn_run(app, **kwargs):
        captured["app"] = app
        captured["kwargs"] = kwargs

    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)
    run_http_server(host="127.0.0.1", port=8002)

    assert isinstance(captured["app"], Starlette)
    assert captured["kwargs"]["host"] == "127.0.0.1"
    assert captured["kwargs"]["port"] == 8002
    assert mcp.settings.host == "127.0.0.1"
    assert mcp.settings.port == 8002


def test_stdio_server_still_uses_stdio_transport(monkeypatch):
    captured: dict[str, str] = {}

    def fake_run(transport: str = "stdio", mount_path=None):
        captured["transport"] = transport

    monkeypatch.setattr("app.mcp.server.mcp.run", fake_run)

    from app.mcp.server import main

    main()

    assert captured["transport"] == "stdio"


def test_http_mcp_endpoint_accepts_post():
    configure_http_settings("127.0.0.1", MCP_HTTP_DEFAULT_PORT)
    app = create_streamable_http_app()
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    }
    with TestClient(app, base_url="http://127.0.0.1:8001") as client:
        response = client.post(MCP_STREAMABLE_HTTP_PATH, json=init_payload)
        assert response.status_code in {200, 202, 406}


def test_http_mcp_request_without_session_id_is_not_rejected():
    """Regression: the ChatGPT/OpenAI tunnel forwards tools/call without an
    ``mcp-session-id`` header. A *stateful* MCP server rejects those with HTTP 400
    ("Missing session ID"), which surfaced to ChatGPT as a 502 upstream error.
    ``stateless_http=True`` on the FastMCP server must keep session-less requests
    working. Guards against silently reverting that flag.
    """
    configure_http_settings("127.0.0.1", MCP_HTTP_DEFAULT_PORT)
    app = create_streamable_http_app()
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    with TestClient(app, base_url="http://127.0.0.1:8001") as client:
        response = client.post(
            MCP_STREAMABLE_HTTP_PATH,
            json=payload,
            headers={"Accept": "application/json, text/event-stream"},
        )
    assert response.status_code != 400, response.text
    assert response.status_code == 200
