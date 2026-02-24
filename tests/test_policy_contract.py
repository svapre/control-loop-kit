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

