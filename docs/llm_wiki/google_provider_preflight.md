# Google provider — preflight / design

Status: **design only, ej implementerat** (2026-06-16). Inga Google-deps, inga scopes,
ingen OAuth, inga `.env`-krav tillagda. Frågan: *kan en Google read-only-provider läggas
till parallellt med Outlook utan att störa MCP, safety eller tunneln?* — **Ja**, med tre
små förberedande ändringar (error-typ, provider-val, token-store-namespace).

## 1. Nuvarande provider-kontrakt

[`app/providers/base.py`](base.py är källan) — två abstrakta interfaces, provider-agnostiska:

- `CalendarProvider.read_calendar() -> List[CalendarEvent]`
- `EmailProvider.read_recent_emails() -> List[EmailMessage]`, `read_email(id) -> EmailDetail`
- Dataklasser: `CalendarEvent`, `EmailMessage`, `EmailDetail`, `EmailBody` (frozen, provider-neutrala)
- Write-metoder (`create_event`, `send_email`, `mark_as_read`) kastar `NotImplementedError`

`OutlookProvider` och `MockProvider` implementerar båda interfaces. **Data-interfacet räcker
för Google oförändrat** — Google mappar sina API-svar till samma dataklasser.

## 2. Passar Google parallellt? — Ja

`GoogleProvider(CalendarProvider, EmailProvider)` kan implementera exakt samma metoder med
**rå `httpx`** (precis som Outlook), så **ingen ny dependency** krävs. Tool-, MCP- och
safety-lagren rör inte providern direkt — de går via `get_provider_with_name()`.

## 3. Behöver kontraktet ändras? — Data nej, error ja (litet)

Friktionen är **inte** data-interfacet utan **error-typen**. Tools-lagret mappar
`GraphApiError` (definierad i [`outlook_provider.py`](outlook_provider.py)) i
`map_graph_error` / `map_read_email_graph_error`. En Google-provider kastar sina egna fel.

Minsta åtgärd (del av Google-slicen, inte nu):

- **(rek.)** inför provider-neutral `ProviderApiError(status_code, message)` som `GraphApiError`
  ärver; tools mappar bas-typen. Inga tool-signaturer ändras.
- alternativ (fult): låt `GoogleProvider` kasta `GraphApiError` — fungerar men missvisande namn.

## 4. Token-store per provider? — Ja (**implementerat 2026-06-16**)

Token store is namespaced by provider. Microsoft/default continues to use
`token_store.json`. Future Google auth will use `token_store_google.json`. Token files
remain local-only and must never be committed.

`token_store.py` har nu `token_store_path(provider)` + `provider`-argument (default
`microsoft`) på `save_tokens`/`load_tokens`/`load_stored_tokens`/`clear_tokens`/
`has_stored_tokens`. Okänd provider → `ValueError` (fail closed). Microsoft-pathen är
exakt som före refaktorn; isolering verifierad av `tests/test_token_store_namespace.py`.

## 5. `.env`-utökning senare? — Ja, senare

[`config.py`](config.py) har `REQUIRED_ENV_VARS` = alla `AZURE_*`. Google behöver senare
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`. **Viktigt:** gör
variabel-grupperna oberoende — kräv inte både Azure och Google; saknad Google-config ska
bara inaktivera Google, inte krascha Microsoft-flödet. Inget nu.

## 6. Read-only scopes (**VERIFIED 2026-06-16** mot officiell Google-doc)

**Calendar-only scope** (mest snävt fokuserade för events-läsning):

- `https://www.googleapis.com/auth/calendar.events.readonly` — *"View events on all your calendars"*

**Identity scopes** (OAuth-login, minimal):

- `openid email`  (`profile` valfri, bara om namn/bild behövs)

**Föreslagen scope-sträng för calendar-only-slicen:**

```
openid email https://www.googleapis.com/auth/calendar.events.readonly
```

**Explicitly excluded** (behövs inte / aldrig):

- `https://www.googleapis.com/auth/calendar` (full read/write/**delete**)
- `https://www.googleapis.com/auth/calendar.events` (read/**write** events)
- Alla Gmail-scopes (`gmail.readonly` = senare slice; `gmail.send`/`gmail.modify`/full = **aldrig**)
- Alla `*.modify`/`*.send`/full-access-scopes

**Sources checked:**

- [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes)
- [Calendar API: Choose auth scopes](https://developers.google.com/workspace/calendar/api/auth)
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)

## 7. Calendar-only, mail-only eller båda först? — **Calendar-only**

Minst yta och risk: Gmail read kräver MIME/base64url-avkodning av body-parts (Graph ger
färdig `body`), och Gmail är känsligare integritetsmässigt. Kalender mappar rakt till
`CalendarEvent`. Börja calendar-only; lägg Gmail i en separat senare slice.

## 8. MCP-påverkan — ingen (modell A)

| Modell | Beskrivning | MCP-signaturer |
|--------|-------------|----------------|
| **A (rek.)** | Samma tools; provider väljs i `deps.py` (vilket konto är authat/konfigurerat) | **oförändrade** |
| B | Nya tools, t.ex. `read_google_calendar` | nya signaturer (mer yta) |
| C | Provider-param i befintliga tools | signaturändring |

**Rekommendation: A** — noll MCP/tool-signaturändring. Första slicen: Google som
*alternativ valbar* provider, inte simultan aggregering av två kalendrar (aggregering = större
design, defer).

## 9. `app/tools`-påverkan — minimal

Tools anropar redan `get_provider_with_name()` och är providerneutrala så när som på
`GraphApiError`-importen (se §3). Med `ProviderApiError`-basen blir tools helt providerneutrala.

## 10. Safety-påverkan — ingen

[`policy.py`](safety_rules.md) klassar på **action-namn** (`read_calendar` …), inte provider.
Google read-tools är samma READ-actions → grinden oförändrad. read allowed · write
`confirmation_required` (inga write-tools) · delete forbidden · unknown denied. Oförändrat.

## 11. Tester som skulle behövas

- `GoogleProvider` enhetstester (fejkad `httpx` → `CalendarEvent`-mappning), offline
- `deps.get_provider_with_name` väljer Google vid Google-token
- error-mappning: Google-API-fel → `ToolError` (via `ProviderApiError`)
- token-store-namespace: Google- och Microsoft-token blandas inte
- secret-negativa tester (inga nycklar i kod/loggar)

## 12. Risker

- **Error-typ-koppling** (`GraphApiError`) — generalisera till `ProviderApiError`.
- **Token-store enfilsblandning** — namespacea.
- **`config.py` required-vars** — Azure är required nu; tvinga inte fram både.
- **Provider-val tvetydigt** om både authade — definiera default/val i första slicen.
- **Gmail-integritet/scope-känslighet** — därför calendar-first.
- **Egress** krävs för Google OAuth + API (samma som Graph).
- Ingen ny dependency *om* vi håller oss till rå `httpx`.

## 13. Rekommenderad första implementation-slice

**Google Calendar read-only, modell A**, i denna ordning:

1. ~~`ProviderApiError`-bas + låt `GraphApiError` ärva~~ — **klart** (38d513f).
2. ~~Token-store-namespace (Google-fil separat)~~ — **klart** (2026-06-16).
3. ~~scope-verifiering~~ — **klart** (2026-06-16, §6 VERIFIED). Nästa slice: `/auth/google`-router (parallell prefix) med `openid email https://www.googleapis.com/auth/calendar.events.readonly`.
4. `GoogleProvider.read_calendar()` via `httpx`.
5. `deps.py`: välj Google när Google-token finns (default/precedens definierad).
6. Tester per §11.

Gmail-read och dual-provider-aggregering = separata senare slices.
