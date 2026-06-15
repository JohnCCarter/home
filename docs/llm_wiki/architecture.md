# Arkitektur

## Huvudflöde

```text
ChatGPT / App / Voice / MCP
        │
        ▼
   Backend (FastAPI)
        │
        ▼
      Tools              ← app/tools/ (read-only JSON-kontrakt)
        │
        ▼
    Providers            ← Outlook, Mock, (senare Google)
        │
        ▼
 Outlook / Google APIs
```

**Idag:** REST-endpoints anropar `app/tools/` som delegerar till providers.

## Repo-layout

```text
home/
├── app/
│   ├── main.py              # FastAPI routing (tunn)
│   ├── config.py
│   ├── auth/
│   │   ├── microsoft.py
│   │   └── token_store.py
│   ├── tools/               # Read-only tool-lager
│   │   ├── contracts.py     # ToolResult, error codes
│   │   ├── deps.py          # Provider-val (mock/outlook)
│   │   ├── serialization.py
│   │   ├── calendar_tools.py
│   │   └── email_tools.py
│   └── providers/
│       ├── base.py
│       ├── mock_provider.py
│       └── outlook_provider.py
├── tests/
├── docs/llm_wiki/
└── ...
```

### Planerad mapp

| Mapp | Syfte |
|------|--------|
| `app/safety/` | Bekräftelse för write-actions (senare) |

## Komponenter

### `app/tools/`

- Enhetligt `ToolResult`-kontrakt
- `read_calendar`, `read_recent_emails`, `read_email`
- Mappar `GraphApiError` → `auth_required`, `permission_denied`, etc.
- Använder `get_valid_tokens()` via `deps.get_provider_with_name()`

### `app/main.py`

- `GET /calendar` → `read_calendar()` → returnerar `data`
- `GET /mail` → `read_recent_emails()`
- `GET /mail/{message_id}` → `read_email()`
- HTML-svar för browser; JSON för API-klienter

### `app/auth/`

- OAuth PKCE, token storage, refresh

### `app/providers/`

- Graph/mock implementation; inga secrets

## Provider-val

```text
get_valid_tokens()
    │
    ├─ giltig access_token → OutlookProvider ("outlook")
    ├─ refresh failed / expired file → auth_required
    └─ ingen token → MockProvider ("mock")
```

## Externa API:er

| Provider | Bas-URL |
|----------|---------|
| Microsoft Graph | `https://graph.microsoft.com/v1.0` |
| Google (planerad) | TBD |
