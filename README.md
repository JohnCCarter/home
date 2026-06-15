# Home Agent

Personlig kalender- och mail-agent med **Microsoft Graph (Outlook)** i första fasen, och planerat stöd för Google samt klienter som ChatGPT App, MCP och eventuell röst-sidecar.

Detta repo är **inte** Fibonacci eller Genesis-Core-V2.

## Funktioner (MVP)

- Read-only kalender och inkorg via Microsoft Graph
- OAuth 2.0 med PKCE (`/auth/microsoft/login`)
- `MockProvider` när ingen token finns (lokal utveckling utan Azure)
- Skriv-actions medvetet disabled tills safety-lager finns

## Installation

```bash
git clone <repo-url>
cd home
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fyll i dina Azure-värden lokalt
```

## Lokal körning

### FastAPI (REST + OAuth)

```bash
uvicorn app.main:app --reload --port 8000
```

| Endpoint | Beskrivning |
|----------|-------------|
| `GET /calendar` | Kalenderhändelser (mock eller Outlook) |
| `GET /mail` | Senaste inkorgsmeddelanden |
| `GET /auth/microsoft/login` | Starta Microsoft-inloggning |

### MCP (read-only tools)

**Stdio** — lokala MCP-klienter (Cursor, Claude Desktop):

```bash
PYTHONPATH=. python -m app.mcp.server
```

**HTTP / streamable** — ChatGPT App/Connector-förberedelse:

```bash
PYTHONPATH=. python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

**Tunnel-test (dev only, ej production):** DNS rebinding-skydd tillåter endast localhost som default. För HTTPS-tunnel, sätt explicit tillåten tunnel-host:

```bash
# Exempel: temporär tunnel-domän från localhost.run / ngrok / cloudflared
export MCP_DEV_ALLOWED_HOSTS=your-tunnel-host.example.com
PYTHONPATH=. python -m app.mcp.http_server --host 127.0.0.1 --port 8001

# Alternativ: CLI-flagga (samma dev-only semantik)
PYTHONPATH=. python -m app.mcp.http_server --dev-allowed-host your-tunnel-host.example.com
```

MCP connector URL: `https://<tunnel-host>/mcp` — exponera **endast** port 8001, inte REST/OAuth på 8000.

**OpenAI UI Tunnel (dev only, rekommenderat för ChatGPT-test):**

1. I ChatGPT: **New App** → **Connection** → **Tunnel** → **Create tunnel**
2. Ange lokal MCP endpoint: `http://127.0.0.1:8001/mcp`
3. Starta MCP HTTP med OpenAI tunnel dev-mode (tillåter ChatGPT origins):

```powershell
# Windows PowerShell
$env:PYTHONPATH="."
$env:MCP_DEV_OPENAI_TUNNEL="1"
python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

```bash
# bash
export PYTHONPATH=.
export MCP_DEV_OPENAI_TUNNEL=1
PYTHONPATH=. python -m app.mcp.http_server --host 127.0.0.1 --port 8001
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

## Tester

```bash
PYTHONPATH=. pytest -q
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
