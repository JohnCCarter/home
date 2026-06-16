from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.auth.microsoft import router as microsoft_auth_router
from app.mcp.schemas import (
    MCP_HTTP_DEFAULT_HOST,
    MCP_HTTP_DEFAULT_PORT,
    MCP_STREAMABLE_HTTP_PATH,
    READ_ONLY_TOOL_NAMES,
)
from app.runtime_metadata import resolve_version, safety_display_label, safety_summary
from app.tools import http_status_for_error, read_calendar, read_email, read_recent_emails
from app.tools.contracts import ToolResult
from app.web_ui import BASE_STYLES, NARROW_MAIN_STYLES

app = FastAPI(title="genesis-core-home-agent")
app.include_router(microsoft_auth_router)

# Static runtime facts surfaced by /health and /status. These never touch the
# mailbox, calendar, tokens, or secrets — they only show that the app is alive
# and which read-only tools it exposes.
MCP_ENDPOINT = f"http://{MCP_HTTP_DEFAULT_HOST}:{MCP_HTTP_DEFAULT_PORT}{MCP_STREAMABLE_HTTP_PATH}"
TUNNEL_ADMIN_UI = "http://127.0.0.1:8080/ui"


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def _error_page(title: str, message: str, status_code: int = 500) -> HTMLResponse:
    from html import escape

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="color-scheme" content="dark" />
  <title>{escape(title)}</title>
  <style>
    {BASE_STYLES}
    {NARROW_MAIN_STYLES}
    h1 {{ color: var(--warn); }}
  </style>
</head>
<body>
  <main>
    <h1>{escape(title)}</h1>
    <p>{escape(message)}</p>
    <p class="nav"><a href="/auth/microsoft/login">Login again</a></p>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


def _list_page(title: str, items: List[dict], columns: List[str]) -> HTMLResponse:
    from html import escape

    if not items:
        body = '<p class="empty">No items found.</p>'
    else:
        headers = "".join(f"<th>{escape(column)}</th>" for column in columns)
        rows = []
        for item in items:
            cells = "".join(f"<td>{escape(str(item.get(column, '')))}</td>" for column in columns)
            rows.append(f"<tr>{cells}</tr>")
        body = f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="color-scheme" content="dark" />
  <title>{escape(title)}</title>
  <style>{BASE_STYLES}</style>
</head>
<body>
  <main>
    <h1>{escape(title)}</h1>
    {body}
    <p class="nav"><a href="/calendar">Calendar</a> · <a href="/mail">Mail</a> · <a href="/auth/microsoft/login">Login</a></p>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html)


def _raise_from_tool_result(result: ToolResult) -> None:
    assert result.error is not None
    raise HTTPException(
        status_code=http_status_for_error(result.error.code),
        detail=result.error.message,
    )


def _handle_tool_result(result: ToolResult, request: Request, html_title: str):
    if result.ok:
        return result.data

    if _wants_html(request):
        status = http_status_for_error(result.error.code) if result.error else 500
        message = result.error.message if result.error else "Request failed"
        return _error_page(html_title, message, status_code=status)

    _raise_from_tool_result(result)


@app.get("/health")
async def get_health() -> dict:
    """Liveness probe. No mailbox/calendar access, no tokens, no login required."""
    return {
        "ok": True,
        "service": "home-agent",
        "mode": "read-only",
        "tools": list(READ_ONLY_TOOL_NAMES),
        "version": resolve_version(),
        "safety": safety_summary(),
    }


@app.get("/status", response_class=HTMLResponse)
async def get_status() -> HTMLResponse:
    """Declarative runtime status page. Shows endpoints and tools only — never
    tokens, secrets, mail, or calendar content. Does not probe liveness of the
    MCP server or tunnel client (that would add failure modes out of scope)."""
    from html import escape

    tool_items = "".join(f"<li><code>{escape(name)}</code></li>" for name in READ_ONLY_TOOL_NAMES)
    safety_items = "".join(
        f"<li>{escape(action)} — {escape(safety_display_label(state))}</li>"
        for action, state in safety_summary().items()
    )
    version = escape(resolve_version())
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="color-scheme" content="dark" />
  <title>Home Agent — status</title>
  <style>
    {BASE_STYLES}
    {NARROW_MAIN_STYLES}
    dt {{ color: var(--muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.03em; }}
    dd {{ margin: 0.2rem 0 0.9rem; }}
    code {{ background: var(--surface-2); padding: 0.1rem 0.35rem; border-radius: 0.3rem; }}
    ul {{ margin: 0.2rem 0 0; padding-left: 1.2rem; }}
  </style>
</head>
<body>
  <main>
    <h1>Home Agent</h1>
    <dl>
      <dt>REST backend</dt><dd>running</dd>
      <dt>Mode</dt><dd>read-only</dd>
      <dt>MCP endpoint</dt><dd><code>{escape(MCP_ENDPOINT)}</code></dd>
      <dt>Tunnel client admin UI</dt><dd><code>{escape(TUNNEL_ADMIN_UI)}</code></dd>
      <dt>Tools</dt><dd><ul>{tool_items}</ul></dd>
      <dt>Safety</dt><dd><ul>{safety_items}</ul></dd>
      <dt>Git commit / version</dt><dd><code>{version}</code></dd>
    </dl>
    <p class="note">Local runtime metadata only — does not check whether the MCP server, tunnel client, or Microsoft Graph are reachable.</p>
    <p class="nav"><a href="/health">/health</a> · <a href="/calendar">Calendar</a> · <a href="/mail">Mail</a></p>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/calendar")
async def get_calendar(request: Request):
    result = await read_calendar()
    data = _handle_tool_result(result, request, "Calendar unavailable")
    if isinstance(data, HTMLResponse):
        return data
    if _wants_html(request):
        return _list_page("Calendar", data, ["subject", "start", "end"])
    return data


@app.get("/mail")
async def get_mail(request: Request):
    result = await read_recent_emails()
    data = _handle_tool_result(result, request, "Mail unavailable")
    if isinstance(data, HTMLResponse):
        return data
    if _wants_html(request):
        return _list_page("Mail", data, ["subject", "sender", "received_at"])
    return data


@app.get("/mail/{message_id:path}")
async def get_mail_message(message_id: str, request: Request):
    result = await read_email(message_id)
    data = _handle_tool_result(result, request, "Mail unavailable")
    if isinstance(data, HTMLResponse):
        return data
    return data
