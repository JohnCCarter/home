"""Token store is namespaced per provider so Google can never overwrite Microsoft.

All token values here are obvious fakes (no real secrets). Isolation uses chdir into
tmp_path so no real local token file is touched.
"""

from pathlib import Path

import pytest

from app.auth import token_store

# Obvious non-secret placeholders.
_MS = {"access_token": "fake-ms-access", "expires_at": "2999-01-01T00:00:00+00:00"}
_GOOGLE = {"access_token": "fake-google-access", "expires_at": "2999-01-01T00:00:00+00:00"}


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)


def test_default_path_matches_legacy():
    assert token_store.token_store_path() == Path("token_store.json")


def test_microsoft_uses_legacy_file():
    assert token_store.token_store_path("microsoft") == Path("token_store.json")


def test_google_uses_separate_file():
    assert token_store.token_store_path("google") == Path("token_store_google.json")


def test_microsoft_and_google_are_isolated():
    token_store.save_tokens(_MS, provider="microsoft")
    token_store.save_tokens(_GOOGLE, provider="google")

    assert token_store.load_stored_tokens("microsoft")["access_token"] == "fake-ms-access"
    assert token_store.load_stored_tokens("google")["access_token"] == "fake-google-access"
    assert Path("token_store.json").exists()
    assert Path("token_store_google.json").exists()


def test_saving_google_does_not_overwrite_microsoft():
    token_store.save_tokens(_MS, provider="microsoft")
    token_store.save_tokens(_GOOGLE, provider="google")
    assert token_store.load_stored_tokens("microsoft")["access_token"] == "fake-ms-access"


def test_saving_microsoft_does_not_overwrite_google():
    token_store.save_tokens(_GOOGLE, provider="google")
    token_store.save_tokens(_MS, provider="microsoft")
    assert token_store.load_stored_tokens("google")["access_token"] == "fake-google-access"


def test_load_without_provider_is_backward_compatible():
    token_store.save_tokens(_MS)  # default = microsoft
    assert token_store.load_stored_tokens()["access_token"] == "fake-ms-access"
    assert token_store.load_tokens()["access_token"] == "fake-ms-access"


def test_save_without_provider_writes_microsoft_file():
    token_store.save_tokens(_MS)
    assert Path("token_store.json").exists()
    assert not Path("token_store_google.json").exists()


def test_clear_and_has_stored_are_namespaced():
    token_store.save_tokens(_MS, provider="microsoft")
    token_store.save_tokens(_GOOGLE, provider="google")
    token_store.clear_tokens("google")
    assert token_store.has_stored_tokens("microsoft") is True
    assert token_store.has_stored_tokens("google") is False


@pytest.mark.parametrize("op", ["path", "save", "load", "clear", "has"])
def test_unknown_provider_fails_closed(op):
    with pytest.raises(ValueError):
        if op == "path":
            token_store.token_store_path("dropbox")
        elif op == "save":
            token_store.save_tokens(_MS, provider="dropbox")
        elif op == "load":
            token_store.load_stored_tokens("dropbox")
        elif op == "clear":
            token_store.clear_tokens("dropbox")
        else:
            token_store.has_stored_tokens("dropbox")
