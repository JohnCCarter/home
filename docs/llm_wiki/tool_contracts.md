# Tool-kontrakt

Alla tools ska returnera **strukturerad JSON** med konsekvent form:

```json
{
  "ok": true,
  "data": { },
  "error": null
}
```

Vid fel: `ok: false`, `data: null`, `error` med kod och meddelande.

**Status idag:** Tools är definierade som kontrakt; REST-endpoints (`GET /calendar`, `GET /mail`) och provider-metoder implementerar delar av read-flödet. Ett dedikerat `app/tools/`-lager är planerat.

---

## `read_calendar`

Läser kommande kalenderhändelser.

| | |
|---|---|
| **Input** | `limit` (valfri int, default 10), `time_min` / `time_max` (valfria ISO-8601, senare) |
| **Output** | Lista av händelser: `id`, `subject`, `start`, `end` (ISO-8601) |
| **Provider** | `OutlookProvider.read_calendar()` / `MockProvider` |
| **Säkerhet** | Läs — körs direkt |

---

## `create_calendar_event`

Skapar kalenderhändelse.

| | |
|---|---|
| **Input** | `subject`, `start`, `end`, valfritt `location`, `attendees` |
| **Output** | Skapad händelse med `id` |
| **Status** | **Ej implementerad** — `NotImplementedError("disabled in MVP phase")` |
| **Säkerhet** | Skriv — kräver användarbekräftelse; kräver `Calendars.ReadWrite` (inte aktiverat än) |

---

## `read_recent_emails`

Läser senaste meddelanden i inkorgen.

| | |
|---|---|
| **Input** | `limit` (valfri int, default 10), valfri `folder` (senare) |
| **Output** | Lista: `id`, `subject`, `sender`, `received_at` |
| **Provider** | `OutlookProvider.read_recent_emails()` / `MockProvider` |
| **Säkerhet** | Läs — körs direkt |

---

## `read_email`

Läser ett enskilt meddelande (brödtext/HTML).

| | |
|---|---|
| **Input** | `message_id` (str) |
| **Output** | `id`, `subject`, `sender`, `received_at`, `body_preview` eller `body` |
| **Status** | **Planerad** — inte exponerad än |
| **Säkerhet** | Läs — körs direkt |

---

## `draft_email`

Skapar utkast utan att skicka.

| | |
|---|---|
| **Input** | `to`, `subject`, `body`, valfritt `cc`, `bcc` |
| **Output** | `draft_id`, sammanfattning av utkast |
| **Status** | **Planerad** |
| **Säkerhet** | Skriv — kräver bekräftelse innan sparning |

---

## `send_email`

Skickar e-post.

| | |
|---|---|
| **Input** | `to`, `subject`, `body`, valfritt `cc`, `bcc`; eller `draft_id` |
| **Output** | `message_id`, `status: "sent"` |
| **Status** | **Ej implementerad** — disabled i MVP |
| **Säkerhet** | Skriv — kräver explicit bekräftelse; kräver `Mail.Send` (inte aktiverat än) |

---

## Mappning REST → tools (interim)

| Endpoint | Tool |
|----------|------|
| `GET /calendar` | `read_calendar` |
| `GET /mail` | `read_recent_emails` |

Nya capabilities ska gå via tool-lager när det finns — inte som ad hoc-endpoints.
