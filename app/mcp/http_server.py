"""HTTP/streamable MCP transport for ChatGPT App/Connector preparation."""

import argparse

from app.mcp.schemas import MCP_HTTP_DEFAULT_HOST, MCP_HTTP_DEFAULT_PORT, MCP_STREAMABLE_HTTP_PATH
from app.mcp.server import mcp
from app.mcp.transport_config import apply_mcp_transport_security


def configure_http_settings(
    host: str,
    port: int,
    *,
    dev_allowed_hosts: list[str] | None = None,
    dev_allowed_origins: list[str] | None = None,
) -> None:
    mcp.settings.host = host
    mcp.settings.port = port
    apply_mcp_transport_security(
        mcp,
        bind_host=host,
        extra_allowed_hosts=dev_allowed_hosts,
        extra_allowed_origins=dev_allowed_origins,
    )


def create_streamable_http_app():
    """Return the Starlette ASGI app for streamable HTTP MCP."""
    return mcp.streamable_http_app()


def mcp_http_endpoint(host: str, port: int) -> str:
    return f"http://{host}:{port}{MCP_STREAMABLE_HTTP_PATH}"


def run_http_server(
    host: str = MCP_HTTP_DEFAULT_HOST,
    port: int = MCP_HTTP_DEFAULT_PORT,
    *,
    dev_allowed_hosts: list[str] | None = None,
    dev_allowed_origins: list[str] | None = None,
) -> None:
    configure_http_settings(
        host,
        port,
        dev_allowed_hosts=dev_allowed_hosts,
        dev_allowed_origins=dev_allowed_origins,
    )
    mcp.run(transport="streamable-http")


def main() -> None:
    parser = argparse.ArgumentParser(description="Home Agent MCP server (streamable HTTP)")
    parser.add_argument("--host", default=MCP_HTTP_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=MCP_HTTP_DEFAULT_PORT)
    parser.add_argument(
        "--dev-allowed-host",
        action="append",
        default=None,
        help="Dev/test only: extra allowed Host header for tunnel (repeatable). "
        "Prefer MCP_DEV_ALLOWED_HOSTS env for local tunnel testing.",
    )
    parser.add_argument(
        "--dev-allowed-origin",
        action="append",
        default=None,
        help="Dev/test only: extra allowed Origin header (repeatable).",
    )
    args = parser.parse_args()
    run_http_server(
        host=args.host,
        port=args.port,
        dev_allowed_hosts=args.dev_allowed_host,
        dev_allowed_origins=args.dev_allowed_origin,
    )


if __name__ == "__main__":
    main()
