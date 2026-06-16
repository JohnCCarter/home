"""Runtime metadata helpers: best-effort version lookup and policy-derived safety summary.

No external services, no secrets — version lookup must never raise, even when git is
unavailable.
"""

import subprocess

import app.runtime_metadata as rm
from app.runtime_metadata import resolve_version, safety_summary


def test_version_prefers_home_agent_version_env(monkeypatch):
    monkeypatch.setenv("HOME_AGENT_VERSION", "v1.2.3")
    assert resolve_version() == "v1.2.3"


def test_version_uses_git_commit_env_when_no_home_agent_version(monkeypatch):
    monkeypatch.delenv("HOME_AGENT_VERSION", raising=False)
    monkeypatch.setenv("GIT_COMMIT", "abc1234")
    assert resolve_version() == "abc1234"


def test_version_falls_back_to_unknown_when_git_missing(monkeypatch):
    monkeypatch.delenv("HOME_AGENT_VERSION", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)

    def boom(*args, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(rm.subprocess, "run", boom)
    assert resolve_version() == "unknown"


def test_version_does_not_raise_on_git_error(monkeypatch):
    monkeypatch.delenv("HOME_AGENT_VERSION", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)

    def fail(*args, **kwargs):
        raise subprocess.SubprocessError("boom")

    monkeypatch.setattr(rm.subprocess, "run", fail)
    assert resolve_version() == "unknown"


def test_version_falls_back_to_unknown_on_nonzero_git(monkeypatch):
    monkeypatch.delenv("HOME_AGENT_VERSION", raising=False)
    monkeypatch.delenv("GIT_COMMIT", raising=False)

    class _Result:
        returncode = 128
        stdout = ""

    monkeypatch.setattr(rm.subprocess, "run", lambda *a, **k: _Result())
    assert resolve_version() == "unknown"


def test_safety_summary_matches_policy():
    assert safety_summary() == {
        "read": "allowed",
        "write": "confirmation_required",
        "delete": "forbidden",
    }
