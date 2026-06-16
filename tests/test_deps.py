"""Calendar provider selection (HOME_AGENT_CALENDAR_PROVIDER).

Encodes the invariant: flag unset ⇒ behavior identical to today (Microsoft default,
Google never wins on token presence alone). Google is calendar-only and must never
reach the shared mail/calendar selector. Offline — tokens are obvious fakes saved to
a tmp cwd; no network (tokens are non-expired so no refresh runs).
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.auth import token_store
from app.providers.google_provider import GoogleProvider
from app.providers.mock_provider import MockProvider
from app.providers.outlook_provider import OutlookProvider
from app.tools.deps import (
    AuthRequiredError,
    get_calendar_provider_with_name,
    get_provider_with_name,
)


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOME_AGENT_CALENDAR_PROVIDER", raising=False)


def _save_token(provider: str, *, expired: bool = False) -> None:
    delta = timedelta(hours=-1) if expired else timedelta(hours=1)
    token_store.save_tokens(
        {
            "access_token": f"fake-{provider}-access",
            "expires_at": (datetime.now(timezone.utc) + delta).isoformat(),
        },
        provider=provider,
    )


# --- flag unset: behavior identical to today ---------------------------------


@pytest.mark.asyncio
async def test_flag_unset_both_authed_microsoft_wins():
    _save_token("microsoft")
    _save_token("google")

    provider, name = await get_calendar_provider_with_name()

    assert isinstance(provider, OutlookProvider)
    assert name == "outlook"


@pytest.mark.asyncio
async def test_flag_unset_only_google_token_does_not_select_google():
    _save_token("google")  # no Microsoft token at all

    provider, name = await get_calendar_provider_with_name()

    # Google token presence alone must NOT pull in Google.
    assert not isinstance(provider, GoogleProvider)
    assert isinstance(provider, MockProvider)
    assert name == "mock"


# --- explicit google selection -----------------------------------------------


@pytest.mark.asyncio
async def test_flag_google_with_valid_token_selects_google(monkeypatch):
    monkeypatch.setenv("HOME_AGENT_CALENDAR_PROVIDER", "google")
    _save_token("google")

    provider, name = await get_calendar_provider_with_name()

    assert isinstance(provider, GoogleProvider)
    assert name == "google"


@pytest.mark.asyncio
async def test_flag_google_missing_token_raises_auth_required(monkeypatch):
    monkeypatch.setenv("HOME_AGENT_CALENDAR_PROVIDER", "google")

    with pytest.raises(AuthRequiredError) as exc:
        await get_calendar_provider_with_name()

    # Fail-fast to the Google login, not a silent Microsoft fallback.
    assert "/auth/google/login" in exc.value.message


@pytest.mark.asyncio
async def test_flag_google_expired_token_raises_auth_required(monkeypatch):
    monkeypatch.setenv("HOME_AGENT_CALENDAR_PROVIDER", "google")
    _save_token("google", expired=True)
    _save_token("microsoft")  # present, but explicit google choice must not fall back

    with pytest.raises(AuthRequiredError) as exc:
        await get_calendar_provider_with_name()

    assert "/auth/google/login" in exc.value.message


# --- mail path is never Google -----------------------------------------------


@pytest.mark.asyncio
async def test_mail_selector_never_returns_google(monkeypatch):
    monkeypatch.setenv("HOME_AGENT_CALENDAR_PROVIDER", "google")
    _save_token("google")  # google selected for calendar, but mail must ignore it

    provider, name = await get_provider_with_name()

    assert not isinstance(provider, GoogleProvider)
    assert isinstance(provider, MockProvider)
    assert name == "mock"
