# Handoff

Senast uppdaterad: 2026-06-15 (`app/tools/` read-only tool-lager)

## Aktuell status

**Read-only MVP** med Graph E2E, token refresh, `read_email`, och **`app/tools/`** med enhetligt JSON-kontrakt. REST-endpoints delegerar till tools.

## Klart

- [x] FastAPI: `GET /calendar`, `GET /mail`, `GET /mail/{message_id}`
- [x] OAuth + token refresh (`get_valid_tokens()`)
- [x] Providers: Mock + Outlook (read-only Graph)
- [x] **`app/tools/`** — `read_calendar`, `read_recent_emails`, `read_email`
- [x] **`ToolResult`** — `ok`, `tool`, `provider`, `data`, `error` med standard error codes
- [x] Endpoints → tools → providers → Graph/mock
- [x] Skriv-actions disabled; read-only scopes endast
- [x] Tester (inkl. tool-kontrakt)
- [x] LLM Wiki uppdaterad

## Write-actions

Fortfarande **avstängda**:

- Inga write-tools i `app/tools/`
- Inga `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite`
- Inga delete/move/reply/forward

## Nästa steg

1. **MCP / ChatGPT App connector skeleton** — exponera samma tools
2. **`app/safety/`** — bekräftelse för write-actions (senare)
3. Google provider
4. Wake-word-sidecar

## Senaste verifiering

```text
Kommando: PYTHONPATH=. pytest -q
Resultat: 43 passed
Graph: read-only via tools
Datum: 2026-06-15
```
