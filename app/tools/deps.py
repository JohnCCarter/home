import os
from typing import Tuple, Union

from app.auth.microsoft import get_valid_tokens
from app.auth.token_store import has_stored_tokens, load_tokens
from app.providers.google_provider import GoogleProvider
from app.providers.mock_provider import MockProvider
from app.providers.outlook_provider import OutlookProvider

# Mail + calendar share this selector — both Outlook and Mock implement both
# interfaces. GoogleProvider is calendar-only and must never reach this union.
Provider = Union[OutlookProvider, MockProvider]

# Calendar-only selector may additionally return GoogleProvider. Kept separate so
# the shared Provider union (which the email path returns) stays honest.
CalendarSelectable = Union[OutlookProvider, GoogleProvider, MockProvider]

# Explicit opt-in: unset/"microsoft" keeps behavior byte-identical to today.
CALENDAR_PROVIDER_ENV = "HOME_AGENT_CALENDAR_PROVIDER"

AUTH_REQUIRED_MESSAGE = (
    "Token expired or refresh failed. Please re-authenticate via /auth/microsoft/login"
)
AUTH_REQUIRED_MESSAGE_GOOGLE = (
    "No valid Google token. Please authenticate via /auth/google/login"
)


class AuthRequiredError(Exception):
    def __init__(self, message: str = AUTH_REQUIRED_MESSAGE) -> None:
        super().__init__(message)
        self.message = message


async def get_provider_with_name() -> Tuple[Provider, str]:
    tokens = await get_valid_tokens()
    access_token = tokens.get("access_token") if tokens else None
    if access_token:
        return OutlookProvider(access_token=access_token), "outlook"
    if has_stored_tokens():
        raise AuthRequiredError()
    return MockProvider(), "mock"


async def get_calendar_provider_with_name() -> Tuple[CalendarSelectable, str]:
    """Calendar provider selection. Default (flag unset/"microsoft") is exactly the
    shared Microsoft/Mock behavior. Only an explicit opt-in selects Google — it never
    wins merely because a Google token exists, and there is no silent Microsoft
    fallback when Google is chosen (fail-fast surfaces auth problems)."""
    choice = os.getenv(CALENDAR_PROVIDER_ENV, "microsoft").strip().lower()

    if choice == "google":
        # No Google refresh flow yet: load_tokens fails closed on expiry, so a stale
        # Google token surfaces as AuthRequiredError rather than a broken provider.
        tokens = load_tokens("google")
        access_token = tokens.get("access_token") if tokens else None
        if access_token:
            return GoogleProvider(access_token=access_token), "google"
        raise AuthRequiredError(AUTH_REQUIRED_MESSAGE_GOOGLE)

    return await get_provider_with_name()
