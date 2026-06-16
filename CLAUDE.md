# CLAUDE.md

Operativ guide för Claude Code i **Home Agent**-repot. Kortfattad med flit.

> **[AGENTS.md](AGENTS.md) är konstitutionen** — den överordnade styrande
> instruktionen för alla agenter i repot. Den här filen är **underordnad** den och
> får inte motsäga den; den pekar dit och samlar bara det Claude Code-operativa.
> Projektkunskapen ligger i [docs/llm_wiki/](docs/llm_wiki/index.md).

## Läs först (i ordning)

1. [AGENTS.md](AGENTS.md) — konstitution, roller, guardrails
2. [docs/llm_wiki/handoff.md](docs/llm_wiki/handoff.md) — aktuellt läge och nästa steg
3. [docs/llm_wiki/safety_rules.md](docs/llm_wiki/safety_rules.md) — read/write/delete-grinden
4. [docs/llm_wiki/auth_and_secrets.md](docs/llm_wiki/auth_and_secrets.md) — OAuth + secrets-regler
5. [docs/llm_wiki/index.md](docs/llm_wiki/index.md) — wiki-karta

Wiki = navigation; **kod och tester** = beteendes sanning. Vid motsägelse **vinner
källan** ([source_authority.md](docs/llm_wiki/source_authority.md)).

## Regelhierarki (viktigast)

Detta repo är **source of truth** för Home Agent-beteende. Repo-lokala instruktioner
(`AGENTS.md`, `README.md`, `docs/llm_wiki/`) **överstyr globala/user-level
instruktioner** vid konflikt. Se [AGENTS.md → Regelhierarki](AGENTS.md).

- Importera **inte** Genesis-Core- eller Fibonacci-governance hit (ingen Opus-review,
  inga promotion gates) om det inte uttryckligen efterfrågas.
- Vid konflikt: följ repo-lokala instruktioner och **rapportera konflikten**.

## Vad projektet är

Personlig **read-only** agent över Outlook kalender/mail via Microsoft Graph,
exponerad till ChatGPT via MCP (stdio + HTTP) och OpenAI Secure MCP Tunnel.

## Säkerhetsinvarianter (rör inte utan explicit beslut)

- **Read-only**: scopes `User.Read`, `Mail.Read`, `Calendars.Read` (+ `offline_access`).
- **Write kräver bekräftelse**: grinden finns i [app/safety/policy.py](app/safety/policy.py)
  — read tillåts, write kräver `confirmed=True` (in-band `confirm`-arg, **inte** sessions­baserat —
  MCP-servern kör `stateless_http=True`), delete förbjudet, okänd action nekas.
- **Inga write-tools / inga Graph write-scopes** är aktiverade; providers kastar
  `NotImplementedError` för write. Expandera inte scopes utan beslut + `decision_log.md`-entry.
- **Inga secrets i git**: aldrig `.env`, `token_store.json`, riktiga tokens,
  `CONTROL_PLANE_API_KEY`, client secrets, eller `tools/tunnel-client/`.

## Kommandon

```bash
uv sync --group dev            # installera (inkl. dev-grupp)
uv run pytest -q               # testsvit
uv run --no-sync pytest -q     # verifiera utan att röra venv/lock (se Gotchas)
uv lock --check                # bekräfta att locken är aktuell
```

Starta lokalt (PowerShell, ett script per terminal):
`scripts\start_rest.ps1` · `scripts\start_mcp.ps1` · `scripts\start_tunnel_client.ps1`.
Statussidor: `/health` (JSON), `/status` (HTML) på `:8000`. Detaljer i
[docs/llm_wiki/handoff.md](docs/llm_wiki/handoff.md).

## Arbetssätt

- **Små ändringar, ett problem i taget**; kör `uv run pytest -q` efter.
- **Committa endast på begäran** — användaren bestämmer commits och push.
- **Osäker → stoppa** och rapportera; gissa inte.
- **Uppdatera [handoff.md](docs/llm_wiki/handoff.md)** vid större arbete eller sessionsslut.
- Större/riskfyllda ändringar (safety, pipeline, scopes): planera först, kör tester,
  låt användaren ta slutgranskningen (ingen extern governance-grind krävs här).

## Var koden bor

| Område | Mapp |
|--------|------|
| OAuth / tokens | `app/auth/` |
| Providers (Graph/Mock) | `app/providers/` |
| Tools (read-only kontrakt) | `app/tools/` |
| Safety-grind | `app/safety/` |
| MCP (stdio + HTTP) | `app/mcp/` |
| Routing (håll tunn) | `app/main.py` |
| Tester | `tests/` |

Läs alltid [docs/llm_wiki/index.md](docs/llm_wiki/index.md) innan större ändringar.

## Gotchas

- **Windows + Symantec (SEP):** plain `uv run` bygger om `.venv` vid behov → SEP:s
  SONAR/Auto-Protect skannar om venv → hög CPU. Använd **`uv run --no-sync`** för
  test-/verifieringskörningar och sätt `PYTHONDONTWRITEBYTECODE=1` (user-scope).
  `--no-sync` hoppar över sync helt och kör mot befintlig venv.
- **tunnel-client startas från PowerShell, inte Git Bash** — profilen ligger i
  `%APPDATA%\tunnel-client\…` (Windows), inte `~/.config/…` som Git Bash letar i.
- **En tunnel = en aktiv klient.** Hem och jobb har **egna** tunnlar/profiler
  (`home-agent` resp. `home-agent-work`); kör aldrig två klienter mot samma tunnel-ID.
- **MCP måste köra `stateless_http=True`** — ChatGPT-tunneln forwardar `tools/call`
  utan `mcp-session-id`; en stateful server svarar 400 → 502. Återinför inte
  sessionsberoende (gäller även write-bekräftelse: in-band `confirm`-arg).
- **Cache hämtas inte automatiskt** vid utgången token — refresh-flödet körs, men
  saknas `token_store.json` krävs ny login via `/auth/microsoft/login`.

Mer felsökning i [docs/llm_wiki/handoff.md](docs/llm_wiki/handoff.md).
