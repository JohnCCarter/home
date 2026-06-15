from datetime import datetime, timedelta, timezone

import httpx
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


@pytest.mark.asyncio
async def test_read_email_normalizes_graph_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/v1.0/me/messages/msg-42")
        assert request.url.params.get("$select")
        return httpx.Response(
            status_code=200,
            json={
                "id": "msg-42",
                "subject": "Test subject",
                "from": {"emailAddress": {"address": "sender@example.com"}},
                "receivedDateTime": "2026-06-15T10:00:00Z",
                "bodyPreview": "Preview line",
                "body": {"contentType": "html", "content": "<p>Hello</p>"},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OutlookProvider(access_token="token", client=client)
        email = await provider.read_email("msg-42")

    assert email.id == "msg-42"
    assert email.subject == "Test subject"
    assert email.sender == "sender@example.com"
    assert email.body_preview == "Preview line"
    assert email.body.content_type == "html"
    assert email.body.content == "<p>Hello</p>"


@pytest.mark.asyncio
async def test_read_email_404_is_clear():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={"error": {"code": "ErrorItemNotFound"}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        provider = OutlookProvider(access_token="token", client=client)
        with pytest.raises(Exception) as exc:
            await provider.read_email("missing-id")

    from app.providers.outlook_provider import GraphApiError

    assert isinstance(exc.value, GraphApiError)
    assert exc.value.status_code == 404
    assert exc.value.message == "Email message not found."


def test_read_email_endpoint_uses_valid_tokens(monkeypatch):
    token_store.save_tokens(_valid_tokens())

    async def fake_read_email(self, message_id: str):
        assert message_id == "msg-42"
        from app.providers.base import EmailBody, EmailDetail

        return EmailDetail(
            id="msg-42",
            subject="Endpoint subject",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            body_preview="preview",
            body=EmailBody(content_type="text", content="body text"),
        )

    monkeypatch.setattr(OutlookProvider, "read_email", fake_read_email)

    client = TestClient(app)
    response = client.get("/mail/msg-42")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "msg-42"
    assert data["body"]["content"] == "body text"


def test_read_email_endpoint_404(monkeypatch):
    token_store.save_tokens(_valid_tokens())

    async def fake_read_email(self, message_id: str):
        from app.providers.outlook_provider import GraphApiError

        raise GraphApiError(404, "Email message not found.")

    monkeypatch.setattr(OutlookProvider, "read_email", fake_read_email)

    client = TestClient(app)
    response = client.get("/mail/missing-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Email message not found."


def test_read_email_endpoint_auth_failure(monkeypatch):
    token_store.save_tokens(
        {
            "access_token": "expired-access-token",
            "refresh_token": "valid-refresh-token",
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
    )

    async def fake_refresh(refresh_token: str):
        raise microsoft.TokenRefreshError("Refresh token expired or revoked. Please sign in again.")

    monkeypatch.setattr(microsoft, "refresh_access_token", fake_refresh)

    client = TestClient(app)
    response = client.get("/mail/msg-42")

    assert response.status_code == 401
    assert "re-authenticate" in response.json()["detail"]


def test_read_email_body_not_logged(monkeypatch, caplog):
    token_store.save_tokens(_valid_tokens())

    async def fake_read_email(self, message_id: str):
        from app.providers.base import EmailBody, EmailDetail

        return EmailDetail(
            id="msg-42",
            subject="Secret subject",
            sender="sender@example.com",
            received_at=datetime.now(timezone.utc),
            body_preview="secret preview",
            body=EmailBody(content_type="text", content="super-private-body-text"),
        )

    monkeypatch.setattr(OutlookProvider, "read_email", fake_read_email)

    with caplog.at_level("INFO"):
        client = TestClient(app)
        response = client.get("/mail/msg-42")

    assert response.status_code == 200
    all_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "super-private-body-text" not in all_logs
    assert "secret preview" not in all_logs


def test_mock_read_email_without_auth():
    client = TestClient(app)
    response = client.get("/mail/mock-email-1")

    assert response.status_code == 200
    assert response.json()["id"] == "mock-email-1"
