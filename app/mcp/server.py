"""MCP server skeleton exposing Home Agent read-only tools."""

from mcp.server.fastmcp import FastMCP

from app.mcp.bridge import invoke_read_calendar, invoke_read_email, invoke_read_recent_emails
from app.mcp.result_models import (
    ReadCalendarResultModel,
    ReadEmailResultModel,
    ReadRecentEmailsResultModel,
)
from app.mcp.schemas import MCP_HTTP_DEFAULT_PORT, MCP_STREAMABLE_HTTP_PATH, TOOL_DESCRIPTIONS
from app.mcp.transport_config import apply_mcp_transport_security

mcp = FastMCP(
    "Home Agent",
    host="127.0.0.1",
    port=MCP_HTTP_DEFAULT_PORT,
    streamable_http_path=MCP_STREAMABLE_HTTP_PATH,
    # ChatGPT/OpenAI tunnel forwards tools/call without an mcp-session-id header,
    # which a stateful server rejects with HTTP 400 ("Missing session ID").
    # Stateless mode makes each request self-contained so no session is required.
    stateless_http=True,
)

apply_mcp_transport_security(mcp, bind_host="127.0.0.1")


@mcp.tool(name="read_calendar", description=TOOL_DESCRIPTIONS["read_calendar"])
async def mcp_read_calendar() -> ReadCalendarResultModel:
    return await invoke_read_calendar()


@mcp.tool(name="read_recent_emails", description=TOOL_DESCRIPTIONS["read_recent_emails"])
async def mcp_read_recent_emails() -> ReadRecentEmailsResultModel:
    return await invoke_read_recent_emails()


@mcp.tool(name="read_email", description=TOOL_DESCRIPTIONS["read_email"])
async def mcp_read_email(message_id: str) -> ReadEmailResultModel:
    return await invoke_read_email(message_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
