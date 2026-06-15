"""MCP server skeleton exposing Home Agent read-only tools."""

from mcp.server.fastmcp import FastMCP

from app.mcp.bridge import invoke_read_calendar, invoke_read_email, invoke_read_recent_emails
from app.mcp.schemas import TOOL_DESCRIPTIONS

mcp = FastMCP("Home Agent")


@mcp.tool(name="read_calendar", description=TOOL_DESCRIPTIONS["read_calendar"])
async def mcp_read_calendar() -> dict:
    return await invoke_read_calendar()


@mcp.tool(name="read_recent_emails", description=TOOL_DESCRIPTIONS["read_recent_emails"])
async def mcp_read_recent_emails() -> dict:
    return await invoke_read_recent_emails()


@mcp.tool(name="read_email", description=TOOL_DESCRIPTIONS["read_email"])
async def mcp_read_email(message_id: str) -> dict:
    return await invoke_read_email(message_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
