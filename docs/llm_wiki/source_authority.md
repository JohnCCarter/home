# Källauktoritet

När dokumentation, kommentarer och kod inte stämmer överens — följ denna ordning.

## 1. Kod i repot (högsta auktoritet)

- Python-filer under `app/` och `tests/`
- `requirements.txt`
- Faktisk routing, scopes och felhantering i koden

**Regel:** Om wikin säger X men koden gör Y — lita på koden och uppdatera wikin om du ändrar beteendet.

## 2. Tester

- Tester beskriver förväntat beteende för auth, config och providers
- Gröna tester + läsbar kod slår gammal wiki-text

## 3. `AGENTS.md`

- Styr **agentbeteende** (vad du får/inte får göra)
- Pekar till denna wiki för djupare kontext

## 4. LLM Wiki (`docs/llm_wiki/`)

- Förklarar och orienterar
- **Får inte ersätta** kod eller tester
- [handoff.md](handoff.md) och [decision_log.md](decision_log.md) kan vara något inaktuella — verifiera mot kod vid tvivel

## 5. `.env.example`

- **Mall** med placeholders (`your-tenant-id`, etc.)
- Inte verklig konfiguration
- Kopiera till lokal `.env` och fyll i riktiga värden utanför git

## Vad som aldrig är auktoritet

| Källa | Varför |
|-------|--------|
| Lokal `.env` | Gitignored, personlig |
| `token_store.json` | Gitignored, innehåller tokens |
| Chatthistorik / minne | Kan vara fel eller från annat repo |
| Fibonacci / Genesis-dokumentation | Fel projekt |

## Vid konflikt

1. Läs relevant kod och test
2. Gör minimal fix eller uppdatera wiki/handoff
3. Stoppa och rapportera om säkerhetsrelaterat (secrets, write utan bekräftelse)
