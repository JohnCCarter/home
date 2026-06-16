"""Google OAuth (read-only) route: PKCE/state, exact scopes, token isolation, optional config.

Token exchange is monkeypatched (no network). All token values are obvious fakes.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.auth import google
from app.auth import token_store
from app.config import GoogleSettings, get_google_settings, get_settings
from app.main import app

EXPECTED_SCOPES = "openid email https://www.googleapis.com/auth/calendar.events.readonly"


@pytest.fixture(autouse=True)
def set_env(monkeypatch, tmp_path):
    # Microsoft config present (other routes import fine); Google config present here.
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AZURE_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "g-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "g-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/auth/google/callback")
    monkeypatch.chdir(tmp_path)
    google._pending_states.clear()


# --- config: optional + independent ------------------------------------------


def test_google_settings_loaded():
    settings = get_google_settings()
    assert isinstance(settings, GoogleSettings)
    assert settings.google_client_id == "g-client"


def test_google_settings_missing_raises(monkeypatch):
    for var in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError):
        get_google_settings()


def test_microsoft_settings_independent_of_google(monkeypatch):
    # Microsoft config must not require GOOGLE_* at all.
    for var in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"):
        monkeypatch.delenv(var, raising=False)
    settings = get_settings()
    assert settings.azure_client_id == "client"


# --- login -------------------------------------------------------------------


def test_login_redirect_has_pkce_state_and_exact_scopes():
    client = TestClient(app)
    response = client.get("/auth/google/login", follow_redirects=False)

    assert response.status_code == 307
    parsed = urlparse(response.headers["location"])
    assert parsed.netloc == "accounts.google.com"
    params = parse_qs(parsed.query)

    assert params["scope"] == [EXPECTED_SCOPES]
    assert params["code_challenge_method"] == ["S256"]
    assert "code_challenge" in params
    assert "state" in params
    assert params["access_type"] == ["offline"]
    assert params["prompt"] == ["consent"]


def test_login_returns_503_when_google_not_configured(monkeypatch):
    for var in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"):
        monkeypatch.delenv(var, raising=False)
    client = TestClient(app)
    response = client.get("/auth/google/login", follow_redirects=False)
    assert response.status_code == 503


def test_login_scope_excludes_write_and_gmail():
    client = TestClient(app)
    response = client.get("/auth/google/login", follow_redirects=False)
    scope = parse_qs(urlparse(response.headers["location"]).query)["scope"][0]
    assert "gmail" not in scope
    assert "calendar.events.readonly" in scope
    # No full-access / write calendar scope.
    assert "auth/calendar " not in scope + " "
    assert ".modify" not in scope


# --- callback ----------------------------------------------------------------


def test_callback_rejects_invalid_state():
    client = TestClient(app)
    response = client.get("/auth/google/callback", params={"code": "abc", "state": "bad"})
    assert response.status_code == 400
    assert "Invalid or expired OAuth state" in response.text


def test_callback_saves_google_token_isolated_from_microsoft(monkeypatch):
    async def fake_exchange(code: str, code_verifier: str):
        return {"access_token": "fake-google-access", "refresh_token": "fake-google-refresh", "expires_in": 3600}

    monkeypatch.setattr(google, "_exchange_code_for_tokens", fake_exchange)

    client = TestClient(app)
    state = parse_qs(urlparse(client.get("/auth/google/login", follow_redirects=False).headers["location"]).query)["state"][0]
    response = client.get("/auth/google/callback", params={"code": "abc", "state": state})

    assert response.status_code == 200
    assert "Login successful" in response.text
    # Saved under the google namespace only — Microsoft file untouched.
    assert token_store.load_stored_tokens("google")["access_token"] == "fake-google-access"
    assert token_store.has_stored_tokens("microsoft") is False


def test_callback_tokens_never_in_response_or_logs(monkeypatch, caplog):
    async def fake_exchange(code: str, code_verifier: str):
        return {"access_token": "super-secret-google", "refresh_token": "super-secret-refresh", "expires_in": 3600}

    monkeypatch.setattr(google, "_exchange_code_for_tokens", fake_exchange)

    client = TestClient(app)
    state = parse_qs(urlparse(client.get("/auth/google/login", follow_redirects=False).headers["location"]).query)["state"][0]
    with caplog.at_level("INFO"):
        response = client.get("/auth/google/callback", params={"code": "abc", "state": state})

    assert response.status_code == 200
    assert "super-secret-google" not in response.text
    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "super-secret-google" not in all_logs
    assert "super-secret-refresh" not in all_logs


# --- refresh flow (get_valid_google_tokens) ----------------------------------


def _save_google_token(*, access: str, refresh: str | None = None, expired: bool = False) -> None:
    delta = timedelta(hours=-1) if expired else timedelta(hours=1)
    data = {"access_token": access, "expires_at": (datetime.now(timezone.utc) + delta).isoformat()}
    if refresh is not None:
        data["refresh_token"] = refresh
    token_store.save_tokens(data, provider="google")


@pytest.mark.asyncio
async def test_get_valid_google_tokens_valid_returns_without_refresh(monkeypatch):
    _save_google_token(access="still-valid", refresh="r", expired=False)

    async def must_not_refresh(refresh_token: str):
        raise AssertionError("refresh must not be called for a valid token")

    monkeypatch.setattr(google, "refresh_google_access_token", must_not_refresh)

    tokens = await google.get_valid_google_tokens()
    assert tokens["access_token"] == "still-valid"


@pytest.mark.asyncio
async def test_get_valid_google_tokens_refreshes_when_expired(monkeypatch):
    _save_google_token(access="old-access", refresh="refresh-1", expired=True)

    async def fake_refresh(refresh_token: str):
        assert refresh_token == "refresh-1"
        return {"access_token": "new-access", "expires_in": 3600}

    monkeypatch.setattr(google, "refresh_google_access_token", fake_refresh)

    tokens = await google.get_valid_google_tokens()
    assert tokens["access_token"] == "new-access"
    # Persisted under the google namespace.
    assert token_store.load_stored_tokens("google")["access_token"] == "new-access"


@pytest.mark.asyncio
async def test_get_valid_google_tokens_preserves_refresh_token(monkeypatch):
    _save_google_token(access="old-access", refresh="keep-me", expired=True)

    async def fake_refresh(refresh_token: str):
        # Google often omits refresh_token on refresh.
        return {"access_token": "new-access", "expires_in": 3600}

    monkeypatch.setattr(google, "refresh_google_access_token", fake_refresh)

    tokens = await google.get_valid_google_tokens()
    assert tokens["refresh_token"] == "keep-me"
    assert token_store.load_stored_tokens("google")["refresh_token"] == "keep-me"


@pytest.mark.asyncio
async def test_get_valid_google_tokens_refresh_failure_returns_none(monkeypatch):
    _save_google_token(access="old-access", refresh="refresh-1", expired=True)

    async def failing_refresh(refresh_token: str):
        raise google.TokenRefreshError("refresh rejected")

    monkeypatch.setattr(google, "refresh_google_access_token", failing_refresh)

    assert await google.get_valid_google_tokens() is None


@pytest.mark.asyncio
async def test_get_valid_google_tokens_missing_config_fails_closed(monkeypatch):
    # Expired token needs a refresh, but Google config is absent → fail closed (None),
    # never a 500 into the tools path.
    for var in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"):
        monkeypatch.delenv(var, raising=False)
    _save_google_token(access="old-access", refresh="refresh-1", expired=True)

    assert await google.get_valid_google_tokens() is None
