from typing import Tuple, Union

from app.auth.microsoft import get_valid_tokens
from app.auth.token_store import has_stored_tokens
from app.providers.mock_provider import MockProvider
from app.providers.outlook_provider import OutlookProvider

Provider = Union[OutlookProvider, MockProvider]

AUTH_REQUIRED_MESSAGE = (
    "Token expired or refresh failed. Please re-authenticate via /auth/microsoft/login"
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
