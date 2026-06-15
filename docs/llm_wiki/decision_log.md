# Beslutlogg

Enkel logg över arkitektur- och scope-beslut. Nyaste överst.

---

## 2026-06-15 — OpenAI UI Tunnel dev-mode för MCP HTTP

**Beslut:** Lägg till `MCP_DEV_OPENAI_TUNNEL=1` / `--openai-tunnel` som explicit dev opt-in; tillåt `https://chatgpt.com` och `https://chat.openai.com` origins endast i det läget.

**Motivering:** ChatGPT OpenAI Tunnel proxar mot lokal MCP; Origin-validering blockerade utan dev-flagga. Host förblir localhost-only om inte `MCP_DEV_ALLOWED_HOSTS` sätts.

**Konsekvens:** Default oförändrat säkert. Nästa steg: manuell ChatGPT developer mode-test.

---

## 2026-06-15 — Dev-only MCP tunnel hosts + read_email not_found

**Beslut:** Lägg till `app/mcp/transport_config.py` med `MCP_DEV_ALLOWED_HOSTS` (explicit opt-in); mappa Graph 400/404 på `read_email` till `not_found`.

**Motivering:** Tunnel-test krävde runtime-inaktivering av DNS rebinding; säkrare att tillåta specifika tunnel-hosts. Graph returnerar 400 för ogiltigt message id — ska inte bli `unknown_error` i MCP.

**Konsekvens:** Default förblir localhost-only med DNS rebinding på. Nästa steg: manuell ChatGPT developer mode-test.

---

## 2026-06-15 — MCP HTTP/streamable transport för ChatGPT-förberedelse

**Beslut:** Lägg till `app/mcp/http_server.py` med FastMCP `streamable-http` transport på `/mcp`; behåll stdio-server oförändrad som separat väg.

**Motivering:** ChatGPT App/Connector kräver HTTP/HTTPS-nåbar MCP-endpoint. Streamable HTTP är SDK:s rekommenderade HTTP-transport.

**Konsekvens:** Båda transporterna delar samma `mcp`-instans, tools och `bridge.py`. Default: `http://127.0.0.1:8001/mcp`. Nästa steg: tunnel/HTTPS + ChatGPT developer mode-test (utan tunnel-konfig i repo).

---

## 2026-06-15 — MCP skeleton med read-only tools via app/tools/

**Beslut:** Inför `app/mcp/` med FastMCP (`mcp`-paketet); exponera endast `read_calendar`, `read_recent_emails`, `read_email`.

**Motivering:** ChatGPT App / MCP-klienter ska återanvända samma tool-kontrakt utan duplicerad provider-logik.

**Konsekvens:** MCP-lagret anropar `app/tools/` via `bridge.py` — aldrig providers direkt. Servern använder **stdio transport** (lokala MCP-klienter). ChatGPT App/Connector kräver **HTTP/HTTPS-nåbar MCP-endpoint** som separat nästa steg (streamable HTTP-transport eller adapter + tunnel/dev mode). Ingen publicering eller deploy i denna fas.

---

## 2026-06-15 — app/tools/ med enhetligt read-only JSON-kontrakt

**Beslut:** Inför `app/tools/` med `ToolResult` och read-only tools; REST-endpoints delegerar till tools.

**Motivering:** Samma kontrakt för framtida MCP/ChatGPT App/wake-word utan att duplicera provider-logik.

**Konsekvens:** Endast read-tools; write förblir i providers som disabled tills safety finns.

---

## 2026-06-15 — read_email för enskilt meddelande

**Beslut:** Exponera `GET /mail/{message_id}` med normaliserat JSON-svar (inkl. body).

**Motivering:** Komplettera read-only mail med enskild läsning efter list-endpoint.

**Konsekvens:** Fortfarande read-only; ingen mark-as-read, delete eller send.

---

## 2026-06-15 — Token refresh för read-only Graph

**Beslut:** Vid utgången access token ska `refresh_token` användas automatiskt innan Graph-anrop.

**Motivering:** Undvika onödig re-login; behåll read-only-flödet stabilt.

**Konsekvens:** Refresh använder samma read-only scopes; vid failure → 401 och ny login.

---

## 2026-06-15 — Microsoft Graph read-only E2E verifierat

**Beslut:** Read-only Graph är måluppfyllt för MVP: OAuth, token storage, `read_calendar`, `read_recent_emails`.

**Motivering:** Säker bas innan tools-lager, refresh och write-actions.

**Verifierat:** `GET /calendar` och `GET /mail` returnerar riktig Graph-data med personligt Microsoft-konto.

---

## 2026-06-15 — Personligt Microsoft-konto via `common`

**Beslut:** Personliga konton (`@hotmail.com`, `@outlook.com`) kräver `AZURE_TENANT_ID=common` och Entra manifest med `AzureADandPersonalMicrosoftAccount` + token v2.

**Motivering:** Tenant-specifik authority ger 401 på mail/kalender för MSA trots giltig login.

**Konsekvens:** `.env.example` visar `common`; arbetskonton kan använda tenant GUID.

---

## 2026-06-15 — Graph read-only först (bekräftat)

**Beslut:** MVP använder endast `User.Read`, `Mail.Read`, `Calendars.Read` (+ `offline_access`).

**Motivering:** Minimera risk; verifiera läsflöde innan skrivbehörigheter.

**Konsekvens:** `Mail.Send`, `Mail.ReadWrite`, `Calendars.ReadWrite` **väntar**.

---

## 2026-06-15 — Delete fortfarande förbjudet i MVP

**Beslut:** Inga delete-tools eller -endpoints.

**Motivering:** Hög risk; utanför read-only-fasen.

---

## 2026-06-15 — LLM Wiki och agentdokumentation

**Beslut:** Skapa lätt `docs/llm_wiki/` + `AGENTS.md` inspirerad av Karpathy-style wiki-principer, anpassad för Home Agent (inte Fib/Genesis).

**Motivering:** Framtida AI-agenter behöver snabb orientering utan tung governance.

---

## 2026-06-15 — Write-actions senare med bekräftelse

**Beslut:** `create_event`, `send_email`, `mark_as_read` kastar `NotImplementedError` i MVP.

**Motivering:** Skriv kräver safety-lager och användarbekräftelse.

---

## 2026-06-15 — MockProvider som standard utan auth

**Beslut:** Utan giltig token → `MockProvider`, inte fel mot Graph.

**Motivering:** Utveckling och demo utan Azure-setup; tester utan nätverk.

---

## 2026-06-15 — Wake-word / röst senare

**Beslut:** Röst-sidecar är framtida klient, inte del av nuvarande kod.

**Motivering:** Samma backend ska kunna återanvändas när klienten finns.

---

## 2026-06-15 — Separat repo från Fibonacci och Genesis

**Beslut:** Detta repo är Home Agent — ingen delad governance med Fib/Genesis.

**Motivering:** Personlig kalender/mail-agent med enkel utvecklingsmodell.
