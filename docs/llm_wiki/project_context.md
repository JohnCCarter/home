# Projektkontext

## Mål

Bygga en **personlig kalender- och mail-agent** som kan:

- Läsa kalender och e-post via **Microsoft Graph (Outlook)** i första fasen
- Senare stödja **Google Calendar / Gmail**
- Exponeras mot flera klienter genom samma backend

## Klienter (nu och senare)

Samma backend ska kunna användas av:

| Klient | Status |
|--------|--------|
| FastAPI REST (`/calendar`, `/mail`) | Implementerad (read-only MVP) |
| ChatGPT App / Connector | Planerad |
| MCP-server | Planerad |
| Wake-word-sidecar (röst) | Planerad |

Klienterna pratar med backend; backend anropar **tools** som i sin tur använder **providers** mot Outlook/Google.

## Vad detta repo **inte** är

- **Inte** Fibonacci
- **Inte** Genesis-Core-V2
- Ingen trading-logik, promotion gates eller research-governance

Om du ser namn som `genesis-core-home-agent` i kod (t.ex. FastAPI-titel) — behandla det som legacy-namngivning, inte som koppling till Genesis-projektet.

## MVP-scope

**Nu:**

- Microsoft OAuth (PKCE) med read-only scopes
- `MockProvider` när ingen token finns
- `OutlookProvider` för kalender och inkorg (read)

**Senare:**

- Tool-lager med strukturerad JSON
- Bekräftelse före skriv-actions
- Google-provider
- Röst/wake-word-integration

## Teknikstack

- Python 3
- FastAPI + uvicorn
- httpx mot Microsoft Graph
- pytest för tester
