from __future__ import annotations

from scripts.run_gate_suite import SUITES
from scripts.verify_governance_survival import (
    ANCHOR_PATH_MAP,
    PROFILE_LOCAL_FULL,
    PROFILE_STAGE0_MIN_FLOOR,
    assess_governance_survival,
)


def _policy() -> dict:
    return {
        "governance_human_authority_rule": {
            "enabled": True,
            "governance_files": [
                "control_loop/default_policy.json",
                "control_loop/process_guard.py",
                "control_loop/control_gate.py",
                "control_loop/policy.py",
                "scripts/verify_control_loop.py",
                "scripts/run_gate_suite.py",
                "scripts/verify_governance_authority.py",
                ".github/workflows/ci.yml",
                ".control-loop/policy.json",
                "GOVERNANCE.md",
            ],
            "required_approvers": ["svapre"],
            "minimum_approvals": 1,
            "require_approval_on_latest_commit": True,
            "allow_pr_authority_bypass": True,
            "authority_bypass_requires_pr_marker": False,
            "require_human_reviewers": True,
        },
        "governance_amendment_rule": {
            "enabled": False,
            "governance_files": [
                "control_loop/default_policy.json",
                "control_loop/process_guard.py",
                ".github/workflows/ci.yml",
                ".control-loop/policy.json",
            ],
        },
        "control_loop_integrity": {
            "stage0_check": "warn",
            "stage0_marker": "STAGE0_TAG",
        },
        "process_guard": {
            "static_guard_rules": {
                "enabled": False,
            }
        },
    }


def _ci_text() -> str:
    return "\n".join(
        [
            "name: ci",
            "env:",
            "  STAGE0_TAG: v0.7.0",
            "jobs:",
            "  governance-human-approval:",
            "    environment:",
            "      name: governance-amendment",
            "  stage0-governance:",
            "    steps:",
            "      - run: python /tmp/stage0/scripts/run_gate_suite.py --suite stage0 --target-root \"$GITHUB_WORKSPACE\"",
            "  verify:",
            "    steps:",
            "      - run: python scripts/verify_governance_authority.py --check",
        ]
    )


def _decl(candidate_tier: str = "C2") -> str:
    return "\n".join(
        [
            "## Constitutional Amendment Declaration (interim metadata source)",
            "- Legal object changed: governance runtime behavior",
            "- Affected layer: toolkit project policy",
            f"- Candidate tier: {candidate_tier}",
            "- Expected constitutional effect: additive local-law adjustment",
            "- Draft status: draft",
        ]
    )


def _all_anchor_paths() -> set[str]:
    out: set[str] = set()
    for paths in ANCHOR_PATH_MAP.values():
        out.update(paths)
    return out


def test_c0_anchor_deletion_classifies_c0_and_fails() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {"control_loop/default_policy.json"}
    present = _all_anchor_paths() - {"control_loop/default_policy.json"}

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=present,
    )

    assert result.governance_affecting is True
    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_stage0_human_path_weakening_classifies_c0_and_fails() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {".github/workflows/ci.yml"}
    weak_ci = "\n".join(["name: ci", "jobs:", "  verify:", "    steps:", "      - run: echo noop"])

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=weak_ci,
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
    )

    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_protected_anchor_refactor_escalates_to_c1_not_c2() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {"control_loop/policy.py"}

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
    )

    assert result.passed is True
    assert result.final_tier == "C1"
    assert result.disposition == "ACCEPT_C1_ESCALATED_REVIEW"


def test_additive_local_law_change_can_remain_c2() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {".control-loop/policy.json"}

    # Additive non-protected local law change.
    head["process_guard"]["new_local_law"] = {"enabled": True}

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
    )

    assert result.passed is True
    assert result.final_tier == "C2"
    assert result.disposition == "ACCEPT_C2_AMENDMENT"


def test_trace_payload_fields_are_present() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {".control-loop/policy.json"}

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
    )

    assert isinstance(result.final_tier, str) and result.final_tier
    assert isinstance(result.rationale, list)
    assert isinstance(result.baseline_results, dict)
    assert isinstance(result.disposition, str) and result.disposition


def test_stage0_mode_declaration_scope_is_overlap_only() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {"GOVERNANCE.md"}

    # In local_full mode this is governance-affecting via policy governance_files.
    local_result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        profile=PROFILE_LOCAL_FULL,
    )
    assert local_result.disposition == "REJECT_MISSING_DECLARATION"

    # Stage0 minimum-floor mode should not require declaration for out-of-overlap files.
    stage0_result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        profile=PROFILE_STAGE0_MIN_FLOOR,
    )
    assert stage0_result.disposition == "PASS_NON_GOVERNANCE"
    assert stage0_result.passed is True


def test_stage0_mode_rejects_c0_weakening_in_overlap_scope() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {".github/workflows/ci.yml"}
    weak_ci = "\n".join(["name: ci", "jobs:", "  verify:", "    steps:", "      - run: echo noop"])

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=weak_ci,
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        profile=PROFILE_STAGE0_MIN_FLOOR,
    )

    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_stage0_mode_keeps_minimum_posture_only_not_c1_escalation() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {"control_loop/policy.py"}

    # local_full escalates protected-anchor refactor semantics to C1.
    local_result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        profile=PROFILE_LOCAL_FULL,
    )
    assert local_result.final_tier == "C1"
    assert local_result.disposition == "ACCEPT_C1_ESCALATED_REVIEW"

    # stage0_min_floor keeps only minimum C0 posture checks and does not add C1 semantics.
    stage0_result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        profile=PROFILE_STAGE0_MIN_FLOOR,
    )
    assert stage0_result.final_tier == "C2"
    assert stage0_result.disposition == "ACCEPT_C2_AMENDMENT"
    assert stage0_result.passed is True


def test_local_full_default_profile_behavior_is_preserved() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {"control_loop/policy.py"}

    explicit_local = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        profile=PROFILE_LOCAL_FULL,
    )
    default_profile = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
    )

    assert default_profile.final_tier == explicit_local.final_tier
    assert default_profile.disposition == explicit_local.disposition
    assert default_profile.passed == explicit_local.passed


def test_stage0_suite_includes_survival_min_floor_step() -> None:
    stage0_cmds = SUITES["stage0"]
    assert [
        "python",
        "scripts/verify_governance_survival.py",
        "--check",
        "--profile",
        "stage0_min_floor",
    ] in stage0_cmds

