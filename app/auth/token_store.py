import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_PROVIDER = "microsoft"
EXPIRY_BUFFER_SECONDS = 60

# Token storage is namespaced by provider so a future Google login can never
# overwrite the Microsoft token (separate local files). Paths are relative on
# purpose — they resolve against the current working directory, which keeps the
# chdir-based test isolation working.
_PROVIDER_TOKEN_FILES: Dict[str, str] = {
    "microsoft": "token_store.json",
    "google": "token_store_google.json",
}


def token_store_path(provider: str = DEFAULT_PROVIDER) -> Path:
    """Return the token file for a provider. Unknown provider fails closed."""
    try:
        filename = _PROVIDER_TOKEN_FILES[provider]
    except KeyError:
        known = ", ".join(sorted(_PROVIDER_TOKEN_FILES))
        raise ValueError(f"Unknown token provider {provider!r}; expected one of: {known}")
    return Path(filename)


# Backward-compatible constant: the Microsoft/default token file path.
TOKEN_STORE_PATH = token_store_path()


def _normalize_tokens(tokens: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(tokens)
    if "expires_in" in normalized and "expires_at" not in normalized:
        expires_in = int(normalized["expires_in"])
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        normalized["expires_at"] = expires_at.isoformat()
    return normalized


def save_tokens(tokens: Dict[str, Any], provider: str = DEFAULT_PROVIDER) -> None:
    path = token_store_path(provider)
    path.write_text(json.dumps(_normalize_tokens(tokens), indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def load_stored_tokens(provider: str = DEFAULT_PROVIDER) -> Optional[Dict[str, Any]]:
    """Load tokens from disk without checking expiry (for refresh flow)."""
    path = token_store_path(provider)
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def load_tokens(provider: str = DEFAULT_PROVIDER) -> Optional[Dict[str, Any]]:
    data = load_stored_tokens(provider)
    if not data:
        return None

    if is_token_expired(data):
        return None
    return data


def clear_tokens(provider: str = DEFAULT_PROVIDER) -> None:
    path = token_store_path(provider)
    if path.exists():
        path.unlink()


def has_stored_tokens(provider: str = DEFAULT_PROVIDER) -> bool:
    return token_store_path(provider).exists()


def is_token_expired(tokens: Dict[str, Any]) -> bool:
    expires_at_raw = tokens.get("expires_at")
    if not expires_at_raw:
        return True

    try:
        expires_at = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
    except ValueError:
        return True

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return expires_at <= datetime.now(timezone.utc) + timedelta(seconds=EXPIRY_BUFFER_SECONDS)
