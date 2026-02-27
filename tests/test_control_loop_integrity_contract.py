"""Tests for the control-loop integrity meta-gate contract."""

from scripts.verify_control_loop import check_ci_wiring


def test_check_ci_wiring_passes_with_valid_workflow(tmp_path):
    # Setup mock CI workflow
    github_dir = tmp_path / ".github" / "workflows"
    github_dir.mkdir(parents=True)
    ci_file = github_dir / "ci.yml"
    ci_file.write_text(
        "name: ci\n"
        "env:\n"
        "  STAGE0_TAG: v0.6.6\n"
        "jobs:\n"
        "  verify:\n"
        "    steps:\n"
        "      - run: python scripts/process_guard.py --mode ci\n"
        "      - run: python scripts/control_gate.py --mode ci\n",
        encoding="utf-8"
    )

    policy = {
        "ci_workflow_path": str(ci_file),
        "required_gate_markers": ["process_guard", "control_gate"],
        "stage0_check": "warn",
        "stage0_marker": "STAGE0_TAG"
    }

    fails, warns = check_ci_wiring(policy)
    assert not fails
    assert not warns


def test_check_ci_wiring_fails_missing_gates(tmp_path):
    github_dir = tmp_path / ".github" / "workflows"
    github_dir.mkdir(parents=True)
    ci_file = github_dir / "ci.yml"
    ci_file.write_text(
        "name: ci\n"
        "env:\n"
        "  STAGE0_TAG: v0.6.6\n",
        encoding="utf-8"
    )

    policy = {
        "ci_workflow_path": str(ci_file),
        "required_gate_markers": ["process_guard", "control_gate"],
        "stage0_check": "ignore"
    }

    fails, warns = check_ci_wiring(policy)
    assert len(fails) == 2
    assert "process_guard" in fails[0]
    assert "control_gate" in fails[1]
    assert not warns


def test_check_ci_wiring_stage0_missing(tmp_path):
    github_dir = tmp_path / ".github" / "workflows"
    github_dir.mkdir(parents=True)
    ci_file = github_dir / "ci.yml"
    ci_file.write_text(
        "name: ci\n"
        "jobs:\n"
        "  verify:\n"
        "    steps:\n"
        "      - run: python scripts/process_guard.py --mode ci\n"
        "      - run: python scripts/control_gate.py --mode ci\n",
        encoding="utf-8"
    )

    # Test warn mode
    policy_warn = {
        "ci_workflow_path": str(ci_file),
        "required_gate_markers": ["process_guard", "control_gate"],
        "stage0_check": "warn",
        "stage0_marker": "STAGE0_TAG"
    }
    fails_warn, warns_warn = check_ci_wiring(policy_warn)
    assert not fails_warn
    assert len(warns_warn) == 1
    assert "STAGE0_TAG" in warns_warn[0]

    # Test strict mode
    policy_strict = dict(policy_warn)
    policy_strict["stage0_check"] = "strict"
    fails_strict, warns_strict = check_ci_wiring(policy_strict)
    assert len(fails_strict) == 1
    assert "STAGE0_TAG" in fails_strict[0]
    assert not warns_strict
