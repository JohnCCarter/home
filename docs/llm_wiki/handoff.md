# Handoff

Senast uppdaterad: 2026-06-15 (`read_email` implementerad)

## Aktuell status

**Read-only MVP fungerar end-to-end** mot riktig Microsoft Graph med personligt Microsoft-konto. **Token refresh** sker automatiskt. **`read_email`** läser enskilt meddelande via message id.

## Klart

- [x] FastAPI-app med `GET /calendar`, `GET /mail`, **`GET /mail/{message_id}`**
- [x] Microsoft OAuth: login, callback, PKCE, state-validering
- [x] Token-lagring + **token refresh** (`get_valid_tokens()`)
- [x] `MockProvider` — fallback utan inloggning
- [x] `OutlookProvider` — read calendar, inbox, **enskilt mail**
- [x] **Microsoft Graph read-only fungerar end-to-end**
- [x] `GET /calendar` — riktiga Graph-händelser
- [x] `GET /mail` — riktiga Graph-mail (lista)
- [x] **`GET /mail/{message_id}`** — normaliserat JSON med body
- [x] Personligt Microsoft-konto: `AZURE_TENANT_ID=common` + MSA manifest
- [x] Graph-fel: 401/403/404/429/5xx med tydliga meddelanden (ingen body i loggar)
- [x] Skriv-actions disabled; read-only scopes endast
- [x] Tester (auth, config, outlook, refresh, **read_email**)
- [x] LLM Wiki + `AGENTS.md` + `README.md`

## Write-actions

Fortfarande **avstängda** i MVP:

- `create_event`, `send_email`, `mark_as_read` → `NotImplementedError`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite`
- Inga delete/move/reply/forward/attachments

## Nästa steg

1. **`app/tools/`** — enhetligt JSON-kontrakt
2. **`app/safety/`** — bekräftelse för write-actions (senare)
3. ChatGPT / MCP — exponera tools mot samma backend
4. Google provider — parallellt interface till `base.py`
5. Wake-word-sidecar — senare

## Kända risker

| Risk | Åtgärd |
|------|--------|
| Refresh token kan revoke:as | 401 + ny login |
| Mail body returneras via API men loggas aldrig | Policy i provider/endpoint |
| Graph message ids kan innehålla `/` | Route `{message_id:path}` + URL-encoding |
| Inget safety-lager än | Håll write disabled |

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: 32 passed
Graph: /calendar, /mail, /mail/{id} read-only
Datum: 2026-06-15
```
