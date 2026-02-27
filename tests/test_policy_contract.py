import json
from pathlib import Path

import pytest

from control_loop.policy import load_policy


def test_partial_override_merges_with_base(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "partial"},
                "control_gate": {"readiness_tag": "custom-ready"},
            }
        ),
        encoding="utf-8",
    )

    policy = load_policy(repo_root=tmp_path)
    assert policy["control_gate"]["readiness_tag"] == "custom-ready"
    assert "process_guard" in policy


def test_full_override_requires_waiver(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "full"},
                "control_gate": {},
                "process_guard": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="waiver"):
        load_policy(repo_root=tmp_path)


def test_full_override_with_waiver_and_sections_passes(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {
                    "mode": "full",
                    "waiver": {
                        "reason": "non-standard repo layout",
                        "approved_by": "tech-lead",
                        "expires_on": "2026-12-31",
                    },
                },
                "control_gate": {"required_files": [], "readiness_commands": []},
                "process_guard": {"required_process_files": [], "required_proposal_sections": []},
            }
        ),
        encoding="utf-8",
    )

    policy = load_policy(repo_root=tmp_path)
    assert policy["control_gate"]["required_files"] == []


def test_ai_settings_file_override_merges_into_effective_policy(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "partial"},
            }
        ),
        encoding="utf-8",
    )
    (policy_dir / "ai_settings.json").write_text(
        json.dumps(
            {
                "response": {"detail_level": "detailed"},
                "execution": {"confirm_before_changes": True},
            }
        ),
        encoding="utf-8",
    )

    policy = load_policy(repo_root=tmp_path)
    assert policy["ai_settings"]["response"]["detail_level"] == "detailed"
    assert policy["ai_settings"]["execution"]["confirm_before_changes"] is True


def test_disabling_global_switch_requires_waiver_when_required(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "ai_settings.json").write_text(
        json.dumps(
            {
                "global_switch": {
                    "enabled": False,
                    "mode": "strict",
                    "require_waiver_when_disabled": True,
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="waiver"):
        load_policy(repo_root=tmp_path)


def test_default_policy_remains_project_agnostic():
    policy = load_policy()
    project_fields = policy["process_guard"]["project_guideline_fields"]

    assert "- Validation coverage evidence:" in project_fields
    assert "- Single-case exception:" in project_fields
    assert "- Corpus coverage evidence:" not in project_fields
    assert "- Single-document special case:" not in project_fields


def test_base_policy_uses_neutral_implementation_targets(tmp_path: Path):
    policy = load_policy(repo_root=tmp_path)
    process_cfg = policy["process_guard"]
    static_cfg = process_cfg["static_guard_rules"]
    contract_cfg = process_cfg["contract_lifecycle_rules"]
    session_cfg = policy["ai_settings"]["session_log"]

    assert process_cfg["implementation_prefixes"] == []
    assert process_cfg["implementation_files"] == []
    assert static_cfg["include_prefixes"] == []
    assert static_cfg["include_files"] == []
    assert "core/" not in contract_cfg["enforce_prefixes"]
    assert "data_models/" not in contract_cfg["enforce_prefixes"]
    assert "utils/" not in contract_cfg["enforce_prefixes"]
    assert "main.py" not in contract_cfg["enforce_files"]
    assert "core/" not in session_cfg["required_for_prefixes"]
    assert "data_models/" not in session_cfg["required_for_prefixes"]
    assert "utils/" not in session_cfg["required_for_prefixes"]
    assert "main.py" not in session_cfg["required_for_files"]


def test_contract_lifecycle_policy_validation_rejects_invalid_max_commits(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "partial"},
                "process_guard": {
                    "contract_lifecycle_rules": {
                        "enabled": True,
                        "max_commits_since_base": -1,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="max_commits_since_base"):
        load_policy(repo_root=tmp_path)


def test_contract_lifecycle_policy_validation_rejects_unknown_transition_status(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "partial"},
                "process_guard": {
                    "contract_lifecycle_rules": {
                        "enabled": True,
                        "allowed_statuses": ["draft", "approved", "active"],
                        "allowed_transitions": {
                            "approved": ["active", "unknown-status"]
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown target statuses"):
        load_policy(repo_root=tmp_path)


def test_governance_human_authority_rule_rejects_invalid_minimum_approvals(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "partial"},
                "governance_human_authority_rule": {
                    "enabled": True,
                    "minimum_approvals": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="minimum_approvals"):
        load_policy(repo_root=tmp_path)


def test_governance_human_authority_rule_rejects_non_list_approvers(tmp_path: Path):
    policy_dir = tmp_path / ".control-loop"
    policy_dir.mkdir(parents=True)
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "policy_override": {"mode": "partial"},
                "governance_human_authority_rule": {
                    "enabled": True,
                    "required_approvers": "svapre",
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="required_approvers"):
        load_policy(repo_root=tmp_path)

