import importlib
from pathlib import Path

import pytest


def test_get_settings_loads_from_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AZURE_TENANT_ID=test-tenant",
                "AZURE_CLIENT_ID=test-client",
                "AZURE_CLIENT_SECRET=test-secret",
                "AZURE_REDIRECT_URI=http://localhost/callback",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    for name in (
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID",
        "AZURE_CLIENT_SECRET",
        "AZURE_REDIRECT_URI",
    ):
        monkeypatch.delenv(name, raising=False)

    from app.config import get_settings

    settings = get_settings()

    assert settings.azure_tenant_id == "test-tenant"
    assert settings.azure_client_id == "test-client"
    assert settings.azure_client_secret == "test-secret"
    assert settings.azure_redirect_uri == "http://localhost/callback"


def test_missing_settings_raise_clear_error(monkeypatch):
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_REDIRECT_URI", raising=False)

    from app.config import get_settings

    with pytest.raises(RuntimeError) as exc:
        get_settings()

    assert "Missing required environment variables" in str(exc.value)


def test_app_import_does_not_embed_real_secrets(monkeypatch):
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_CLIENT_ID", "client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AZURE_REDIRECT_URI", "http://localhost/callback")

    module = importlib.import_module("app.main")

    assert module.app.title == "genesis-core-home-agent"
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "super-secret" not in source
