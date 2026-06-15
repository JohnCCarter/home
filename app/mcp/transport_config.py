"""Dev-only MCP HTTP transport security (DNS rebinding protection)."""

import os
from typing import Iterable

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

MCP_DEV_ALLOWED_HOSTS_ENV = "MCP_DEV_ALLOWED_HOSTS"
MCP_DEV_ALLOWED_ORIGINS_ENV = "MCP_DEV_ALLOWED_ORIGINS"

DEFAULT_LOCAL_HOSTS = ("127.0.0.1:*", "localhost:*", "[::1]:*")
DEFAULT_LOCAL_ORIGINS = (
    "http://127.0.0.1:*",
    "http://localhost:*",
    "http://[::1]:*",
)


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_allowed_hosts(entries: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for entry in entries:
        if "://" in entry:
            continue
        if entry.endswith(":*"):
            normalized.append(entry)
        elif ":" in entry and not entry.startswith("["):
            normalized.append(entry)
        else:
            normalized.append(entry)
            normalized.append(f"{entry}:*")
    return normalized


def _normalize_allowed_origins(entries: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for entry in entries:
        if entry.startswith("http://") or entry.startswith("https://"):
            normalized.append(entry)
            if entry.endswith(":*"):
                continue
            if entry.count(":") == 1:
                normalized.append(f"{entry}:*")
        else:
            normalized.append(f"https://{entry}")
            normalized.append(f"https://{entry}:*")
    return normalized


def build_transport_security(
    bind_host: str = "127.0.0.1",
    extra_allowed_hosts: Iterable[str] | None = None,
    extra_allowed_origins: Iterable[str] | None = None,
) -> TransportSecuritySettings:
    """Build transport security with localhost defaults and optional dev tunnel hosts."""
    env_hosts = _split_csv(os.getenv(MCP_DEV_ALLOWED_HOSTS_ENV, ""))
    env_origins = _split_csv(os.getenv(MCP_DEV_ALLOWED_ORIGINS_ENV, ""))
    cli_hosts = list(extra_allowed_hosts or ())
    cli_origins = list(extra_allowed_origins or ())

    allowed_hosts = list(DEFAULT_LOCAL_HOSTS)
    if bind_host not in ("127.0.0.1", "localhost", "::1"):
        allowed_hosts.append(bind_host)
        allowed_hosts.append(f"{bind_host}:*")

    dev_hosts = env_hosts + cli_hosts
    if dev_hosts:
        allowed_hosts.extend(_normalize_allowed_hosts(dev_hosts))

    allowed_origins = list(DEFAULT_LOCAL_ORIGINS)
    dev_origins = env_origins + cli_origins
    if dev_origins:
        allowed_origins.extend(_normalize_allowed_origins(dev_origins))

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def apply_mcp_transport_security(
    mcp: FastMCP,
    *,
    bind_host: str = "127.0.0.1",
    extra_allowed_hosts: Iterable[str] | None = None,
    extra_allowed_origins: Iterable[str] | None = None,
) -> TransportSecuritySettings:
    settings = build_transport_security(
        bind_host=bind_host,
        extra_allowed_hosts=extra_allowed_hosts,
        extra_allowed_origins=extra_allowed_origins,
    )
    mcp.settings.transport_security = settings
    return settings
