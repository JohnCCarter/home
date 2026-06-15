"""Thin MCP bridge to app/tools (no direct provider access)."""

from app.tools import read_calendar as tools_read_calendar
from app.tools import read_email as tools_read_email
from app.tools import read_recent_emails as tools_read_recent_emails


async def invoke_read_calendar() -> dict:
    return (await tools_read_calendar()).to_dict()


async def invoke_read_recent_emails() -> dict:
    return (await tools_read_recent_emails()).to_dict()


async def invoke_read_email(message_id: str) -> dict:
    return (await tools_read_email(message_id)).to_dict()
