# Arkitektur

## Huvudflöde

```text
ChatGPT / App / Voice / MCP
        │
        ▼
   Backend (FastAPI)
        │
        ▼
      Tools          ← planerat lager (strukturerad JSON)
        │
        ▼
    Providers        ← Outlook, Mock, (senare Google)
        │
        ▼
 Outlook / Google APIs
```

**Idag:** Klienten kan anropa REST-endpoints direkt; provider-logik ligger i `app/main.py` utan separat tool-modul.

**Mål:** Alla capabilities går via tools med enhetliga kontrakt (se [tool_contracts.md](tool_contracts.md)).

## Repo-layout

```text
home/
├── app/
│   ├── main.py              # FastAPI-app, routing, provider-val
│   ├── config.py            # Miljövariabler (.env)
│   ├── auth/                # Microsoft OAuth, token-lagring
│   │   ├── microsoft.py
│   │   └── token_store.py
│   └── providers/           # Kalender/mail-abstraktion
│       ├── base.py          # ABC + dataclass-modeller
│       ├── mock_provider.py
│       └── outlook_provider.py
├── tests/                   # pytest (mockar Graph, ingen riktig OAuth)
├── docs/llm_wiki/           # Denna wiki
├── .env.example             # Mall — inte riktiga värden
├── requirements.txt
├── AGENTS.md
└── README.md
```

### Planerade mappar (ännu inte skapade)

| Mapp | Syfte |
|------|--------|
| `app/tools/` | Tool-implementeringar: validering, JSON-svar, koppling till providers |
| `app/safety/` | Bekräftelseflöde, policy för read vs write, blockering av delete |

Placera ny kod där den hör hemma — inte i `main.py` när tool- eller safety-lagret finns.

## Komponenter idag

### `app/auth/`

- `/auth/microsoft/login` — startar OAuth med PKCE
- `/auth/microsoft/callback` — byter code mot tokens, sparar lokalt
- Scopes: `offline_access User.Read Mail.Read Calendars.Read` (read-only)

### `app/providers/`

- **`base.py`** — `CalendarProvider`, `EmailProvider`, dataclasses; skriv-metoder kastar `NotImplementedError` i MVP
- **`mock_provider.py`** — fasta testdata utan nätverk
- **`outlook_provider.py`** — Microsoft Graph `/me/events`, `/me/mailFolders/inbox/messages`

### `app/main.py`

- Väljer provider: `OutlookProvider` om giltig token finns, annars `MockProvider`
- `GET /calendar` — serialiserar `CalendarEvent`
- `GET /mail` — serialiserar `EmailMessage`

### `tests/`

- Auth-flöde, config, Outlook-provider med `httpx.MockTransport`
- Inga riktiga Microsoft-credentials krävs

## Provider-val

```text
load_tokens()
    │
    ├─ giltig access_token → OutlookProvider
    ├─ utgången token (fil finns) → HTTP 401
    └─ ingen token → MockProvider
```

## Externa API:er

| Provider | Bas-URL |
|----------|---------|
| Microsoft Graph | `https://graph.microsoft.com/v1.0` |
| Google (planerad) | TBD |
