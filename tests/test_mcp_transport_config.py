import pytest

from app.mcp.http_server import configure_http_settings
from app.mcp.transport_config import (
    MCP_DEV_ALLOWED_HOSTS_ENV,
    MCP_DEV_OPENAI_TUNNEL_ENV,
    OPENAI_TUNNEL_DEV_ORIGINS,
    apply_mcp_transport_security,
    build_transport_security,
)
from app.mcp.schemas import READ_ONLY_TOOL_NAMES
from app.mcp.server import mcp
from app.providers.outlook_provider import GraphApiError
from mcp.server.transport_security import TransportSecurityMiddleware


def test_default_transport_security_is_localhost_only():
    settings = build_transport_security(bind_host="127.0.0.1")
    assert settings.enable_dns_rebinding_protection is True
    assert "127.0.0.1:*" in settings.allowed_hosts
    assert "tunnel.example.com" not in settings.allowed_hosts
    assert "https://chatgpt.com" not in settings.allowed_origins


def test_default_has_no_host_wildcard():
    settings = build_transport_security(bind_host="127.0.0.1")
    assert not any(host in ("*", "*:*") or host.startswith("*.") for host in settings.allowed_hosts)


def test_openai_tunnel_dev_mode_adds_chatgpt_origins_only(monkeypatch):
    monkeypatch.setenv(MCP_DEV_OPENAI_TUNNEL_ENV, "1")
    settings = build_transport_security(bind_host="127.0.0.1")
    for origin in OPENAI_TUNNEL_DEV_ORIGINS:
        assert origin in settings.allowed_origins
    assert "tunnel.example.com" not in settings.allowed_hosts


def test_openai_tunnel_dev_mode_does_not_change_hosts_without_explicit_host(monkeypatch):
    monkeypatch.setenv(MCP_DEV_OPENAI_TUNNEL_ENV, "1")
    settings = build_transport_security(bind_host="127.0.0.1")
    middleware = TransportSecurityMiddleware(settings)
    assert middleware._validate_host("127.0.0.1:8001") is True
    assert middleware._validate_host("tunnel.example.com") is False


def test_openai_tunnel_dev_mode_opt_in_via_cli_flag():
    settings = build_transport_security(bind_host="127.0.0.1", enable_openai_tunnel_dev=True)
    assert "https://chatgpt.com" in settings.allowed_origins


def test_openai_tunnel_dev_mode_off_by_default(monkeypatch):
    monkeypatch.delenv(MCP_DEV_OPENAI_TUNNEL_ENV, raising=False)
    settings = build_transport_security(bind_host="127.0.0.1", enable_openai_tunnel_dev=False)
    assert "https://chatgpt.com" not in settings.allowed_origins


def test_openai_tunnel_origin_allowed_when_dev_mode_enabled():
    settings = build_transport_security(bind_host="127.0.0.1", enable_openai_tunnel_dev=True)
    middleware = TransportSecurityMiddleware(settings)
    assert middleware._validate_origin("https://chatgpt.com") is True
    assert middleware._validate_origin("https://chat.openai.com") is True


def test_no_write_tools_exposed():
    import asyncio

    async def _list():
        return await mcp.list_tools()

    tools = asyncio.run(_list())
    tool_names = {tool.name for tool in tools}
    assert tool_names == set(READ_ONLY_TOOL_NAMES)
    assert "send_email" not in tool_names
    assert "delete_email" not in tool_names


def test_dev_allowed_hosts_opt_in_via_env(monkeypatch):
    monkeypatch.setenv(MCP_DEV_ALLOWED_HOSTS_ENV, "tunnel.example.com")
    settings = build_transport_security(bind_host="127.0.0.1")
    assert "tunnel.example.com" in settings.allowed_hosts
    assert "tunnel.example.com:*" in settings.allowed_hosts


def test_dev_allowed_hosts_opt_in_via_cli_extra():
    settings = build_transport_security(
        bind_host="127.0.0.1",
        extra_allowed_hosts=["abc123.lhr.life"],
    )
    assert "abc123.lhr.life" in settings.allowed_hosts


def test_tunnel_host_rejected_without_dev_opt_in():
    settings = build_transport_security(bind_host="127.0.0.1")
    middleware = TransportSecurityMiddleware(settings)
    assert middleware._validate_host("127.0.0.1:8001") is True
    assert middleware._validate_host("tunnel.example.com") is False


def test_tunnel_host_allowed_with_dev_opt_in():
    settings = build_transport_security(
        bind_host="127.0.0.1",
        extra_allowed_hosts=["tunnel.example.com"],
    )
    middleware = TransportSecurityMiddleware(settings)
    assert middleware._validate_host("tunnel.example.com") is True


def test_configure_http_settings_applies_dev_hosts():
    from app.mcp.server import mcp

    configure_http_settings("127.0.0.1", 8001, dev_allowed_hosts=["tunnel.example.com"])
    middleware = TransportSecurityMiddleware(mcp.settings.transport_security)
    assert middleware._validate_host("tunnel.example.com") is True
    apply_mcp_transport_security(mcp, bind_host="127.0.0.1")


@pytest.mark.asyncio
async def test_read_email_graph_400_maps_to_not_found():
    from app.tools.contracts import map_read_email_graph_error

    error = map_read_email_graph_error(
        GraphApiError(400, "Microsoft Graph request failed with status 400.")
    )
    assert error.code == "not_found"
    assert error.retryable is False


@pytest.mark.asyncio
async def test_read_email_nonexistent_id_maps_to_not_found_via_tools(monkeypatch):
    from app.mcp.server import mcp_read_email
    from app.tools.email_tools import read_email

    class FakeProvider:
        async def read_email(self, message_id: str):
            raise GraphApiError(400, "Email message not found.")

    async def fake_get_provider_with_name():
        return FakeProvider(), "outlook"

    monkeypatch.setattr("app.tools.email_tools.get_provider_with_name", fake_get_provider_with_name)

    tool_result = await read_email("nonexistent-id")
    assert tool_result.ok is False
    assert tool_result.error.code == "not_found"

    monkeypatch.setattr("app.mcp.bridge.tools_read_email", read_email)
    mcp_result = await mcp_read_email("nonexistent-id")
    assert mcp_result["ok"] is False
    assert mcp_result["error"]["code"] == "not_found"
