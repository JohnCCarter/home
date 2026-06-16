# Säkerhetsregler

Enkla regler för agent och runtime — ingen tung governance.

## Action-typer

| Typ | Exempel | Regel |
|-----|---------|--------|
| **Läs** | `read_calendar`, `read_recent_emails`, `read_email` | Får köras direkt |
| **Skriv** | `create_calendar_event`, `draft_email`, `send_email` | Kräver **explicit användarbekräftelse** innan körning |
| **Delete** | Radera mail, avboka möten | **Förbjudet i MVP** |

## Microsoft Graph-scopes

| Scope | MVP |
|-------|-----|
| `Mail.Read`, `Calendars.Read`, `User.Read` | Tillåtet |
| `Mail.Send` | **Inte** förrän read-only fungerar + safety-lager |
| `Calendars.ReadWrite` | **Inte** förrän read-only fungerar + safety-lager |

Ändra inte scopes i `app/auth/microsoft.py` utan att uppdatera [decision_log.md](decision_log.md) och safety-plan.

## Implementation idag

- `app/safety/policy.py` — central grind: `classify(action)` + `evaluate(action, confirmed)`. Read tillåts, write kräver `confirmed=True`, delete och okänd action nekas. Felkod `confirmation_required` (HTTP 428).
- `app/providers/base.py` — skriv-metoder (`create_event`, `send_email`, `mark_as_read`) kastar `NotImplementedError("disabled in MVP phase")`
- Inga delete-endpoints eller -metoder
- Inga write-tools registrerade ännu — grinden finns, men providers förblir disabled tills write byggs medvetet

## Agentbeteende

1. **Osäkerhet → stoppa** — fråga användaren eller rapportera i handoff; gissa inte
2. **Ingen autonom skickning** — skicka aldrig mail eller skapa möten utan bekräftelse
3. **Ingen delete** — implementera inte delete i MVP även om användaren ber om det utan explicit beslut
4. **Minimera data** — returnera bara fält som behövs; exponera inte tokens i API-svar
5. **Mock som fallback** — utan auth ska `MockProvider` användas, inte felaktiga riktiga anrop

## Safety-lager (`app/safety/`) — byggt 2026-06-16

Grinden finns och gör:

- Klassificerar varje action som read/write/delete (`classify`)
- Blockerar write utan bekräftelseflagga och nekar okänd action (`evaluate`)
- Centraliserar policyn i `app/safety/policy.py` (inte spridd i varje endpoint)

**Bekräftelse är in-band** (`confirm`-argument på själva anropet) — MCP-servern kör `stateless_http=True` och har ingen session att hålla pending-bekräftelse i. Återinför inte sessionsbaserad tvåstegs-bekräftelse; det bryter ChatGPT-tunneln.

Write förblir disabled i providers och inga bredare OAuth-scopes aktiveras förrän write-tools byggs medvetet och konsumerar grinden.
