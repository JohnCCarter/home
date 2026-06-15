from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.auth import microsoft
from app.auth.token_store import is_token_expired
from app.main import app


@pytest.fixture(autouse=True)
def set_env(monkeypatch, tmp_path):
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AZURE_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.chdir(tmp_path)
    microsoft._pending_states.clear()


def test_login_redirect_contains_pkce_and_state():
    client = TestClient(app)

    response = client.get("/auth/microsoft/login", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    parsed = urlparse(location)
    params = parse_qs(parsed.query)

    assert params["code_challenge_method"] == ["S256"]
    assert "code_challenge" in params
    assert "state" in params
    assert params["scope"] == ["offline_access User.Read Mail.Read Calendars.Read"]


def test_callback_rejects_invalid_state():
    client = TestClient(app)

    response = client.get("/auth/microsoft/callback", params={"code": "abc", "state": "bad"})

    assert response.status_code == 400
    assert "Invalid or expired OAuth state" in response.text


def test_tokens_never_returned_or_logged(monkeypatch, caplog):
    async def fake_exchange(code: str, code_verifier: str):
        return {
            "access_token": "super-secret-access",
            "refresh_token": "super-secret-refresh",
            "expires_in": 3600,
        }

    monkeypatch.setattr(microsoft, "_exchange_code_for_tokens", fake_exchange)

    client = TestClient(app)
    login_response = client.get("/auth/microsoft/login", follow_redirects=False)
    state = parse_qs(urlparse(login_response.headers["location"]).query)["state"][0]

    with caplog.at_level("INFO"):
        response = client.get("/auth/microsoft/callback", params={"code": "abc", "state": state})

    assert response.status_code == 200
    assert "Login successful" in response.text
    assert "super-secret-access" not in response.text

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "super-secret-access" not in all_logs
    assert "super-secret-refresh" not in all_logs
    assert "secret" not in all_logs


# --- is_token_expired edge-case tests ---


def test_is_token_expired_z_suffix_future():
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert not is_token_expired({"expires_at": future})


def test_is_token_expired_z_suffix_past():
    past = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert is_token_expired({"expires_at": past})


def test_is_token_expired_invalid_timestamp():
    assert is_token_expired({"expires_at": "not-a-timestamp"})


def test_is_token_expired_missing_key():
    assert is_token_expired({})


def test_is_token_expired_within_buffer():
    # expires in 30s, inside the 60s buffer → should count as expired
    near = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat()
    assert is_token_expired({"expires_at": near})


def test_is_token_expired_outside_buffer():
    # expires in 90s, outside the 60s buffer → not expired
    outside = (datetime.now(timezone.utc) + timedelta(seconds=90)).isoformat()
    assert not is_token_expired({"expires_at": outside})
