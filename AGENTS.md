# AGENTS.md

Regler för AI-agenter i **Home Agent**-repot.

> **Detta är inte Fibonacci. Detta är inte Genesis-Core-V2.**  
> Använd inte trading-regler, promotion gates eller research-governance från andra projekt.

## Start här

Läs **[docs/llm_wiki/index.md](docs/llm_wiki/index.md)** innan du ändrar kod.

Viktiga sidor:

- [safety_rules.md](docs/llm_wiki/safety_rules.md)
- [auth_and_secrets.md](docs/llm_wiki/auth_and_secrets.md)
- [handoff.md](docs/llm_wiki/handoff.md)

## Korta regler

1. **Kod vinner** — vid tvivel, läs `app/` och `tests/` ([source_authority.md](docs/llm_wiki/source_authority.md))
2. **Små ändringar** — ett problem i taget; kör `PYTHONPATH=. pytest -q`
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
| Tools (planerat) | `app/tools/` |
| Safety (planerat) | `app/safety/` |
| Tester | `tests/` |
| Routing | `app/main.py` (håll tunn) |

## Test och körning

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
uvicorn app.main:app --reload --port 8000
```

Se [README.md](README.md) och [docs/llm_wiki/testing.md](docs/llm_wiki/testing.md).
