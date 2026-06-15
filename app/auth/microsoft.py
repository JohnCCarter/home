import base64
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.auth import token_store
from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/microsoft", tags=["auth"])

_MAX_PENDING_STATES = 1000
_STATE_TTL_SECONDS = 600

_pending_states: Dict[str, tuple[str, datetime]] = {}


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
    return (
        f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/authorize?{query}"
    )


async def _exchange_code_for_tokens(code: str, code_verifier: str) -> Dict[str, Any]:
    settings = get_settings()
    token_url = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/token"
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
        response.raise_for_status()
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
async def microsoft_callback(code: Optional[str] = None, state: Optional[str] = Query(default=None)) -> Dict[str, str]:
    if not state or state not in _pending_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    code_verifier, created_at = _pending_states[state]
    now = datetime.now(timezone.utc)
    if (now - created_at).total_seconds() > _STATE_TTL_SECONDS:
        del _pending_states[state]
        raise HTTPException(status_code=400, detail="OAuth state has expired")

    del _pending_states[state]

    try:
        token_data = await _exchange_code_for_tokens(code, code_verifier)
    except httpx.HTTPError as exc:
        logger.error("Microsoft token exchange failed")
        raise HTTPException(status_code=502, detail="Failed to exchange authorization code") from exc

    token_store.save_tokens(token_data)
    logger.info("Microsoft authentication completed")

    return {"status": "authenticated"}
