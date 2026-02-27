"""Tests for the constitutional amendment gate in process_guard."""

from __future__ import annotations

from pathlib import Path

from control_loop.process_guard import check_governance_amendment_rule


def _policy(enabled: bool = True, governance_files: list[str] | None = None) -> dict:
    return {
        "governance_amendment_rule": {
            "enabled": enabled,
            "governance_files": governance_files or ["control_loop/default_policy.json"],
            "required_token_field": "- Governance change token:",
            "required_token_value": "GOVERNANCE_CHANGE",
            "review_evidence_field": "- Governance review evidence:",
        }
    }


def _write_session(tmp_path: Path, token: str = "none", evidence: str = "none") -> Path:
    session = tmp_path / "docs" / "sessions" / "2025-01-01-test.md"
    session.parent.mkdir(parents=True)
    session.write_text(
        f"## Results\n"
        f"- Governance change token: {token}\n"
        f"- Governance review evidence: {evidence}\n",
        encoding="utf-8",
    )
    return session


def test_non_governance_file_skips_check(tmp_path: Path) -> None:
    """Regular files are not subject to the constitutional gate."""
    changed = {"scripts/validate_backlog.py", "docs/proposals/PROP-001.md"}
    fails = check_governance_amendment_rule(changed, [], _policy())
    assert not fails


def test_gate_disabled_skips_check(tmp_path: Path) -> None:
    """When gate is disabled (e.g. consumer projects), no check runs."""
    changed = {"control_loop/default_policy.json"}
    fails = check_governance_amendment_rule(changed, [], _policy(enabled=False))
    assert not fails


def test_governance_file_no_session_fails(tmp_path: Path) -> None:
    """Governance file changed but no session log at all → fail."""
    changed = {"control_loop/default_policy.json"}
    fails = check_governance_amendment_rule(changed, [], _policy())
    assert len(fails) == 1
    assert "no session log found" in fails[0]


def test_governance_file_missing_token_fails(tmp_path: Path) -> None:
    """Session exists but has no GOVERNANCE_CHANGE token → fail."""
    session = _write_session(tmp_path, token="none", evidence="Human approved on 2025-01-01")
    changed = {"control_loop/default_policy.json"}
    fails = check_governance_amendment_rule(changed, [str(session)], _policy())
    assert any("GOVERNANCE_CHANGE" in f for f in fails)
    # Evidence was present — only 1 failure (missing token)
    assert len(fails) == 1


def test_governance_file_missing_evidence_fails(tmp_path: Path) -> None:
    """Session has token but no review evidence → fail."""
    session = _write_session(tmp_path, token="GOVERNANCE_CHANGE", evidence="none")
    changed = {"control_loop/default_policy.json"}
    fails = check_governance_amendment_rule(changed, [str(session)], _policy())
    assert any("Governance review evidence" in f for f in fails)
    assert len(fails) == 1


def test_governance_file_with_token_and_evidence_passes(tmp_path: Path) -> None:
    """Session has both token and evidence → gate passes."""
    session = _write_session(
        tmp_path,
        token="GOVERNANCE_CHANGE",
        evidence="Human reviewed on 2025-01-01 via PR comment",
    )
    changed = {"control_loop/default_policy.json"}
    fails = check_governance_amendment_rule(changed, [str(session)], _policy())
    assert not fails


def test_both_token_and_evidence_missing_two_failures(tmp_path: Path) -> None:
    """Session has neither token nor evidence → two separate failures."""
    session = _write_session(tmp_path, token="none", evidence="none")
    changed = {"control_loop/default_policy.json"}
    fails = check_governance_amendment_rule(changed, [str(session)], _policy())
    assert len(fails) == 2
