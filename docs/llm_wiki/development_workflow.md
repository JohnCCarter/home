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

**Source of truth:** `pyproject.toml` + `uv.lock`. `requirements.txt` är legacy-fallback.

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

## Commits och PR

- Committa **endast** när användaren ber om det
- Inkludera aldrig `.env`, `token_store.json` eller riktiga credentials
- Uppdatera [handoff.md](handoff.md) vid större milstolpar
- Lägg beslut i [decision_log.md](decision_log.md) vid arkitekturval

## Vad vi inte gör

- Ingen Fib/Genesis-process
- Ingen obligatorisk design-doc före varje ändring
- Ingen automatisk deploy eller scope-expansion utan explicit beslut
