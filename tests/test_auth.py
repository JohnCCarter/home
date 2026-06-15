from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.auth import microsoft
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
    assert response.json()["detail"] == "Invalid OAuth state"


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
    assert response.json() == {"status": "authenticated"}

    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "super-secret-access" not in all_logs
    assert "super-secret-refresh" not in all_logs
    assert "secret" not in all_logs
