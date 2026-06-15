# Beslutlogg

Enkel logg över arkitektur- och scope-beslut. Nyaste överst.

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
