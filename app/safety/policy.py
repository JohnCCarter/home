"""Centralized safety policy for Home Agent actions.

Single source of truth for whether an action may run:

- **read**   — runs freely
- **write**  — requires an explicit confirmation flag from the caller
- **delete** — forbidden in the MVP

Why confirmation must be **in-band** (a ``confirm`` argument on the call) and not a
server-held "pending confirmation": the MCP HTTP server runs ``stateless_http=True``
(required so the ChatGPT tunnel, which forwards ``tools/call`` without an
``mcp-session-id`` header, does not get HTTP 400). With no session there is nowhere
to remember a pending write between calls, so confirmation MUST travel on the same
call that performs the write. Do not reintroduce session-based, two-phase
confirmation — it breaks the tunnel.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.tools.contracts import ToolErrorCode


class ActionClass(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


# Action name -> class. Unknown actions are never silently allowed: classify()
# returns None and evaluate() denies them. Write/delete tools do not exist yet
# (write is disabled in the MVP) but are listed here so the policy — and its
# tests — describe the full matrix the gate will enforce once they land.
_ACTION_CLASSES: dict[str, ActionClass] = {
    "read_calendar": ActionClass.READ,
    "read_recent_emails": ActionClass.READ,
    "read_email": ActionClass.READ,
}


def classify(action: str) -> Optional[ActionClass]:
    """Return the registered class for ``action``, or ``None`` if unregistered."""
    return _ACTION_CLASSES.get(action)


@dataclass(frozen=True)
class SafetyDecision:
    allowed: bool
    reason: str
    error_code: Optional[ToolErrorCode] = None


def decision_for_class(action_class: ActionClass, confirmed: bool = False) -> SafetyDecision:
    """Decision for a known action class, independent of any registered name.

    Lets callers describe the policy per class (e.g. the /status safety summary)
    without needing a registered action of that class.
    """
    if action_class is ActionClass.READ:
        return SafetyDecision(allowed=True, reason="Read actions run without confirmation.")

    if action_class is ActionClass.DELETE:
        return SafetyDecision(
            allowed=False,
            reason="Delete actions are forbidden in the MVP.",
            error_code="permission_denied",
        )

    # WRITE
    if confirmed:
        return SafetyDecision(allowed=True, reason="Write action confirmed by caller.")
    return SafetyDecision(
        allowed=False,
        reason="Write action requires explicit confirmation (confirm=true).",
        error_code="confirmation_required",
    )


def evaluate(action: str, confirmed: bool = False) -> SafetyDecision:
    """Decide whether ``action`` may run, given an in-band ``confirmed`` flag."""
    action_class = classify(action)
    if action_class is None:
        return SafetyDecision(
            allowed=False,
            reason=f"Unknown action '{action}' is denied by default.",
            error_code="permission_denied",
        )
    return decision_for_class(action_class, confirmed)
