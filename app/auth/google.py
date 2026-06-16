"""Google OAuth (read-only) — parallel to the Microsoft flow.

Authorization code + PKCE. Tokens are saved under the "google" provider namespace
(token_store_google.json) so they never collide with the Microsoft token. This adds
NO provider runtime, NO MCP/tool changes, and NO write/delete scopes — read-only
calendar + minimal identity only.
"""

import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import token_store
from app.config import get_google_settings
from app.web_ui import BASE_STYLES, NARROW_MAIN_STYLES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/google", tags=["auth"])

PROVIDER = "google"
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Verified read-only scopes (see docs/llm_wiki/google_provider_preflight.md §6):
# minimal identity + read-only calendar events. No write/modify/send/full-access.
READ_ONLY_SCOPES = "openid email https://www.googleapis.com/auth/calendar.events.readonly"

_MAX_PENDING_STATES = 1000
_STATE_TTL_SECONDS = 600

_pending_states: Dict[str, tuple[str, datetime]] = {}


class TokenExchangeError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _callback_page(success: bool, title: str, message: str, status_code: int = 200) -> HTMLResponse:
    extra = (
        '<p class="nav"><a href="/calendar">/calendar</a> · <a href="/mail">/mail</a></p>'
        if success
        else '<p class="nav"><a href="/auth/google/login">Try login again</a></p>'
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="color-scheme" content="dark" />
  <title>{title}</title>
  <style>
    {BASE_STYLES}
    {NARROW_MAIN_STYLES}
    h1 {{ color: {"var(--accent)" if success else "var(--warn)"}; }}
  </style>
</head>
<body>
  <main>
    <h1>{title}</h1>
    <p>{message}</p>
    {extra}
  </main>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = _base64url(secrets.token_bytes(32))
    code_challenge = _base64url(hashlib.sha256(code_verifier.encode("ascii")).digest())
    return code_verifier, code_challenge


def _build_authorization_url(state: str, code_challenge: str) -> str:
    settings = get_google_settings()
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "response_type": "code",
            "redirect_uri": settings.google_redirect_uri,
            "scope": READ_ONLY_SCOPES,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            # offline + consent so Google returns a refresh_token.
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return f"{GOOGLE_AUTH_ENDPOINT}?{query}"


async def _exchange_code_for_tokens(code: str, code_verifier: str) -> Dict[str, Any]:
    settings = get_google_settings()
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "redirect_uri": settings.google_redirect_uri,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_TOKEN_ENDPOINT, data=payload)
        if response.is_error:
            logger.error("Google token exchange failed: status=%s", response.status_code)
            raise TokenExchangeError(
                "Google token exchange failed. Verify GOOGLE_* credentials and redirect URI."
            )
        token_data = response.json()

    if "expires_in" in token_data and "expires_at" not in token_data:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(token_data["expires_in"]))
        token_data["expires_at"] = expires_at.isoformat()

    return token_data


def _purge_expired_states() -> None:
    now = datetime.now(timezone.utc)
    expired = [
        s
        for s, (_, created_at) in _pending_states.items()
        if (now - created_at).total_seconds() > _STATE_TTL_SECONDS
    ]
    for s in expired:
        del _pending_states[s]


@router.get("/login")
async def google_login() -> RedirectResponse:
    try:
        get_google_settings()
    except RuntimeError as exc:
        # Google is optional: a clear 503 instead of a 500 when it is not configured.
        raise HTTPException(status_code=503, detail=str(exc))

    _purge_expired_states()
    if len(_pending_states) >= _MAX_PENDING_STATES:
        raise HTTPException(status_code=429, detail="Too many pending auth requests")

    state = secrets.token_urlsafe(16)
    code_verifier, code_challenge = _generate_pkce_pair()
    _pending_states[state] = (code_verifier, datetime.now(timezone.utc))

    return RedirectResponse(url=_build_authorization_url(state, code_challenge), status_code=307)


@router.get("/callback")
async def google_callback(
    code: Optional[str] = None, state: Optional[str] = Query(default=None)
) -> HTMLResponse:
    if not state or state not in _pending_states:
        return _callback_page(
            False,
            "Login failed",
            "Invalid or expired OAuth state. Start a fresh login.",
            status_code=400,
        )
    if not code:
        return _callback_page(
            False,
            "Login failed",
            "Missing authorization code from Google.",
            status_code=400,
        )

    code_verifier, created_at = _pending_states[state]
    now = datetime.now(timezone.utc)
    if (now - created_at).total_seconds() > _STATE_TTL_SECONDS:
        del _pending_states[state]
        return _callback_page(
            False,
            "Login failed",
            "OAuth state has expired. Start login again.",
            status_code=400,
        )

    del _pending_states[state]

    try:
        token_data = await _exchange_code_for_tokens(code, code_verifier)
    except TokenExchangeError as exc:
        return _callback_page(False, "Login failed", exc.message, status_code=502)

    token_store.save_tokens(token_data, provider=PROVIDER)
    logger.info("Google authentication completed")

    return _callback_page(
        True,
        "Login successful",
        "Google authentication completed. Token saved locally.",
    )
