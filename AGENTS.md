# AGENTS.md — konstitution för Home Agent-agenterna

Den här filen är den **överordnade styrande instruktionen** (konstitutionen) för alla
AI-agenter — Claude Code, Codex och andra — som arbetar i **Home Agent**-repot. Alla
andra agentkonfigurar (`CLAUDE.md`, `.github/`, IDE-/verktygsspecifika filer) är
**underordnade** denna fil och får inte motsäga den. Vid konflikt gäller AGENTS.md.

> **Detta är inte Fibonacci. Detta är inte Genesis-Core-V2.**  
> Använd inte trading-regler, promotion gates eller research-governance från andra projekt.

## Regelhierarki

Prioritetsordning vid konflikt (högst först):

1. **AGENTS.md (denna konstitution)** — styr governance, safety, scopes, commits, tester. Source of truth för Home Agent-beteende.
2. **Källkod (`app/`, `tests/`)** — source of truth för hur saker *faktiskt* fungerar. Konstitutionen styr *reglerna*, koden avgör *fakta* ([source_authority.md](docs/llm_wiki/source_authority.md)).
3. **Övriga repo-docs** (`README.md`, `docs/llm_wiki/`) — projektkunskap, underordnade konstitutionen.
4. **Andra agentkonfigurar** (`CLAUDE.md` m.fl.) — får förtydliga och peka hit, aldrig motsäga.
5. **Globala/user-level instruktioner** — viker för repot vid konflikt.

Tillämpning:

- **Importera inte Genesis-Core- eller Fibonacci-governance/workflows** om det inte uttryckligen efterfrågas — ingen Opus-review, promotion gates eller andra projekts grindar gäller här.
- **Vid konflikt** mellan globala instruktioner och repot (denna fil / `README.md` / docs / aktuell task-scope): **följ repo-lokala instruktioner och rapportera konflikten** till användaren.
- **Generella globala hygienregler gäller** när de inte krockar — inga secrets i git, komprimerade svar, plan mode för multi-fil-ändringar.
- **Personliga globala konventioner behålls** (t.ex. `Mode:`-svarsbanner) — de krockar inte med repo-governance.

## Start här

Läs **[docs/llm_wiki/index.md](docs/llm_wiki/index.md)** innan du ändrar kod.

Viktiga sidor:

- [safety_rules.md](docs/llm_wiki/safety_rules.md)
- [auth_and_secrets.md](docs/llm_wiki/auth_and_secrets.md)
- [handoff.md](docs/llm_wiki/handoff.md)

## Korta regler

1. **Kod vinner** — vid tvivel, läs `app/` och `tests/` ([source_authority.md](docs/llm_wiki/source_authority.md))
2. **Små ändringar** — ett problem i taget; kör `uv run pytest -q`
3. **Inga secrets i git** — aldrig committa `.env`, `token_store.json` eller riktiga tokens
4. **Läs får köras** — kalender/mail-read är OK
5. **Skriv kräver bekräftelse** — implementera inte autonom send/create utan safety-lager
6. **Ingen delete i MVP**
7. **Expandera inte OAuth-scopes** (`Mail.Send`, `Calendars.ReadWrite`) utan explicit beslut
8. **Osäker → stoppa** — rapportera istället för att gissa
9. **Committa endast på begäran** — användaren bestämmer commits
10. **Uppdatera handoff** vid större arbete eller sessionsslut

## Var kod hör hemma

| Område | Mapp |
|--------|------|
| OAuth / tokens | `app/auth/` |
| Graph/Google | `app/providers/` |
| Tools (read-only kontrakt) | `app/tools/` |
| Safety-grind | `app/safety/` |
| MCP (stdio + HTTP) | `app/mcp/` |
| Tester | `tests/` |
| Routing | `app/main.py` (håll tunn) |

## Test och körning

```bash
uv sync --group dev
uv run pytest -q
uv run uvicorn app.main:app --reload --port 8000
```

**Dependencies:** `pyproject.toml` + `uv.lock` — använd `uv sync --group dev`.

Se [README.md](README.md) och [docs/llm_wiki/testing.md](docs/llm_wiki/testing.md).
