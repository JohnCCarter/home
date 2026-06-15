import pytest

from app.mcp.http_server import configure_http_settings
from app.mcp.transport_config import (
    MCP_DEV_ALLOWED_HOSTS_ENV,
    apply_mcp_transport_security,
    build_transport_security,
)
from app.providers.outlook_provider import GraphApiError
from mcp.server.transport_security import TransportSecurityMiddleware


def test_default_transport_security_is_localhost_only():
    settings = build_transport_security(bind_host="127.0.0.1")
    assert settings.enable_dns_rebinding_protection is True
    assert "127.0.0.1:*" in settings.allowed_hosts
    assert "tunnel.example.com" not in settings.allowed_hosts


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
