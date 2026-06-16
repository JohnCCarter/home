"""Tests for runtime UX endpoints (/health, /status) and the start scripts.

All assertions are about static runtime facts — no mailbox, calendar, token, or
secret data is involved.
"""

from pathlib import Path

from starlette.testclient import TestClient

from app.main import app
from app.mcp.schemas import READ_ONLY_TOOL_NAMES

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Substrings that must never appear in a status page or health payload.
SECRET_MARKERS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "CONTROL_PLANE_API_KEY",
    "sk-proj-",
    "sk-",
    "AZURE_CLIENT_SECRET",
)


# --- /health ----------------------------------------------------------------


def test_health_ok_true():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_health_mode_read_only():
    assert client.get("/health").json()["mode"] == "read-only"


def test_health_lists_exactly_three_read_only_tools():
    tools = client.get("/health").json()["tools"]
    assert tools == list(READ_ONLY_TOOL_NAMES)
    assert len(tools) == 3


def test_health_has_no_secret_fields():
    payload = client.get("/health").text
    for marker in SECRET_MARKERS:
        assert marker not in payload


def test_health_includes_version():
    assert "version" in client.get("/health").json()


def test_health_includes_safety_summary():
    safety = client.get("/health").json()["safety"]
    assert safety == {
        "read": "allowed",
        "write": "confirmation_required",
        "delete": "forbidden",
    }


def test_health_has_no_tunnel_ids():
    assert "tunnel_" not in client.get("/health").text


# --- /status -----------------------------------------------------------------


def test_status_returns_html_200():
    response = client.get("/status")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_status_contains_read_only_tools():
    body = client.get("/status").text
    for name in READ_ONLY_TOOL_NAMES:
        assert name in body
    assert "read-only" in body


def test_status_has_no_secrets():
    body = client.get("/status").text
    for marker in SECRET_MARKERS:
        assert marker not in body


def test_status_includes_home_agent_heading():
    assert "Home Agent" in client.get("/status").text


def test_status_includes_mode_read_only():
    assert "read-only" in client.get("/status").text


def test_status_includes_safety_summary():
    body = client.get("/status").text
    assert "allowed" in body          # read
    assert "confirmation" in body     # write requires confirmation
    assert "forbidden" in body        # delete


def test_status_includes_version_field():
    # Field is always present; value is a commit when git is available, else "unknown".
    assert "Git commit / version" in client.get("/status").text


def test_status_has_no_tunnel_ids():
    import re

    body = client.get("/status").text
    assert "tunnel_" not in body
    assert re.search(r"tunnel_[a-z0-9]{32}", body) is None


# --- PowerShell start scripts ------------------------------------------------


def test_start_scripts_exist():
    for name in ("start_rest.ps1", "start_mcp.ps1", "start_tunnel_client.ps1"):
        assert (SCRIPTS_DIR / name).is_file(), f"missing script: {name}"


def test_tunnel_script_has_no_hardcoded_api_key():
    body = (SCRIPTS_DIR / "start_tunnel_client.ps1").read_text(encoding="utf-8")
    # The script must READ the key from .env, never embed one.
    assert "sk-proj-" not in body
    assert "sk-" not in body
    # The literal env-var name appears (it reads it), but no '=<value>' assignment.
    assert 'CONTROL_PLANE_API_KEY="sk' not in body


def test_tunnel_script_is_profile_parametrized():
    body = (SCRIPTS_DIR / "start_tunnel_client.ps1").read_text(encoding="utf-8")
    # Accepts a -Profile parameter, falling back to the TUNNEL_PROFILE env var.
    assert "param(" in body
    assert "$Profile" in body
    assert "$env:TUNNEL_PROFILE" in body
    # Default preserves the original home behavior.
    assert '$Profile = "home-agent"' in body
    # Both doctor and run must use the variable, not a hardcoded profile.
    assert "doctor --profile $Profile" in body
    assert "run --profile $Profile" in body
    # The profile must no longer be hardcoded as the only option.
    assert "--profile home-agent " not in body
    assert "--profile home-agent\n" not in body


# --- write/delete tools must not be exposed ----------------------------------


def test_no_write_or_delete_tools_exposed():
    tools = client.get("/health").json()["tools"]
    for forbidden in ("send_email", "delete_email", "send", "delete", "write", "move", "reply"):
        assert forbidden not in tools
