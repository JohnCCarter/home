# Handoff

Senast uppdaterad: 2026-06-15 (Microsoft Graph read-only E2E verifierat)

## Aktuell status

**Read-only MVP fungerar end-to-end** mot riktig Microsoft Graph med personligt Microsoft-konto.

## Klart

- [x] FastAPI-app (`app/main.py`) med `GET /calendar`, `GET /mail`
- [x] Microsoft OAuth: login, callback, PKCE, state-validering
- [x] OAuth login/callback fungerar (HTML-svar vid success/fel)
- [x] Token-lagring i `token_store.json` (gitignored) med expiry-check
- [x] `MockProvider` — fallback utan inloggning
- [x] `OutlookProvider` — read calendar + inbox via Graph
- [x] **Microsoft Graph read-only fungerar end-to-end**
- [x] `GET /calendar` returnerar riktiga Graph-händelser
- [x] `GET /mail` returnerar riktiga Graph-mail
- [x] Personligt Microsoft-konto: `AZURE_TENANT_ID=common` + Entra `signInAudience` för MSA
- [x] Token v2 (`accessTokenAcceptedVersion: 2` i Entra manifest)
- [x] `oauth_authority_base` i `app/config.py`
- [x] Graph-fel hanteras utan 500-vit skärm (HTML i browser)
- [x] Skriv-actions disabled i `base.py` / provider
- [x] Read-only OAuth scopes (`Mail.Read`, `Calendars.Read`)
- [x] Tester för auth, config, outlook (18 tester)
- [x] LLM Wiki + `AGENTS.md` + `README.md`
- [x] `.env` och `token_store.json` i `.gitignore`

## Write-actions

Fortfarande **avstängda** i MVP:

- `create_event`, `send_email`, `mark_as_read` → `NotImplementedError`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite` i kod
- Inga delete-actions

## Nästa steg

1. **Token refresh** — slippa ny login vid expiry
2. **`read_email`** — enskilt meddelande från Graph
3. **`app/tools/`** — enhetligt JSON-kontrakt
4. **`app/safety/`** — bekräftelse för write-actions (senare)
5. ChatGPT / MCP — exponera tools mot samma backend
6. Google provider — parallellt interface till `base.py`
7. Wake-word-sidecar — senare

## Kända risker

| Risk | Åtgärd |
|------|--------|
| Token refresh inte implementerad | Användare måste logga in igen vid expiry |
| In-memory OAuth state (`_pending_states`) | Försvinner vid omstart; OK för lokal dev |
| Inget safety-lager än | Håll write disabled; expandera inte scopes |
| Personligt konto kräver `common` + MSA manifest | Dokumenterat i `.env.example` |
| FastAPI-titel `genesis-core-home-agent` | Legacy-namn; byt vid tillfälle |

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: 18 passed
Graph E2E: GET /calendar 200, GET /mail 200 (riktig Graph-data)
Datum: 2026-06-15
```

Uppdatera denna sektion efter varje större ändring eller testkörning.
