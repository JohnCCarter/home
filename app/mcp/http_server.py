"""HTTP/streamable MCP transport for ChatGPT App/Connector preparation."""

import argparse

from app.mcp.schemas import MCP_HTTP_DEFAULT_HOST, MCP_HTTP_DEFAULT_PORT, MCP_STREAMABLE_HTTP_PATH
from app.mcp.server import mcp


def configure_http_settings(host: str, port: int) -> None:
    mcp.settings.host = host
    mcp.settings.port = port


def create_streamable_http_app():
    """Return the Starlette ASGI app for streamable HTTP MCP."""
    return mcp.streamable_http_app()


def mcp_http_endpoint(host: str, port: int) -> str:
    return f"http://{host}:{port}{MCP_STREAMABLE_HTTP_PATH}"


def run_http_server(
    host: str = MCP_HTTP_DEFAULT_HOST,
    port: int = MCP_HTTP_DEFAULT_PORT,
) -> None:
    configure_http_settings(host, port)
    mcp.run(transport="streamable-http")


def main() -> None:
    parser = argparse.ArgumentParser(description="Home Agent MCP server (streamable HTTP)")
    parser.add_argument("--host", default=MCP_HTTP_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=MCP_HTTP_DEFAULT_PORT)
    args = parser.parse_args()
    run_http_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
