"""Tests for machine-verifiable governance human authority checks."""

from __future__ import annotations

from scripts.verify_governance_authority import _merge_authority_config, evaluate_governance_authority


def _review(
    *,
    login: str,
    state: str,
    commit_id: str = "abc123",
    submitted_at: str = "2026-02-27T00:00:00Z",
    user_type: str = "User",
    review_id: int = 1,
) -> dict:
    return {
        "id": review_id,
        "state": state,
        "commit_id": commit_id,
        "submitted_at": submitted_at,
        "user": {"login": login, "type": user_type},
    }


def _config(**kwargs) -> dict:
    base = {
        "governance_files": ["control_loop/default_policy.json", "control_loop/process_guard.py"],
        "required_approvers": ["svapre"],
        "minimum_approvals": 1,
        "require_approval_on_latest_commit": True,
        "allow_pr_authority_bypass": False,
        "authority_bypass_requires_pr_marker": True,
        "pr_authority_bypass_field": "- Governance authority sign-off:",
        "pr_authority_bypass_token": "OWNER_APPROVED",
        "require_human_reviewers": True,
    }
    base.update(kwargs)
    return base


def test_non_governance_changes_skip_authority_check() -> None:
    fails, warns = evaluate_governance_authority(
        {"README.md"},
        [],
        _config(),
        head_sha="abc123",
        pr_author="svapre",
        pr_body="",
        repo_owner="svapre",
    )
    assert not fails
    assert not warns


def test_required_approver_on_latest_commit_passes() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [_review(login="svapre", state="APPROVED", commit_id="headsha")],
        _config(),
        head_sha="headsha",
        pr_author="agent-user",
        pr_body="",
        repo_owner="svapre",
    )
    assert not fails
    assert not warns


def test_required_approver_old_commit_fails_when_latest_required() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [_review(login="svapre", state="APPROVED", commit_id="oldsha")],
        _config(require_approval_on_latest_commit=True),
        head_sha="headsha",
        pr_author="agent-user",
        pr_body="",
        repo_owner="svapre",
    )
    assert fails
    assert not warns


def test_old_commit_approval_passes_when_latest_not_required() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [_review(login="svapre", state="APPROVED", commit_id="oldsha")],
        _config(require_approval_on_latest_commit=False),
        head_sha="headsha",
        pr_author="agent-user",
        pr_body="",
        repo_owner="svapre",
    )
    assert not fails
    assert not warns


def test_non_required_reviewer_does_not_satisfy_gate() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [_review(login="someoneelse", state="APPROVED", commit_id="headsha")],
        _config(required_approvers=["svapre"]),
        head_sha="headsha",
        pr_author="agent-user",
        pr_body="",
        repo_owner="svapre",
    )
    assert fails
    assert not warns


def test_authority_bypass_allows_owner_self_signoff() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [],
        _config(allow_pr_authority_bypass=True),
        head_sha="headsha",
        pr_author="svapre",
        pr_body="- Governance authority sign-off: OWNER_APPROVED",
        repo_owner="svapre",
    )
    assert not fails
    assert warns


def test_authority_bypass_missing_marker_still_fails() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [],
        _config(allow_pr_authority_bypass=True),
        head_sha="headsha",
        pr_author="svapre",
        pr_body="no marker here",
        repo_owner="svapre",
    )
    assert fails
    assert not warns


def test_authority_bypass_without_marker_passes_when_marker_not_required() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [],
        _config(allow_pr_authority_bypass=True, authority_bypass_requires_pr_marker=False),
        head_sha="headsha",
        pr_author="svapre",
        pr_body="",
        repo_owner="svapre",
    )
    assert not fails
    assert warns


def test_bot_approval_is_ignored_when_human_required() -> None:
    fails, warns = evaluate_governance_authority(
        {"control_loop/default_policy.json"},
        [_review(login="svapre", state="APPROVED", commit_id="headsha", user_type="Bot")],
        _config(require_human_reviewers=True),
        head_sha="headsha",
        pr_author="agent-user",
        pr_body="",
        repo_owner="svapre",
    )
    assert fails
    assert not warns


def test_merge_keeps_base_enabled_rule_active() -> None:
    merged = _merge_authority_config(
        {"enabled": False, "required_approvers": [], "minimum_approvals": 1},
        {
            "enabled": True,
            "required_approvers": ["svapre"],
            "minimum_approvals": 1,
            "require_approval_on_latest_commit": True,
            "require_human_reviewers": True,
            "allow_pr_authority_bypass": False,
        },
    )
    assert merged["enabled"] is True
    assert merged["required_approvers"] == ["svapre"]


def test_merge_uses_current_bypass_settings_in_governance_pr() -> None:
    merged = _merge_authority_config(
        {
            "enabled": True,
            "required_approvers": ["svapre"],
            "minimum_approvals": 1,
            "allow_pr_authority_bypass": True,
            "authority_bypass_requires_pr_marker": False,
        },
        {
            "enabled": True,
            "required_approvers": ["svapre"],
            "minimum_approvals": 1,
            "allow_pr_authority_bypass": False,
            "authority_bypass_requires_pr_marker": True,
        },
    )
    assert merged["allow_pr_authority_bypass"] is True
    assert merged["authority_bypass_requires_pr_marker"] is False
