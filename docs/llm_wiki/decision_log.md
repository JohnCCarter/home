# Beslutlogg

Enkel logg över arkitektur- och scope-beslut. Nyaste överst.

---

## 2026-06-15 — LLM Wiki och agentdokumentation

**Beslut:** Skapa lätt `docs/llm_wiki/` + `AGENTS.md` inspirerad av Karpathy-style wiki-principer, anpassad för Home Agent (inte Fib/Genesis).

**Motivering:** Framtida AI-agenter behöver snabb orientering utan tung governance.

---

## 2026-06-15 — Microsoft Graph read-only först

**Beslut:** MVP använder `User.Read`, `Mail.Read`, `Calendars.Read` (+ `offline_access`).

**Motivering:** Minimera risk; verifiera läsflöde innan skrivbehörigheter.

**Konsekvens:** `Mail.Send` och `Calendars.ReadWrite` ska inte aktiveras än.

---

## 2026-06-15 — Write-actions senare med bekräftelse

**Beslut:** `create_event`, `send_email`, `mark_as_read` kastar `NotImplementedError` i MVP.

**Motivering:** Skriv kräver safety-lager och användarbekräftelse.

---

## 2026-06-15 — Ingen delete i MVP

**Beslut:** Inga delete-tools eller -endpoints.

**Motivering:** Hög risk; utanför initial scope.

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
