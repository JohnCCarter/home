# Handoff

Senast uppdaterad: 2026-06-15 (`app/mcp/http_server.py` HTTP transport)

## Aktuell status

**Read-only MVP** med Graph E2E, token refresh, `read_email`, **`app/tools/`**, och **MCP** med både stdio och HTTP/streamable transport.

## Klart

- [x] FastAPI: `GET /calendar`, `GET /mail`, `GET /mail/{message_id}`
- [x] OAuth + token refresh (`get_valid_tokens()`)
- [x] Providers: Mock + Outlook (read-only Graph)
- [x] **`app/tools/`** — `read_calendar`, `read_recent_emails`, `read_email`
- [x] **`ToolResult`** — `ok`, `tool`, `provider`, `data`, `error` med standard error codes
- [x] Endpoints → tools → providers → Graph/mock
- [x] **`app/mcp/`** — MCP stdio-server (FastMCP), endast read-only tools
- [x] **`app/mcp/http_server.py`** — streamable HTTP-transport på `/mcp`
- [x] MCP → `app/tools/` → providers (ingen direkt provider-access)
- [x] Skriv-actions disabled; read-only scopes endast
- [x] Tester (inkl. tool-kontrakt, MCP stdio och HTTP)
- [x] LLM Wiki uppdaterad

## Write-actions

Fortfarande **avstängda**:

- Inga write-tools i `app/tools/`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite`
- Inga delete/move/reply/forward

## Nästa steg

1. **Tunnel/HTTPS + ChatGPT developer mode-test** — exponera `http://127.0.0.1:8001/mcp` via HTTPS (ngrok/Cloudflare e.d., ej i repo)
2. **`app/safety/`** — bekräftelse för write-actions (senare)
3. Google provider
4. Wake-word-sidecar

## MCP lokalt

### Stdio (behålls)

```bash
PYTHONPATH=. python -m app.mcp.server
```

För lokala MCP-klienter (Cursor, Claude Desktop). Stdio-transport.

### HTTP / streamable (ny)

```bash
PYTHONPATH=. python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

| | |
|---|---|
| **Endpoint** | `http://127.0.0.1:8001/mcp` |
| **Transport** | FastMCP `streamable-http` |
| **Tools** | `read_calendar`, `read_recent_emails`, `read_email` |
| **Auth** | Samma token-store som REST (`/auth/microsoft/login` på port 8000) |

ChatGPT App/Connector kräver HTTPS — nästa steg är tunnel mot HTTP-endpointen ovan, inte ny OAuth.

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: (se senaste körning i commit-rapport)
Graph: read-only via tools + MCP (stdio + HTTP)
Datum: 2026-06-15
```
