# Handoff

Senast uppdaterad: 2026-06-15 (OpenAI UI Tunnel dev-mode)

## Aktuell status

**Read-only MVP** med Graph E2E, token refresh, `read_email`, **`app/tools/`**, **MCP** (stdio + HTTP), dev tunnel hosts, och **OpenAI Tunnel dev-mode**.

## Klart

- [x] FastAPI: `GET /calendar`, `GET /mail`, `GET /mail/{message_id}`
- [x] OAuth + token refresh (`get_valid_tokens()`)
- [x] Providers: Mock + Outlook (read-only Graph)
- [x] **`app/tools/`** — `read_calendar`, `read_recent_emails`, `read_email`
- [x] **`ToolResult`** — `ok`, `tool`, `provider`, `data`, `error` med standard error codes
- [x] Endpoints → tools → providers → Graph/mock
- [x] **`app/mcp/`** — MCP stdio-server (FastMCP), endast read-only tools
- [x] **`app/mcp/http_server.py`** — streamable HTTP-transport på `/mcp`
- [x] **Dev-only tunnel hosts** — `MCP_DEV_ALLOWED_HOSTS` / `--dev-allowed-host`
- [x] **OpenAI UI Tunnel dev-mode** — `MCP_DEV_OPENAI_TUNNEL=1` / `--openai-tunnel`
- [x] **`read_email` not_found** — Graph 400/404 → `not_found` via tools/MCP
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

1. **Manuell ChatGPT developer mode-test** — OpenAI UI Tunnel mot `http://127.0.0.1:8001/mcp` med `MCP_DEV_OPENAI_TUNNEL=1`
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

**Tunnel-test (dev only):**

```bash
export MCP_DEV_ALLOWED_HOSTS=<temporary-tunnel-host>
PYTHONPATH=. python -m app.mcp.http_server --host 127.0.0.1 --port 8001
# eller: --dev-allowed-host <temporary-tunnel-host>
```

| | |
|---|---|
| **Endpoint** | `http://127.0.0.1:8001/mcp` (via tunnel: `https://<host>/mcp`) |
| **Transport** | FastMCP `streamable-http` |
| **Tools** | `read_calendar`, `read_recent_emails`, `read_email` |
| **Auth** | Samma token-store som REST (`/auth/microsoft/login` på port 8000) |
| **Tunnel** | Exponera endast port **8001**; ingen permanent tunnel-config i repo |

DNS rebinding-skydd är **på** som default (localhost only). Tunnel-host kräver explicit `MCP_DEV_ALLOWED_HOSTS` — inte production-config.

### OpenAI UI Tunnel (rekommenderat för ChatGPT-test)

1. ChatGPT: **New App** → **Connection** → **Tunnel** → **Create tunnel**
2. Lokal MCP endpoint: `http://127.0.0.1:8001/mcp`
3. Starta MCP:

```powershell
$env:PYTHONPATH="."
$env:MCP_DEV_OPENAI_TUNNEL="1"
python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

4. **Authentication:** No auth / None (skriv aldrig Microsoft client secret i ChatGPT UI)
5. **Om Host-fel (421):** `$env:MCP_DEV_ALLOWED_HOSTS="<tunnel-host-without-https>"`

`MCP_DEV_OPENAI_TUNNEL=1` lägger till ChatGPT/OpenAI **origins** only — hosts förblir localhost unless `MCP_DEV_ALLOWED_HOSTS` sätts.

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: (se senaste körning i commit-rapport)
Graph: read-only via tools + MCP (stdio + HTTP)
Datum: 2026-06-15
```
