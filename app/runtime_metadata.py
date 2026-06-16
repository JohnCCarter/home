"""Safe, deterministic runtime metadata for /health and /status.

Everything here is local and static: no external services, no Microsoft login, no
tunnel-client probing, no tokens or secrets. The status endpoints describe what
this process *is*, not whether other services are reachable.

Version lookup is best-effort and never raises — a missing git binary, a non-repo
checkout, or a hang yields ``"unknown"`` rather than failing the status page.
"""

import os
import subprocess

from app.safety.policy import ActionClass, decision_for_class

# Manual reference shown on /status so the user can sanity-check a fresh checkout
# ("if pytest doesn't report this, something drifted"). Bump when the suite changes.
EXPECTED_TEST_COUNT = 129

# Human-readable labels for the policy states surfaced by safety_summary().
_SAFETY_DISPLAY = {
    "allowed": "allowed",
    "confirmation_required": "requires confirmation",
    "forbidden": "forbidden",
}


def resolve_version() -> str:
    """Best-effort commit/version string. Never raises; falls back to ``"unknown"``."""
    for env_var in ("HOME_AGENT_VERSION", "GIT_COMMIT"):
        value = os.environ.get(env_var)
        if value and value.strip():
            return value.strip()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        commit = result.stdout.strip()
        if result.returncode == 0 and commit:
            return commit
    except (OSError, subprocess.SubprocessError):
        pass

    return "unknown"


def safety_summary() -> dict[str, str]:
    """Policy state per action class, derived from app.safety (no duplicated truth)."""
    read = decision_for_class(ActionClass.READ)
    write = decision_for_class(ActionClass.WRITE, confirmed=False)
    delete = decision_for_class(ActionClass.DELETE)
    return {
        "read": "allowed" if read.allowed else "denied",
        "write": write.error_code or ("allowed" if write.allowed else "denied"),
        "delete": "forbidden" if not delete.allowed else "allowed",
    }


def safety_display_label(state: str) -> str:
    """Friendly label for an HTML status page (falls back to the raw state)."""
    return _SAFETY_DISPLAY.get(state, state)
