from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.auth import microsoft
from app.auth import token_store
from app.main import app
from app.providers.outlook_provider import OutlookProvider


@pytest.fixture(autouse=True)
def set_env(monkeypatch, tmp_path):
    monkeypatch.setenv("AZURE_TENANT_ID", "common")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AZURE_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.chdir(tmp_path)
    microsoft._pending_states.clear()


def _valid_tokens() -> dict:
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    return {
        "access_token": "valid-access-token",
        "refresh_token": "valid-refresh-token",
        "expires_at": expires_at,
        "token_type": "Bearer",
        "scope": "offline_access User.Read Mail.Read Calendars.Read",
    }


def _expired_tokens() -> dict:
    expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    return {
        "access_token": "expired-access-token",
        "refresh_token": "valid-refresh-token",
        "expires_at": expires_at,
        "token_type": "Bearer",
        "scope": "offline_access User.Read Mail.Read Calendars.Read",
    }


@pytest.mark.asyncio
async def test_valid_token_used_without_refresh(monkeypatch):
    token_store.save_tokens(_valid_tokens())
    refresh_called = False

    async def fake_refresh(refresh_token: str):
        nonlocal refresh_called
        refresh_called = True
        return {}

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    tokens = await microsoft.get_valid_tokens()

    assert tokens is not None
    assert tokens["access_token"] == "valid-access-token"
    assert refresh_called is False


@pytest.mark.asyncio
async def test_expired_token_triggers_refresh(monkeypatch):
    token_store.save_tokens(_expired_tokens())

    async def fake_refresh(refresh_token: str):
        assert refresh_token == "valid-refresh-token"
        return {
            "access_token": "new-access-token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "offline_access User.Read Mail.Read Calendars.Read",
        }

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    tokens = await microsoft.get_valid_tokens()

    assert tokens is not None
    assert tokens["access_token"] == "new-access-token"
    assert tokens["refresh_token"] == "valid-refresh-token"


@pytest.mark.asyncio
async def test_successful_refresh_persists_tokens(monkeypatch):
    token_store.save_tokens(_expired_tokens())

    async def fake_refresh(refresh_token: str):
        return {
            "access_token": "persisted-access-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    await microsoft.get_valid_tokens()
    saved = token_store.load_stored_tokens()

    assert saved is not None
    assert saved["access_token"] == "persisted-access-token"
    assert saved["refresh_token"] == "valid-refresh-token"
    assert saved["expires_at"] is not None


@pytest.mark.asyncio
async def test_failed_refresh_returns_none(monkeypatch):
    token_store.save_tokens(_expired_tokens())

    async def fake_refresh(refresh_token: str):
        raise microsoft.TokenRefreshError("Refresh token expired or revoked. Please sign in again.")

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    tokens = await microsoft.get_valid_tokens()

    assert tokens is None


def test_failed_refresh_returns_401_on_calendar(monkeypatch):
    token_store.save_tokens(_expired_tokens())

    async def fake_refresh(refresh_token: str):
        raise microsoft.TokenRefreshError("Refresh token expired or revoked. Please sign in again.")

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    client = TestClient(app)
    response = client.get("/calendar")

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Token expired or refresh failed. Please re-authenticate via /auth/microsoft/login"
    )


def test_refresh_tokens_never_logged(monkeypatch, caplog):
    token_store.save_tokens(_expired_tokens())

    async def fake_refresh(refresh_token: str):
        raise microsoft.TokenRefreshError("Refresh token expired or revoked. Please sign in again.")

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    with caplog.at_level("INFO"):
        client = TestClient(app)
        client.get("/calendar")

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "valid-refresh-token" not in all_logs
    assert "expired-access-token" not in all_logs
    assert "super-secret" not in all_logs


def test_calendar_uses_refreshed_token(monkeypatch):
    token_store.save_tokens(_expired_tokens())
    seen_tokens: list[str] = []

    async def fake_refresh(refresh_token: str):
        return {
            "access_token": "refreshed-access-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    async def fake_read_calendar(self):
        seen_tokens.append(self._access_token)
        return []

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)
    monkeypatch.setattr(OutlookProvider, "read_calendar", fake_read_calendar)

    client = TestClient(app)
    response = client.get("/calendar")

    assert response.status_code == 200
    assert seen_tokens == ["refreshed-access-token"]
