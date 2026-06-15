# Testning

## Köra tester

Från repo-roten:

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

Verbose:

```bash
PYTHONPATH=. pytest -v
```

Enskild fil:

```bash
PYTHONPATH=. pytest tests/test_auth.py -v
```

`PYTHONPATH=.` behövs eftersom `app` inte är installerat som paket än.

## Principer

| Princip | |
|---------|---|
| Inga riktiga Microsoft/Google-credentials i CI eller lokala tester | Env sätts via `monkeypatch` i fixtures |
| Mocka HTTP | `httpx.MockTransport` för Graph-anrop |
| Mock-provider ska alltid fungera | Ingen nätverksaccess krävs för grundflöde |
| Tokens får inte synas i loggar | `test_tokens_never_returned_or_logged` |

## Testfiler

| Fil | Täcker |
|-----|--------|
| `tests/test_auth.py` | OAuth login/callback, PKCE, state, token-loggning |
| `tests/test_config.py` | `.env`-laddning, saknade variabler |
| `tests/test_outlook_provider.py` | Graph parsing, disabled write |

## Mock-provider

`MockProvider` returnerar fast kalender- och mail-data utan token:

- Används automatiskt i `GET /calendar` och `GET /mail` när ingen giltig token finns
- Ska fortsatt fungera efter refaktoreringar — lägg till regressionstest vid behov

## Kända fallgropar

- **`test_missing_settings_raise_clear_error`** — kan fallera om riktig `.env` finns i cwd och laddas före testet. Tester som kräver tom env bör chdir till `tmp_path` eller rensa env explicit.
- Auth-tester använder `tmp_path` + `monkeypatch.chdir` för isolerad token-fil.

## Innan merge / handoff

- Kör hela testsviten
- Notera antal passed/failed i [handoff.md](handoff.md)
- Lägg inte till tester som bäddar in riktiga secrets — använd `test-secret`, `token` etc. som testdata
