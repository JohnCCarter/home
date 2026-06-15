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
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/microsoft", tags=["auth"])

_MAX_PENDING_STATES = 1000
_STATE_TTL_SECONDS = 600

_pending_states: Dict[str, tuple[str, datetime]] = {}


class TokenExchangeError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _callback_page(success: bool, title: str, message: str, status_code: int = 200) -> HTMLResponse:
    color = "#0f766e" if success else "#b45309"
    extra = (
        "<p><a href=\"/calendar\">/calendar</a> · <a href=\"/mail\">/mail</a></p>"
        if success
        else "<p><a href=\"/auth/microsoft/login\">Try login again</a></p>"
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem; }}
    h1 {{ color: {color}; }}
    a {{ color: #1d4ed8; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>{message}</p>
  {extra}
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


def _token_exchange_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "Microsoft token exchange failed. Check Azure app credentials and redirect URI."

    error_codes = body.get("error_codes") or []
    if 7000215 in error_codes:
        return (
            "Invalid client secret. In .env, set AZURE_CLIENT_SECRET to the secret "
            "Value from Entra (shown once at creation), not the Secret ID."
        )
    if body.get("error") == "invalid_grant":
        return "Authorization code expired or already used. Start login again."
    return "Microsoft token exchange failed. Verify Azure app credentials and redirect URI."


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = _base64url(secrets.token_bytes(32))
    code_challenge = _base64url(hashlib.sha256(code_verifier.encode("ascii")).digest())
    return code_verifier, code_challenge


def _build_authorization_url(state: str, code_challenge: str) -> str:
    settings = get_settings()
    query = urlencode(
        {
            "client_id": settings.azure_client_id,
            "response_type": "code",
            "redirect_uri": settings.azure_redirect_uri,
            "response_mode": "query",
            "scope": "offline_access User.Read Mail.Read Calendars.Read",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{settings.oauth_authority_base}/authorize?{query}"


async def _exchange_code_for_tokens(code: str, code_verifier: str) -> Dict[str, Any]:
    settings = get_settings()
    token_url = f"{settings.oauth_authority_base}/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.azure_client_id,
        "client_secret": settings.azure_client_secret,
        "code": code,
        "redirect_uri": settings.azure_redirect_uri,
        "code_verifier": code_verifier,
        "scope": "offline_access User.Read Mail.Read Calendars.Read",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(token_url, data=payload)
        if response.is_error:
            error_codes: list[Any] = []
            try:
                error_codes = response.json().get("error_codes") or []
            except ValueError:
                pass
            logger.error(
                "Microsoft token exchange failed: status=%s error_codes=%s",
                response.status_code,
                error_codes,
            )
            raise TokenExchangeError(_token_exchange_error_message(response))
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
async def microsoft_login() -> RedirectResponse:
    _purge_expired_states()
    if len(_pending_states) >= _MAX_PENDING_STATES:
        raise HTTPException(status_code=429, detail="Too many pending auth requests")
    state = secrets.token_urlsafe(16)
    code_verifier, code_challenge = _generate_pkce_pair()
    _pending_states[state] = (code_verifier, datetime.now(timezone.utc))

    return RedirectResponse(url=_build_authorization_url(state, code_challenge), status_code=307)


@router.get("/callback")
async def microsoft_callback(
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
            "Missing authorization code from Microsoft.",
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

    token_store.save_tokens(token_data)
    logger.info("Microsoft authentication completed")

    return _callback_page(
        True,
        "Login successful",
        "Microsoft authentication completed. Token saved locally.",
    )
