import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


REQUIRED_ENV_VARS = (
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "AZURE_REDIRECT_URI",
)


@dataclass(frozen=True)
class Settings:
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    azure_redirect_uri: str

    @property
    def oauth_authority_base(self) -> str:
        """OAuth v2 base URL. Use AZURE_TENANT_ID=common for personal Microsoft accounts."""
        tenant = self.azure_tenant_id.strip()
        return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0"

def get_settings() -> Settings:
    load_dotenv(dotenv_path=Path(".env"), override=False)

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(f"Missing required environment variables: {missing_list}")

    return Settings(
        azure_tenant_id=os.environ["AZURE_TENANT_ID"],
        azure_client_id=os.environ["AZURE_CLIENT_ID"],
        azure_client_secret=os.environ["AZURE_CLIENT_SECRET"],
        azure_redirect_uri=os.environ["AZURE_REDIRECT_URI"],
    )
