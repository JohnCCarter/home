# Handoff

Senast uppdaterad: 2026-06-15 (`app/mcp/` MCP skeleton)

## Aktuell status

**Read-only MVP** med Graph E2E, token refresh, `read_email`, **`app/tools/`**, och **MCP skeleton** som exponerar samma read-only tools.

## Klart

- [x] FastAPI: `GET /calendar`, `GET /mail`, `GET /mail/{message_id}`
- [x] OAuth + token refresh (`get_valid_tokens()`)
- [x] Providers: Mock + Outlook (read-only Graph)
- [x] **`app/tools/`** — `read_calendar`, `read_recent_emails`, `read_email`
- [x] **`ToolResult`** — `ok`, `tool`, `provider`, `data`, `error` med standard error codes
- [x] Endpoints → tools → providers → Graph/mock
- [x] **`app/mcp/`** — MCP stdio-server (FastMCP), endast read-only tools
- [x] MCP → `app/tools/` → providers (ingen direkt provider-access)
- [x] Skriv-actions disabled; read-only scopes endast
- [x] Tester (inkl. tool-kontrakt och MCP-delegering)
- [x] LLM Wiki uppdaterad

## Write-actions

Fortfarande **avstängda**:

- Inga write-tools i `app/tools/`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite`
- Inga delete/move/reply/forward

## Nästa steg

1. **MCP HTTP/HTTPS transport** — lägg till streamable HTTP-transport eller adapter så MCP-endpointen är nåbar över HTTPS (krävs för ChatGPT App/Connector)
2. **ChatGPT developer mode-test** — tunnel/HTTPS-endpoint mot MCP-servern (efter HTTP-transport)
3. **`app/safety/`** — bekräftelse för write-actions (senare)
4. Google provider
5. Wake-word-sidecar

## MCP lokalt (stdio)

**Current MCP skeleton uses stdio transport.** Det är giltigt som första MCP-skeleton och för lokala MCP-klienter (t.ex. Cursor, Claude Desktop).

```bash
PYTHONPATH=. python -m app.mcp.server
```

Stdio-transport; kräver giltig token via befintlig `/auth/microsoft/login` (samma som REST).

**ChatGPT App/Connector-test kräver nästa steg:** en HTTP/HTTPS-nåbar MCP-endpoint. Stdio räcker inte för ChatGPT developer mode — lägg till HTTP/streamable transport eller adapter, testa sedan via tunnel/HTTPS.

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: (se senaste körning i commit-rapport)
Graph: read-only via tools + MCP
Datum: 2026-06-15
```
