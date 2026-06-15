"""Pydantic result models for MCP tool output schemas.

These mirror the wire shape produced today by ``ToolResult.to_dict()`` and the
``serialize_*`` helpers (datetime fields are already ISO strings on the wire, so
they are typed as ``str`` here — never ``datetime`` — to preserve the exact bytes).

Annotating the MCP tool functions with these models lets FastMCP generate an
``outputSchema`` (so ChatGPT stops showing "output schema recommended") while still
coercing the plain dicts the tools return into ``structuredContent``.

This module deliberately imports nothing from ``app.tools`` or ``app.providers``:
``app.tools.contracts`` transitively pulls in a provider module, and the MCP layer
must stay provider-agnostic. The error-code Literal is mirrored inline instead.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class ToolErrorModel(BaseModel):
    # Keep in sync with app.tools.contracts.ToolError.code.
    code: Literal[
        "auth_required",
        "permission_denied",
        "not_found",
        "rate_limited",
        "provider_error",
        "validation_error",
        "unknown_error",
    ]
    message: str
    retryable: bool


class CalendarEventModel(BaseModel):
    id: str
    subject: str
    start: str
    end: str


class EmailSummaryModel(BaseModel):
    id: str
    subject: str
    sender: str
    received_at: str


class EmailBodyModel(BaseModel):
    content_type: str
    content: str


class EmailDetailModel(BaseModel):
    id: str
    subject: str
    sender: str
    received_at: str
    body_preview: str
    body: EmailBodyModel


class ReadCalendarResultModel(BaseModel):
    ok: bool
    tool: str
    provider: str
    data: Optional[list[CalendarEventModel]] = None
    error: Optional[ToolErrorModel] = None


class ReadRecentEmailsResultModel(BaseModel):
    ok: bool
    tool: str
    provider: str
    data: Optional[list[EmailSummaryModel]] = None
    error: Optional[ToolErrorModel] = None


class ReadEmailResultModel(BaseModel):
    ok: bool
    tool: str
    provider: str
    data: Optional[EmailDetailModel] = None
    error: Optional[ToolErrorModel] = None
