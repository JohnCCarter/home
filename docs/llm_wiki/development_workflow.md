# Utvecklingsworkflow

Lätt process — ingen promotion gates, ingen trading-governance.

## Standardcykel

```text
1. Liten ändring (ett problem i taget)
2. Kör tester
3. Kontrollera secrets (ingen .env/token i diff)
4. Rapportera ändrade filer till användaren
```

## Innan du kodar

1. Läs [safety_rules.md](safety_rules.md) om du rör mail/kalender/auth
2. Kolla [handoff.md](handoff.md) för pågående arbete
3. Håll scope minimalt — matcha befintlig stil i `app/`

## Pakethantering (uv)

**Source of truth:** `pyproject.toml` + `uv.lock`. Använd `uv sync --group dev` — inte `requirements.txt`.

```bash
uv sync --group dev
```

## Under utveckling

- **Providers** — affärslogik mot Graph/Google
- **Auth** — endast OAuth/token; ingen provider-logik här
- **Tools** (när de finns) — JSON-kontrakt, delegerar till providers
- **main.py** — tunn routing tills tool-lager tar över

## Efter ändring

```bash
# Från repo-roten
uv run pytest -q
```

Valfritt lokalt:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Kräver `.env` med Azure-värden för auth; `/calendar` och `/mail` fungerar med mock utan inloggning.

## Starta runtime (PowerShell scripts)

Tre terminaler — ett script var:

```powershell
.\scripts\start_rest.ps1            # REST/OAuth :8000
.\scripts\start_mcp.ps1             # MCP HTTP :8001 (MCP_DEV_OPENAI_TUNNEL=1)
.\scripts\start_tunnel_client.ps1   # tunnel-client (läser nyckeln ur .env, skriver aldrig ut den)
```

Tunnel-profil (en per dator) styrs av `-Profile` (default `home-agent`): jobbdatorn kör `.\scripts\start_tunnel_client.ps1 -Profile home-agent-work` (eller `$env:TUNNEL_PROFILE="home-agent-work"`). Samma repo/`.env`/nyckel/Azure-config på båda — endast tunnel-profil/tunnel-ID skiljer.

Liveness/status: `http://127.0.0.1:8000/health` (JSON), `http://127.0.0.1:8000/status` (HTML). Scripten skapar aldrig `.env` och committar inget.

`/status` and `/health` expose safe local runtime metadata only. They do not probe Microsoft Graph, mailbox/calendar data, MCP liveness, tunnel-client liveness, or external services. Version is best-effort: `HOME_AGENT_VERSION` → `GIT_COMMIT` → `git rev-parse --short HEAD` → `unknown`.

Vill du sanity-checka en färsk clone, jämför resultatet mot senaste [handoff.md](handoff.md):

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
uv run --no-sync pytest -q
```

## Commits och PR

- Committa **endast** när användaren ber om det
- Inkludera aldrig `.env`, `token_store.json` eller riktiga credentials
- Uppdatera [handoff.md](handoff.md) vid större milstolpar
- Lägg beslut i [decision_log.md](decision_log.md) vid arkitekturval

## Vad vi inte gör

- Ingen Fib/Genesis-process
- Ingen obligatorisk design-doc före varje ändring
- Ingen automatisk deploy eller scope-expansion utan explicit beslut
