# Handoff

Senast uppdaterad: 2026-06-15 (OpenAI Secure MCP Tunnel runtime)

## Aktuell status (runtime)

| Tjänst | Port / URL | Status |
|--------|------------|--------|
| REST / OAuth (FastAPI) | `http://127.0.0.1:8000` | Kör lokalt |
| MCP HTTP (streamable) | `http://127.0.0.1:8001/mcp` | Kör lokalt |
| tunnel-client admin UI | `http://127.0.0.1:8080/ui` | `ready` efter `run` |
| OpenAI Platform tunnel | **Home Agent** | Registrerad via tunnel-client |

**Verifierat på utvecklingsmaskin:**

- `tunnel-client doctor` — API key OK, tunnel ID OK, MCP connection OK
- `tunnel-client run` — `ready`
- OAuth metadata-varning i doctor är **förväntad** — ChatGPT-connector använder **No auth**

**Nästa manuella steg:** ChatGPT UI-test (se nedan).

## Klart (repo)

- [x] FastAPI: `GET /calendar`, `GET /mail`, `GET /mail/{message_id}`
- [x] OAuth + token refresh (`get_valid_tokens()`)
- [x] Providers: Mock + Outlook (read-only Graph)
- [x] **`app/tools/`** — `read_calendar`, `read_recent_emails`, `read_email`
- [x] **`ToolResult`** — `ok`, `tool`, `provider`, `data`, `error`
- [x] **`app/mcp/`** — MCP stdio + HTTP (FastMCP), endast read-only tools
- [x] **Dev tunnel hosts** — `MCP_DEV_ALLOWED_HOSTS` / `--dev-allowed-host`
- [x] **OpenAI Tunnel dev-mode** — `MCP_DEV_OPENAI_TUNNEL=1` / `--openai-tunnel`
- [x] **`read_email` not_found** — Graph 400/404 → `not_found`
- [x] MCP → `app/tools/` → providers (ingen direkt provider-access)
- [x] Skriv-actions disabled; read-only scopes endast
- [x] Tester (tool-kontrakt, MCP stdio och HTTP)
- [x] **uv-pakethantering** — `pyproject.toml` + `uv.lock` (source of truth; `requirements.txt` legacy-fallback)

## Write-actions

Fortfarande **avstängda**:

- Inga write-tools i `app/tools/`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite`
- Inga delete/move/reply/forward

## Fortsätt hemma — snabbstart

Öppna **tre terminaler** (Git Bash rekommenderas på Windows). Använd `export` — inte PowerShell `$env:` i Git Bash.

Första gången: `uv sync --group dev` från repo-roten.

### Terminal 1 — Backend (REST + OAuth)

```bash
cd <repo-root>
uv run uvicorn app.main:app --port 8000
```

### Terminal 2 — MCP HTTP

```bash
cd <repo-root>
export MCP_DEV_OPENAI_TUNNEL=1
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

| | |
|---|---|
| **Endpoint** | `http://127.0.0.1:8001/mcp` |
| **Tools** | `read_calendar`, `read_recent_emails`, `read_email` |
| **Microsoft-auth** | Via REST: `http://localhost:8000/auth/microsoft/login` |

### Terminal 3 — tunnel-client

`tools/tunnel-client/` är **gitignored** — ladda ner igen på hemdatorn om mappen saknas:

- [tunnel-client v0.0.9 windows-amd64](https://github.com/openai/tunnel-client/releases/tag/v0.0.9--context-conduit-topaz)

```bash
cd <repo-root>/tools/tunnel-client
export CONTROL_PLANE_API_KEY="<set locally; do not commit>"
./tunnel-client.exe doctor --profile home-agent --explain
./tunnel-client.exe run --profile home-agent
```

Profil `home-agent` lagras lokalt i `~/.config/tunnel-client/home-agent.yaml` (ej i repo). På ny maskin: `init` med tunnel-ID från [OpenAI Platform → Tunnels](https://platform.openai.com/settings/organization/tunnels) (**Home Agent**). Tunnel-ID måste vara `tunnel_` + exakt 32 tecken `a-z0-9`.

### ChatGPT UI

1. [ChatGPT → Connectors](https://chatgpt.com/#settings/Connectors)
2. **Developer mode** → **New App** → **Tunnel**
3. Välj **Home Agent** → **No auth**
4. Verifiera tools: `read_calendar`, `read_recent_emails`, `read_email`
5. Testa t.ex. *"Vad har jag i kalendern imorgon?"*

Lokal status under körning: `http://127.0.0.1:8080/ui`

## Secrets — aldrig i git eller docs

Får **aldrig** committas, visas i chat eller skrivas i dokumentation:

- `CONTROL_PLANE_API_KEY` och andra OpenAI API-nycklar
- Microsoft client secret
- Access tokens / refresh tokens
- `token_store.json`
- `.env` (kopiera från `.env.example` lokalt)
- Privata mailtexter eller kalenderdetaljer

`tools/tunnel-client/` (inkl. `tunnel-client.exe`) committas inte.

## MCP lokalt (referens)

### Stdio

```bash
uv run python -m app.mcp.server
```

### HTTP / streamable

```bash
export MCP_DEV_OPENAI_TUNNEL=1
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

DNS rebinding-skydd är **på** som default (localhost only). `MCP_DEV_OPENAI_TUNNEL=1` lägger till ChatGPT/OpenAI **origins** only.

### Alternativ: tillfällig HTTPS-tunnel (dev)

```bash
export MCP_DEV_ALLOWED_HOSTS=<temporary-tunnel-host>
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

## Nästa steg (efter ChatGPT-test)

1. **`app/safety/`** — bekräftelse för write-actions (senare)
2. Google provider
3. Wake-word-sidecar

## Senaste verifiering

```text
Kommando: uv run pytest -q
Resultat: 77 passed
Graph: read-only via tools + MCP (stdio + HTTP)
Datum: 2026-06-15
```
