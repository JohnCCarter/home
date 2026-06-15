"""MCP tool metadata for Home Agent read-only tools."""

READ_ONLY_TOOL_NAMES = (
    "read_calendar",
    "read_recent_emails",
    "read_email",
)

MCP_HTTP_DEFAULT_HOST = "127.0.0.1"
MCP_HTTP_DEFAULT_PORT = 8001
MCP_STREAMABLE_HTTP_PATH = "/mcp"

TOOL_DESCRIPTIONS: dict[str, str] = {
    "read_calendar": "Read upcoming calendar events from the connected mailbox (read-only).",
    "read_recent_emails": "Read recent inbox messages (read-only).",
    "read_email": "Read a single email message by Graph message id (read-only).",
}

# JSON shape returned by every MCP tool (matches app.tools.contracts.ToolResult).
TOOL_RESULT_EXAMPLE_SUCCESS = {
    "ok": True,
    "tool": "read_calendar",
    "provider": "outlook",
    "data": [],
    "error": None,
}

TOOL_RESULT_EXAMPLE_FAILURE = {
    "ok": False,
    "tool": "read_calendar",
    "provider": "outlook",
    "data": None,
    "error": {
        "code": "auth_required",
        "message": "Token expired or refresh failed. Please re-authenticate via /auth/microsoft/login",
        "retryable": False,
    },
}
