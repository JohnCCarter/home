from dataclasses import asdict, dataclass
from typing import Any, Literal, Optional

from app.providers.base import ProviderApiError

ToolErrorCode = Literal[
    "auth_required",
    "permission_denied",
    "confirmation_required",
    "not_found",
    "rate_limited",
    "provider_error",
    "validation_error",
    "unknown_error",
]


@dataclass(frozen=True)
class ToolError:
    code: ToolErrorCode
    message: str
    retryable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    tool: str
    provider: str
    data: Any
    error: Optional[ToolError]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tool": self.tool,
            "provider": self.provider,
            "data": self.data,
            "error": self.error.to_dict() if self.error else None,
        }


def tool_success(tool: str, provider: str, data: Any) -> ToolResult:
    return ToolResult(ok=True, tool=tool, provider=provider, data=data, error=None)


def tool_failure(tool: str, provider: str, error: ToolError) -> ToolResult:
    return ToolResult(ok=False, tool=tool, provider=provider, data=None, error=error)


def http_status_for_error(code: ToolErrorCode) -> int:
    return {
        "auth_required": 401,
        "permission_denied": 403,
        "confirmation_required": 428,
        "not_found": 404,
        "rate_limited": 429,
        "provider_error": 502,
        "validation_error": 400,
        "unknown_error": 500,
    }.get(code, 500)


def map_graph_error(exc: ProviderApiError) -> ToolError:
    if exc.status_code == 401:
        return ToolError("auth_required", exc.message, retryable=False)
    if exc.status_code == 403:
        return ToolError("permission_denied", exc.message, retryable=False)
    if exc.status_code == 404:
        return ToolError("not_found", exc.message, retryable=False)
    if exc.status_code == 429:
        return ToolError("rate_limited", exc.message, retryable=True)
    if exc.status_code >= 500:
        return ToolError("provider_error", exc.message, retryable=True)
    return ToolError("unknown_error", exc.message, retryable=False)


def map_read_email_graph_error(exc: ProviderApiError) -> ToolError:
    """Map Graph errors for single-message reads (404 and malformed-id 400 → not_found)."""
    if exc.status_code in (400, 404):
        return ToolError("not_found", exc.message, retryable=False)
    return map_graph_error(exc)
