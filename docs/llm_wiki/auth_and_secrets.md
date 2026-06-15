# Auth och secrets

## Microsoft OAuth

Autentisering sker via **Azure AD / Microsoft Entra** med authorization code + **PKCE**.

| Steg | Endpoint / fil |
|------|----------------|
| Starta inloggning | `GET /auth/microsoft/login` |
| Callback | `GET /auth/microsoft/callback` |
| Token-lagring | `token_store.json` (lokal fil, gitignored) |

### Miljövariabler

Definieras i lokal `.env` (kopiera från `.env.example`):

| Variabel | Syfte |
|----------|--------|
| `AZURE_TENANT_ID` | Azure tenant |
| `AZURE_CLIENT_ID` | App registration client ID |
| `AZURE_CLIENT_SECRET` | Client secret (server-side only) |
| `AZURE_REDIRECT_URI` | Måste matcha app-registrering (t.ex. `http://localhost:8000/auth/microsoft/callback`) |

`app/config.py` laddar `.env` via `python-dotenv` och kräver alla fyra variabler vid auth-anrop.

### Scopes (MVP)

```
offline_access User.Read Mail.Read Calendars.Read
```

**Inte** `Mail.Send` eller `Calendars.ReadWrite` förrän read-only-flödet är stabilt och safety-lager finns.

## Secrets — absoluta regler

| Regel | |
|-------|---|
| Committa aldrig `.env` | Finns i `.gitignore` |
| Committa aldrig `token_store.json` | Finns i `.gitignore` |
| Logga aldrig access/refresh tokens | Test `test_tokens_never_returned_or_logged` verifierar detta |
| Skriv aldrig client secrets i kod, docs, tester eller loggar | Använd env + placeholders i `.env.example` |
| Skapa inte dummy-secrets i repo | Bara placeholders som `your-client-secret` |

## Token-fil

- Sökväg: `token_store.json` (projektrot vid körning)
- Skrivs med filrättigheter `0600` när OS tillåter
- Utgångna tokens behandlas som saknade; användaren måste logga in igen

## För agenter

- Läs **inte** användarens `.env` eller `token_store.json` om du inte explicit behöver felsöka auth — och rapportera aldrig innehållet
- Vid PR/commit: dubbelkolla att inga secrets hamnat i diff
- Om du lägger till nya hemligheter — uppdatera `.env.example` med placeholder och `.gitignore` om ny filtyp

## Verifiering

```bash
git check-ignore -v .env token_store.json   # ska visa gitignore-regler
git diff --staged                            # inga secrets före commit
```
