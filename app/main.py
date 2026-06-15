from dataclasses import asdict
from html import escape
from typing import Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.auth.microsoft import get_valid_tokens, router as microsoft_auth_router
from app.auth.token_store import has_stored_tokens
from app.providers.base import CalendarEvent, EmailMessage
from app.providers.mock_provider import MockProvider
from app.providers.outlook_provider import GraphApiError, OutlookProvider

app = FastAPI(title="genesis-core-home-agent")
app.include_router(microsoft_auth_router)


async def _get_provider():
    tokens = await get_valid_tokens()
    access_token = tokens.get("access_token") if tokens else None
    if access_token:
        return OutlookProvider(access_token=access_token)
    if has_stored_tokens():
        raise HTTPException(
            status_code=401,
            detail="Token expired or refresh failed. Please re-authenticate via /auth/microsoft/login",
        )
    return MockProvider()


def _serialize(items: List[Any]) -> List[dict]:
    serialized: List[dict] = []
    for item in items:
        row = asdict(item)
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                row[key] = value.isoformat()
        serialized.append(row)
    return serialized


def _wants_html(request: Request) -> bool:
    accept = request.headers.get("accept", "")
    return "text/html" in accept


def _error_page(title: str, message: str, status_code: int = 500) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem; }}
    h1 {{ color: #b45309; }}
    a {{ color: #1d4ed8; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <p>{escape(message)}</p>
  <p><a href="/auth/microsoft/login">Login again</a></p>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


def _list_page(title: str, items: List[dict], columns: List[str]) -> HTMLResponse:
    if not items:
        body = "<p>No items found.</p>"
    else:
        headers = "".join(f"<th>{escape(column)}</th>" for column in columns)
        rows = []
        for item in items:
            cells = "".join(f"<td>{escape(str(item.get(column, '')))}</td>" for column in columns)
            rows.append(f"<tr>{cells}</tr>")
        body = f"<table border=\"1\" cellpadding=\"8\" cellspacing=\"0\"><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 56rem; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ color: #0f766e; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th {{ text-align: left; background: #f3f4f6; }}
    a {{ color: #1d4ed8; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  {body}
  <p><a href="/calendar">Calendar</a> · <a href="/mail">Mail</a> · <a href="/auth/microsoft/login">Login</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/calendar")
async def get_calendar(request: Request):
    try:
        provider = await _get_provider()
        events: List[CalendarEvent] = await provider.read_calendar()
        data = _serialize(events)
    except GraphApiError as exc:
        if _wants_html(request):
            return _error_page("Calendar unavailable", exc.message, status_code=exc.status_code)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if _wants_html(request):
        return _list_page("Calendar", data, ["subject", "start", "end"])
    return data


@app.get("/mail")
async def get_mail(request: Request):
    try:
        provider = await _get_provider()
        emails: List[EmailMessage] = await provider.read_recent_emails()
        data = _serialize(emails)
    except GraphApiError as exc:
        if _wants_html(request):
            return _error_page("Mail unavailable", exc.message, status_code=exc.status_code)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if _wants_html(request):
        return _list_page("Mail", data, ["subject", "sender", "received_at"])
    return data
