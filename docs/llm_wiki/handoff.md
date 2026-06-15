# Handoff

Senast uppdaterad: 2026-06-15 (token refresh implementerad)

## Aktuell status

**Read-only MVP fungerar end-to-end** mot riktig Microsoft Graph med personligt Microsoft-konto. **Token refresh** sker automatiskt vid utgången access token.

## Klart

- [x] FastAPI-app (`app/main.py`) med `GET /calendar`, `GET /mail`
- [x] Microsoft OAuth: login, callback, PKCE, state-validering
- [x] OAuth login/callback fungerar (HTML-svar vid success/fel)
- [x] Token-lagring i `token_store.json` (gitignored) med expiry-check
- [x] **Token refresh** via `refresh_token` (`get_valid_tokens()`)
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
- [x] Tester för auth, config, outlook, token refresh (25 tester)
- [x] LLM Wiki + `AGENTS.md` + `README.md`
- [x] `.env` och `token_store.json` i `.gitignore`

## Write-actions

Fortfarande **avstängda** i MVP:

- `create_event`, `send_email`, `mark_as_read` → `NotImplementedError`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite` i kod eller refresh
- Inga delete-actions

## Nästa steg

1. **`read_email`** — enskilt meddelande från Graph
2. **`app/tools/`** — enhetligt JSON-kontrakt
3. **`app/safety/`** — bekräftelse för write-actions (senare)
4. ChatGPT / MCP — exponera tools mot samma backend
5. Google provider — parallellt interface till `base.py`
6. Wake-word-sidecar — senare

## Kända risker

| Risk | Åtgärd |
|------|--------|
| Refresh token kan revoke:as | 401 + ny login via `/auth/microsoft/login` |
| In-memory OAuth state (`_pending_states`) | Försvinner vid omstart; OK för lokal dev |
| Inget safety-lager än | Håll write disabled; expandera inte scopes |
| Personligt konto kräver `common` + MSA manifest | Dokumenterat i `.env.example` |
| FastAPI-titel `genesis-core-home-agent` | Legacy-namn; byt vid tillfälle |

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: 25 passed
Graph E2E: GET /calendar 200, GET /mail 200 (riktig Graph-data)
Token refresh: automatisk vid expired access_token
Datum: 2026-06-15
```

Uppdatera denna sektion efter varje större ändring eller testkörning.
