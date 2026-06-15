# Handoff

Senast uppdaterad: 2026-06-15 (LLM Wiki skapad)

## Aktuell status

Tidigt **read-only MVP**: FastAPI-backend med Microsoft OAuth (PKCE), mock- och Outlook-providers, pytest-svit.

## Klart

- [x] FastAPI-app (`app/main.py`) med `GET /calendar`, `GET /mail`
- [x] Microsoft OAuth: login, callback, PKCE, state-validering
- [x] Token-lagring i `token_store.json` (gitignored) med expiry-check
- [x] `MockProvider` — fallback utan inloggning
- [x] `OutlookProvider` — read calendar + inbox via Graph
- [x] Skriv-actions disabled i `base.py` / provider
- [x] Read-only OAuth scopes (`Mail.Read`, `Calendars.Read`)
- [x] Tester för auth, config, outlook (17 tester; 16+ passerar med lokal `.env`)
- [x] LLM Wiki + `AGENTS.md` + `README.md`
- [x] `.env` och `token_store.json` i `.gitignore`

## Nästa steg (förslag)

1. **`app/tools/`** — implementera tool-kontrakt med enhetlig JSON
2. **`app/safety/`** — bekräftelse för write-actions
3. **`read_email`** — enskilt meddelande från Graph
4. **ChatGPT / MCP** — exponera tools mot samma backend
5. **Google provider** — parallellt interface till `base.py`
6. **Wake-word-sidecar** — senare; samma API
7. Rensa legacy-namn `genesis-core-home-agent` i FastAPI-titel om önskat

## Kända risker

| Risk | Åtgärd |
|------|--------|
| Token refresh inte implementerad | Användare måste logga in igen vid expiry |
| In-memory OAuth state (`_pending_states`) | Försvinner vid omstart; OK för lokal dev |
| Inget safety-lager än | Håll write disabled; expandera inte scopes |
| `test_missing_settings_raise_clear_error` känslig för lokal `.env` | Isolera test med chdir/tmp_path |
| FastAPI-titel kan förvirra (Genesis-namn) | Dokumenterat i wiki; byt namn vid tillfälle |

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: 16 passed, 1 failed (test_missing_settings_raise_clear_error — lokal .env i cwd)
Datum: 2026-06-15
```

Uppdatera denna sektion efter varje större ändring eller testkörning.
