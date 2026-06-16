"""Policy matrix for app/safety: read runs, write needs confirmation, delete is forbidden."""

import pytest

from app.safety import ActionClass, classify, evaluate
from app.safety import policy as policy_module
from app.tools.contracts import http_status_for_error


@pytest.fixture
def with_sample_write_delete(monkeypatch):
    """Register a sample write and delete action (none exist in the MVP registry)."""
    monkeypatch.setitem(policy_module._ACTION_CLASSES, "draft_email", ActionClass.WRITE)
    monkeypatch.setitem(policy_module._ACTION_CLASSES, "delete_email", ActionClass.DELETE)


def test_read_tools_are_classified_read():
    for name in ("read_calendar", "read_recent_emails", "read_email"):
        assert classify(name) is ActionClass.READ


def test_unknown_action_is_unclassified():
    assert classify("totally_made_up") is None


@pytest.mark.parametrize("confirmed", [False, True])
def test_read_runs_without_confirmation(confirmed):
    decision = evaluate("read_calendar", confirmed=confirmed)
    assert decision.allowed is True
    assert decision.error_code is None


def test_unknown_action_is_denied():
    decision = evaluate("totally_made_up")
    assert decision.allowed is False
    assert decision.error_code == "permission_denied"


def test_write_without_confirmation_is_denied(with_sample_write_delete):
    decision = evaluate("draft_email", confirmed=False)
    assert decision.allowed is False
    assert decision.error_code == "confirmation_required"


def test_write_with_confirmation_is_allowed(with_sample_write_delete):
    decision = evaluate("draft_email", confirmed=True)
    assert decision.allowed is True
    assert decision.error_code is None


@pytest.mark.parametrize("confirmed", [False, True])
def test_delete_is_always_forbidden(with_sample_write_delete, confirmed):
    decision = evaluate("delete_email", confirmed=confirmed)
    assert decision.allowed is False
    assert decision.error_code == "permission_denied"


def test_confirmation_required_maps_to_http_428():
    assert http_status_for_error("confirmation_required") == 428
