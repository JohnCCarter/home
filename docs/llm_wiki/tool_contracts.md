# Tool-kontrakt

Alla read-only tools returnerar **samma JSON-form** via `app/tools/contracts.py`.

## Success

```json
{
  "ok": true,
  "tool": "read_calendar",
  "provider": "outlook",
  "data": [],
  "error": null
}
```

## Failure

```json
{
  "ok": false,
  "tool": "read_calendar",
  "provider": "outlook",
  "data": null,
  "error": {
    "code": "auth_required",
    "message": "Please re-authenticate via /auth/microsoft/login",
    "retryable": false
  }
}
```

## Error codes

| Code | HTTP | Retryable | Typiskt scenario |
|------|------|-----------|------------------|
| `auth_required` | 401 | nej | Token saknas/expired, refresh misslyckades |
| `permission_denied` | 403 | nej | Otillräcklig Graph-behörighet |
| `not_found` | 404 | nej | Mail hittades inte |
| `rate_limited` | 429 | ja | Graph throttling |
| `provider_error` | 502 | ja | Graph 5xx |
| `validation_error` | 400 | nej | Ogiltig input (t.ex. tom `message_id`) |
| `unknown_error` | 500 | nej | Övrigt provider-fel |

## Implementerade tools (read-only)

| Tool | Modul | Provider-metod |
|------|-------|----------------|
| `read_calendar` | `app/tools/calendar_tools.py` | `read_calendar()` |
| `read_recent_emails` | `app/tools/email_tools.py` | `read_recent_emails()` |
| `read_email` | `app/tools/email_tools.py` | `read_email(message_id)` |

Write-tools (`create_calendar_event`, `draft_email`, `send_email`) är **inte** implementerade i tool-lagret.

## Flöde

```text
HTTP route / MCP tool → app/tools → provider → Graph/mock
```

| Klient | Väg |
|--------|-----|
| REST | `GET /calendar`, `GET /mail`, `GET /mail/{message_id}` |
| MCP (stdio) | `read_calendar`, `read_recent_emails`, `read_email` via `python -m app.mcp.server` |
| MCP (HTTP) | Samma tools via `http://127.0.0.1:8001/mcp` (`python -m app.mcp.http_server`) |

REST returnerar `data`-delen vid success (bakåtkompatibelt). MCP returnerar full `ToolResult` oavsett transport.

## MCP tools (read-only)

| MCP tool | app/tools |
|----------|-----------|
| `read_calendar` | `read_calendar()` |
| `read_recent_emails` | `read_recent_emails()` |
| `read_email(message_id)` | `read_email(message_id)` |

Inga write-tools exponeras via MCP.

## `read_calendar`

| | |
|---|---|
| **Input** | Inga (limit via provider default 10) |
| **Output `data`** | Lista: `id`, `subject`, `start`, `end` (ISO-8601) |
| **Säkerhet** | Läs — körs direkt |

## `read_recent_emails`

| | |
|---|---|
| **Input** | Inga (limit via provider default 10) |
| **Output `data`** | Lista: `id`, `subject`, `sender`, `received_at` |
| **Säkerhet** | Läs — körs direkt |

## `read_email`

| | |
|---|---|
| **Input** | `message_id` (str) |
| **Output `data`** | `id`, `subject`, `sender`, `received_at`, `body_preview`, `body` |
| **Säkerhet** | Läs — körs direkt; body loggas aldrig |

## Planerade write-tools (ej implementerade)

- `create_calendar_event` — kräver `Calendars.ReadWrite` + safety
- `draft_email` / `send_email` — kräver `Mail.Send` + safety
- Inga delete-tools i MVP
