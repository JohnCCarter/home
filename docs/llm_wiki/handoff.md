# Handoff

Senast uppdaterad: 2026-06-16 (Google calendar-vägen komplett inkl. refresh flow, pushat på 65d806e)

## Aktuell status (runtime)

| Tjänst | Port / URL | Status |
|--------|------------|--------|
| REST / OAuth (FastAPI) | `http://127.0.0.1:8000` | Verifierad lokalt |
| MCP HTTP (streamable) | `http://127.0.0.1:8001/mcp` | Verifierad lokalt |
| tunnel-client admin UI | `http://127.0.0.1:8080/ui` | `ready` efter `run` |
| OpenAI Platform tunnel | **Home Agent** | Registrerad via tunnel-client |

**Verifierat på utvecklingsmaskin:**

- `uv lock --check` — OK
- `uv run pytest -q` — 172 passed
- `tunnel-client doctor` — API key OK, tunnel ID OK, MCP connection OK
- `tunnel-client run` — `ready`
- OAuth metadata-varning i doctor är **förväntad** — ChatGPT-connector använder **No auth**

**ChatGPT UI-test:** ✅ Verifierad 2026-06-15 — `read_recent_emails` returnerade riktig Outlook-inbox via hem-tunneln (`tunnel_6a3043a186388191a7bdf21720cab2d2`), end-to-end.

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
- [x] **uv-pakethantering** — `pyproject.toml` + `uv.lock` (source of truth; `requirements.txt` borttagen)

## Write-actions

Fortfarande **avstängda**:

- Inga write-tools i `app/tools/`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite`
- Inga delete/move/reply/forward

## Safety policy layer (2026-06-16)

Safety policy layer is now implemented in `app/safety/policy.py`.

**Current behavior:**

- read actions are allowed
- write actions require `confirmed=True`
- delete actions are forbidden
- unknown actions are denied

Confirmation is **in-band** via a `confirm` argument because `stateless_http=True`
does not support session-based two-step confirmation safely (the ChatGPT tunnel
forwards `tools/call` without an `mcp-session-id`, so there is no session to hold a
pending confirmation between calls).

**New contract:**

- `confirmation_required`
- mapped to HTTP **428**
- mirrored in MCP result models (`app/mcp/result_models.py`)
- sync test (`tests/test_error_code_sync.py`) prevents contract/model drift

**Scope — this is a safety foundation only:**

- **No write tools are enabled yet.**
- **No delete tools are enabled.**
- **No Microsoft Graph write scopes were added.**
- **Providers still do not implement write behavior** (`base.py` write methods raise `NotImplementedError`).

## Runtime status (`/status`, `/health`)

`/status` and `/health` expose safe local runtime metadata only. They do not probe
Microsoft Graph, mailbox/calendar data, MCP liveness, tunnel-client liveness, or
external services. Both surface mode, tools, and a policy-derived safety summary;
`version` is best-effort: `HOME_AGENT_VERSION` → `GIT_COMMIT` →
`git rev-parse --short HEAD` → `unknown`. (Test count lives here in the handoff, not
in the runtime endpoint — sanity-check a fresh clone with `uv run --no-sync pytest -q`.)

---

## Fortsätt hemma — resume från ren clone/pull

```bash
git pull
uv sync --group dev
uv run pytest -q
```

Förväntat: **172 passed** (siffran växer med nya tester — kontrollera mot senaste commit).

### Lokal miljö hemma (ej i git)

| Fil / mapp | I git? | Åtgärd hemma |
|------------|--------|--------------|
| `.env` | **Nej** | Kopiera från `.env.example`, fyll i Azure-värden |
| `token_store.json` | **Nej** | Skapas efter Microsoft OAuth |
| `CONTROL_PLANE_API_KEY` | **Nej** | Sätt lokalt i terminal eller lokal `.env` — aldrig i docs/chat/git |
| `tools/tunnel-client/` | **Nej** | Ladda ner binary (se Terminal 3) |

**Microsoft-auth:** Om token saknas, öppna `http://localhost:8000/auth/microsoft/login` efter REST startat.

**OpenAI API key:** Sätt `CONTROL_PLANE_API_KEY` lokalt i terminal eller lokal `.env` — aldrig i docs, chat eller git.

---

## Startkommandon hemma

**Enklast (PowerShell scripts)** — ett script per terminal:

```powershell
.\scripts\start_rest.ps1            # Terminal 1 — REST/OAuth :8000
.\scripts\start_mcp.ps1             # Terminal 2 — MCP HTTP :8001 (sätter MCP_DEV_OPENAI_TUNNEL=1)
.\scripts\start_tunnel_client.ps1   # Terminal 3 — tunnel-client (läser nyckeln ur .env, skriver aldrig ut den)
```

`start_tunnel_client.ps1` läser `CONTROL_PLANE_API_KEY` ur lokal `.env`, skapar inte `.env`, committar inget, och kräver att `tools\tunnel-client\` finns (gitignored).

**Tunnel-profil per dator** — scriptet tar `-Profile` (default `home-agent`):

```powershell
.\scripts\start_tunnel_client.ps1                          # hemdator (default: home-agent)
.\scripts\start_tunnel_client.ps1 -Profile home-agent-work # jobbdator
# eller: $env:TUNNEL_PROFILE="home-agent-work"; .\scripts\start_tunnel_client.ps1
```

Samma `.env`/`CONTROL_PLANE_API_KEY`/Azure-config på båda datorerna — endast tunnel-profil/tunnel-ID skiljer. Hemprofilen heter fortfarande `home-agent` (oförändrad). Skapa jobbprofilen en gång (tunnel-ID aldrig i git):

```powershell
cd tools\tunnel-client
.\tunnel-client.exe init --profile home-agent-work --tunnel-id <work-computer-tunnel-id> --mcp-server-url http://127.0.0.1:8001/mcp --force
.\tunnel-client.exe doctor --profile home-agent-work --explain
```

Statussidor under körning: `http://127.0.0.1:8000/health` (JSON), `http://127.0.0.1:8000/status` (HTML), `http://127.0.0.1:8080/ui` (tunnel admin).

**Manuellt** — öppna **tre terminaler**. Git Bash: använd `export`. PowerShell: använd `$env:`.

### Terminal 1 — REST / backend

```bash
cd <repo-root>
uv run uvicorn app.main:app --port 8000
```

### Terminal 2 — MCP HTTP

**bash / Git Bash:**

```bash
cd <repo-root>
export MCP_DEV_OPENAI_TUNNEL=1
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

**PowerShell:**

```powershell
cd <repo-root>
$env:MCP_DEV_OPENAI_TUNNEL="1"
uv run python -m app.mcp.http_server --host 127.0.0.1 --port 8001
```

| | |
|---|---|
| **Endpoint** | `http://127.0.0.1:8001/mcp` |
| **Tools** | `read_calendar`, `read_recent_emails`, `read_email` |
| **Microsoft-auth** | `http://localhost:8000/auth/microsoft/login` |

### Terminal 3 — tunnel-client

`tools/tunnel-client/` är **gitignored** — ladda ner på hemdatorn om mappen saknas:

- [tunnel-client v0.0.9 windows-amd64](https://github.com/openai/tunnel-client/releases/tag/v0.0.9--context-conduit-topaz)

**bash / Git Bash:**

```bash
cd <repo-root>/tools/tunnel-client
export CONTROL_PLANE_API_KEY="<set locally; never commit>"
./tunnel-client.exe doctor --profile home-agent --explain
./tunnel-client.exe run --profile home-agent
```

**PowerShell:**

```powershell
cd <repo-root>\tools\tunnel-client
$env:CONTROL_PLANE_API_KEY="<set locally; never commit>"
.\tunnel-client.exe doctor --profile home-agent --explain
.\tunnel-client.exe run --profile home-agent
```

Profil `home-agent` lagras lokalt i **`%APPDATA%\tunnel-client\home-agent.yaml`** (Windows; ej i repo) — **inte** `~/.config/...` (det är där Git Bash letar och misslyckas). **Starta därför tunnel-client från PowerShell, inte Git Bash.** Hemma använder en **egen** tunnel `tunnel_6a3043a186388191a7bdf21720cab2d2` (jobb och hem delar inte tunnel — se Felsökning nedan). På ny maskin: `init` med tunnel-ID från [OpenAI Platform → Tunnels](https://platform.openai.com/settings/organization/tunnels). Tunnel-ID måste vara `tunnel_` + exakt 32 tecken `a-z0-9`.

### Admin UI

`http://127.0.0.1:8080/ui` — lokal status under körning.

**Läsbar mörk UI (dev):** tunnel-client:s inbyggda UI har låg kontrast på vit bakgrund. Kör proxyn och öppna `:8082` istället:

```bash
uv run python tools/tunnel_ui_proxy.py
```

Öppna `http://127.0.0.1:8082/ui` (kräver att tunnel-client redan kör på `:8080`).

### ChatGPT

1. [ChatGPT → Connectors](https://chatgpt.com/#settings/Connectors)
2. **Developer mode** → **New App** → **Tunnel**
3. Välj **Home Agent** → **No auth**
4. Verifiera tools: `read_calendar`, `read_recent_emails`, `read_email`
5. Testa t.ex. *"Vad har jag i kalendern imorgon?"*

---

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

## Felsökning & lärdomar (2026-06-15, hemma)

När Home Agent inte gick att nå från ChatGPT visade det sig vara tre separata orsaker:

### 1. En tunnel = en aktiv tunnel-client
En OpenAI-tunnel kan bara servas av **en** tunnel-client åt gången. Jobb- och hemdatorn delade samma tunnel (`tunnel_6a30000575…`, "Home Agent") på **samma konto** → anrop routades ibland till fel maskin (växlande `502` / `connection failed`).
**Lösning:** två separata tunnlar, **en per maskin** (samma OpenAI-konto):

| Maskin | Tunnel-ID | Connector i ChatGPT |
|--------|-----------|---------------------|
| Jobbdator | `tunnel_6a30000575ac8191926cb8e029ab4967` ("Home Agent") | egen — orörd, behålls för jobb |
| Hemdator | `tunnel_6a3043a186388191a7bdf21720cab2d2` | egen — skapas för hemma |

Varje maskin kör sin egen tunnel-client mot sin egen tunnel och har en egen connector i ChatGPT (connectorer är konto-globala men pekar var för sig). Kör aldrig två klienter mot **samma** tunnel-ID. Bara hemdatorns profil (`%APPDATA%\tunnel-client\home-agent.yaml`) ändrades; jobbdatorns är orörd.

### 2. MCP-servern måste köra stateless
ChatGPT/tunneln forwardar `tools/call` **utan** `mcp-session-id`. En stateful FastMCP-server svarar då `HTTP 400` ("Missing session ID") → `502` i ChatGPT. Tunnel-loggen visade `session_id=''` på alla fel.
**Lösning:** `stateless_http=True` i `app/mcp/server.py` (på main, med regressionstest). Den Content-Type-middleware som först provades var en återvändsgränd och togs bort.

### 3. CONTROL_PLANE_API_KEY får inte vara platshållaren
Att klistra in `<din nyckel>` ordagrant → `401 Unauthorized` i control-plane-pollen → `502`. Nyckeln ligger i lokal `.env` (gitignorerad) — ladda den därifrån, klistra inte in den manuellt.

### Ofarliga varningar
`doctor` rödmarkerar `oauth_metadata` (404 på `/.well-known/oauth-protected-resource`) och `run` loggar "OAuth discovery failed: invalid character 'N'". Det är **förväntat** för en No-auth-server och blockerar ingenting.

## Google calendar-vägen (klar, 2026-06-16)

The Google calendar provider path is now complete end-to-end:

- **Google OAuth route implemented** — `/auth/google` login + callback (parallel prefix,
  PKCE + CSRF state, scopes `openid email https://www.googleapis.com/auth/calendar.events.readonly`).
- **Google token-store namespace implemented** — Google tokens in `token_store_google.json`,
  isolated from Microsoft's `token_store.json` (local-only, never committed).
- **`GoogleProvider.read_calendar` implemented** — calendar-only, maps Google events
  (timed `dateTime` + all-day `date`) to `CalendarEvent`; `GoogleApiError(ProviderApiError)`.
- **Explicit calendar provider selection implemented** via `HOME_AGENT_CALENDAR_PROVIDER=google`
  (`get_calendar_provider_with_name()` in [`app/tools/deps.py`](deps.py)).
- **Google refresh flow implemented** — calendar provider selection now uses refresh-aware
  token loading (`get_valid_google_tokens()` in [`app/auth/google.py`](google.py)): an expired
  access token with a `refresh_token` is refreshed against the Google token endpoint and the new
  token is saved to `token_store_google.json`. Fails closed (→ `/auth/google/login`) on missing/
  unrefreshable tokens or missing Google config. No new scopes, no Gmail, no write/delete tools.
- **Microsoft remains default** — flag unset/`microsoft` ⇒ behavior byte-identical to before.
- **Google never reaches the mail path** — separate calendar selector; `get_provider_with_name()`
  (mail) unchanged and can never return `GoogleProvider`.
- **No write/delete tools.**
- **No new MCP signatures.**

`GOOGLE_*` config is optional and fully independent of the Microsoft (`AZURE_*`) flow.

## Nästa möjliga spår (ej påbörjade)

The Google calendar path is feature-complete in code (auth + provider + provider selection +
refresh-aware tokens). Nothing below is started; pick one as the next slice:

1. **Live-test** Google OAuth + Google calendar provider end-to-end (real `GOOGLE_*` in local
   `.env`, `HOME_AGENT_CALENDAR_PROVIDER=google`, verify refresh past ~1h).
2. **Status polish** — surface the selected calendar provider / Google auth status safely on
   `/status` (no tokens, no secrets — same discipline as the existing safety summary).
3. **Google provider refinement** — recurring-event expansion (`singleEvents=true`/`orderBy`/
   `timeMin`); current parity with Outlook returns recurring masters (see `google_provider.py`).
4. **Gmail read-only** — separate later slice; needs MIME/base64url body decoding, privacy-sensitive.
5. **Future write-tool design** — behind the safety gate + explicit `confirm`, much later.

`app/safety/`-grunden och status-polish-grunden (version + safety-summary, inget drift-känsligt
testantal i runtime) är **klara** och pushade.

## Senaste verifiering

```text
Kommando: uv lock --check && PYTHONDONTWRITEBYTECODE=1 uv run --no-sync pytest -q
Resultat: lock OK, 172 passed
Graph: read-only via tools + MCP (stdio + HTTP)
Tunnel: per-maskin (home-agent / home-agent-work), MCP :8001 stateless
Datum: 2026-06-16
HEAD: 65d806e (origin/main == HEAD), working tree clean
Batch: 0f3ef5e google-calendar-provider · ab53e31 explicit google calendar selection · 27f1a0a handoff · 65d806e google refresh flow
```
