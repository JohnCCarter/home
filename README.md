# Home Agent

Personlig kalender- och mail-agent med **Microsoft Graph (Outlook)** i första fasen, och planerat stöd för Google samt klienter som ChatGPT App, MCP och eventuell röst-sidecar.

Detta repo är **inte** Fibonacci eller Genesis-Core-V2.

## Funktioner (MVP)

- Read-only kalender och inkorg via Microsoft Graph
- OAuth 2.0 med PKCE (`/auth/microsoft/login`)
- `MockProvider` när ingen token finns (lokal utveckling utan Azure)
- Skriv-actions medvetet disabled tills safety-lager finns

## Installation

**Source of truth:** `pyproject.toml` + `uv.lock`. `requirements.txt` finns kvar som legacy-fallback.

```bash
git clone <repo-url>
cd home
uv sync --group dev
cp .env.example .env        # fyll i dina Azure-värden lokalt
```

Utan [uv](https://docs.astral.sh/uv/): `pip install -r requirements.txt` (ej låst; föredra uv).

## Lokal körning

### FastAPI (REST + OAuth)

```bash
uv run uvicorn app.main:app --reload --port 8000
```

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /calendar` | Kalenderhändelser (mock eller Outlook) |
| `GET /mail` | Senaste inkorgsmeddelanden |
| `GET /auth/microsoft/login` | Starta Microsoft-inloggning |

### MCP (read-only tools)

**Stdio** — lokala MCP-klienter (Cursor, Claude Desktop):

```bash
uv run python -m app.mcp.server
```

**HTTP / streamable** — ChatGPT App/Connector-förberedelse:

```bash
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

**Tunnel-test (dev only, ej production):** DNS rebinding-skydd tillåter endast localhost som default. För HTTPS-tunnel, sätt explicit tillåten tunnel-host:

```bash
# Exempel: temporär tunnel-domän från localhost.run / ngrok / cloudflared
export MCP_DEV_ALLOWED_HOSTS=your-tunnel-host.example.com
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001

# Alternativ: CLI-flagga (samma dev-only semantik)
uv run python -m app.mcp.http_server --dev-allowed-host your-tunnel-host.example.com
```

MCP connector URL: `https://<tunnel-host>/mcp` — exponera **endast** port 8001, inte REST/OAuth på 8000.

**OpenAI UI Tunnel (dev only, rekommenderat för ChatGPT-test):**

1. I ChatGPT: **New App** → **Connection** → **Tunnel** → **Create tunnel**
2. Ange lokal MCP endpoint: `http://127.0.0.1:8001/mcp`
3. Starta MCP HTTP med OpenAI tunnel dev-mode (tillåter ChatGPT origins):

```powershell
# Windows PowerShell
$env:MCP_DEV_OPENAI_TUNNEL="1"
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

```bash
# bash
export MCP_DEV_OPENAI_TUNNEL=1
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
# eller: --openai-tunnel
```

**Authentication i ChatGPT UI:** välj **No auth / None** om möjligt. Skriv aldrig Microsoft client secret i ChatGPT UI. Om UI kräver OAuth — pausa och utred separat.

**Om OpenAI Tunnel ger Host-fel (421):** lägg till specifik tunnel-host (utan `https://`):

```powershell
$env:MCP_DEV_ALLOWED_HOSTS="<tunnel-host-without-https>"
```

Vanligtvis räcker `MCP_DEV_OPENAI_TUNNEL=1` eftersom OpenAI Tunnel proxar mot localhost — extra host behövs bara om UI visar ett specifikt host-namn.

| | |
|---|---|
| MCP endpoint | `http://127.0.0.1:8001/mcp` |
| Tools | `read_calendar`, `read_recent_emails`, `read_email` |

OAuth sker via FastAPI på port 8000 (`/auth/microsoft/login`). MCP HTTP-servern använder samma token-store — ingen separat OAuth.

Utan inloggning används mock-data. Efter OAuth sparas tokens i `token_store.json` (gitignored).

### OpenAI Secure MCP Tunnel (ChatGPT)

Platform-tunnel kräver lokal [tunnel-client](https://github.com/openai/tunnel-client) (ej i repo). Starta REST (`:8000`), MCP HTTP (`:8001` med `MCP_DEV_OPENAI_TUNNEL=1`), sedan `tunnel-client run`. Full runbook: **[docs/llm_wiki/handoff.md](docs/llm_wiki/handoff.md)**.

## Tester

```bash
uv run pytest -q
```

Tester kräver inte riktiga Microsoft-credentials. Se [docs/llm_wiki/testing.md](docs/llm_wiki/testing.md).

## Konfiguration

Kopiera `.env.example` till `.env`. Placeholders — lägg aldrig riktiga secrets i git.

## Dokumentation för AI-agenter

**[docs/llm_wiki/index.md](docs/llm_wiki/index.md)** — LLM Wiki med arkitektur, safety, tools och handoff.

Korta agentregler: **[AGENTS.md](AGENTS.md)**

## Projektstruktur

```text
app/
  auth/         Microsoft OAuth, token store
  providers/    Mock + Outlook (Graph)
  tools/        Read-only tool layer (ToolResult)
  mcp/          MCP stdio + HTTP transport
  main.py       FastAPI routes
tests/
docs/llm_wiki/  Agent-wiki
```
