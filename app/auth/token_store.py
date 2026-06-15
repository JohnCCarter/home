import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

TOKEN_STORE_PATH = Path("token_store.json")
EXPIRY_BUFFER_SECONDS = 60


def _normalize_tokens(tokens: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(tokens)
    if "expires_in" in normalized and "expires_at" not in normalized:
        expires_in = int(normalized["expires_in"])
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        normalized["expires_at"] = expires_at.isoformat()
    return normalized


def save_tokens(tokens: Dict[str, Any]) -> None:
    TOKEN_STORE_PATH.write_text(json.dumps(_normalize_tokens(tokens), indent=2), encoding="utf-8")
    try:
        TOKEN_STORE_PATH.chmod(0o600)
    except OSError:
        pass


def load_stored_tokens() -> Optional[Dict[str, Any]]:
    """Load tokens from disk without checking expiry (for refresh flow)."""
    if not TOKEN_STORE_PATH.exists():
        return None

    try:
        return json.loads(TOKEN_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def load_tokens() -> Optional[Dict[str, Any]]:
    data = load_stored_tokens()
    if not data:
        return None

    if is_token_expired(data):
        return None
    return data


def clear_tokens() -> None:
    if TOKEN_STORE_PATH.exists():
        TOKEN_STORE_PATH.unlink()


def has_stored_tokens() -> bool:
    return TOKEN_STORE_PATH.exists()


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
