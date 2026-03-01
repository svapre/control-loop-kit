from __future__ import annotations

from scripts.run_gate_suite import SUITES
from scripts.verify_governance_survival import (
    PROFILE_LOCAL_FULL,
    PROFILE_STAGE0_MIN_FLOOR,
    assess_governance_survival,
    survival_config_from_policy,
)

ARTIFACT_PATH = ".control-loop/amendments/2026-03-01-test-amendment.json"


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
        "governance_survival": {
            "anchor_paths_by_category": {
                "governance_declaration_scope": [".control-loop/policy.json"],
                "universal_baseline_law": ["control_loop/default_policy.json"],
                "independent_adjudication_wiring": [
                    ".github/workflows/ci.yml",
                    "scripts/run_gate_suite.py",
                ],
                "governance_authority_verification": ["scripts/verify_governance_authority.py"],
                "governance_integrity_verification": ["scripts/verify_control_loop.py"],
                "governance_enforcement_runtime": [
                    "control_loop/policy.py",
                    "control_loop/control_gate.py",
                    "control_loop/process_guard.py",
                ],
                "process_state_contract": [
                    ".control-loop/backlog.json",
                    ".control-loop/setpoints.json",
                    ".control-loop/contracts.json",
                ],
            },
            "stage0_min_floor_categories": [
                "governance_declaration_scope",
                "universal_baseline_law",
                "independent_adjudication_wiring",
                "governance_authority_verification",
                "governance_integrity_verification",
                "governance_enforcement_runtime",
            ],
            "ci_workflow_paths": [".github/workflows/ci.yml"],
            "ci_survival_markers": [
                {"name": "stage0_pin", "marker": "STAGE0_TAG"},
                {"name": "human_gate_environment", "marker": "governance-amendment"},
                {"name": "stage0_suite_invocation", "marker": "--suite stage0"},
                {"name": "authority_check_step", "marker": "verify_governance_authority.py --check"},
            ],
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


def _all_anchor_paths(policy: dict | None = None) -> set[str]:
    cfg = survival_config_from_policy(policy or _policy())
    out: set[str] = set()
    for paths in cfg.anchor_path_map.values():
        out.update(paths)
    return out


def _artifact_payload(
    *,
    path: str = ARTIFACT_PATH,
    legal_object_changed: str = "governance runtime behavior",
    affected_layer: str = "toolkit project policy",
    candidate_tier: str = "C2",
    expected_constitutional_effect: str = "additive local-law adjustment",
    draft_status: str = "draft",
    schema_version: str = "1",
    amendment_id: str | None = None,
) -> dict[str, dict]:
    stem = path.rsplit("/", 1)[-1].removesuffix(".json")
    return {
        path: {
            "schema_version": schema_version,
            "amendment_id": amendment_id if amendment_id is not None else stem,
            "legal_object_changed": legal_object_changed,
            "affected_layer": affected_layer,
            "candidate_tier": candidate_tier,
            "expected_constitutional_effect": expected_constitutional_effect,
            "draft_status": draft_status,
        }
    }


def _with_artifact(changed: set[str], path: str = ARTIFACT_PATH) -> set[str]:
    return set(changed) | {path}


def test_c0_anchor_deletion_classifies_c0_and_fails() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/default_policy.json"})
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
        artifact_payloads=_artifact_payload(),
    )

    assert result.governance_affecting is True
    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_stage0_human_path_weakening_classifies_c0_and_fails() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({".github/workflows/ci.yml"})
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
        artifact_payloads=_artifact_payload(),
    )

    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_protected_anchor_refactor_escalates_to_c1_not_c2() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

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
        artifact_payloads=_artifact_payload(),
    )

    assert result.passed is True
    assert result.final_tier == "C1"
    assert result.disposition == "ACCEPT_C1_ESCALATED_REVIEW"


def test_additive_local_law_change_can_remain_c2() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({".control-loop/policy.json"})

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
        artifact_payloads=_artifact_payload(),
    )

    assert result.passed is True
    assert result.final_tier == "C2"
    assert result.disposition == "ACCEPT_C2_AMENDMENT"


def test_trace_payload_fields_are_present() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({".control-loop/policy.json"})

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
        artifact_payloads=_artifact_payload(),
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
    changed = _with_artifact({".github/workflows/ci.yml"})
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
        artifact_payloads=_artifact_payload(),
    )

    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_stage0_mode_keeps_minimum_posture_only_not_c1_escalation() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

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
        artifact_payloads=_artifact_payload(),
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
        artifact_payloads=_artifact_payload(),
    )
    assert stage0_result.final_tier == "C2"
    assert stage0_result.disposition == "ACCEPT_C2_AMENDMENT"
    assert stage0_result.passed is True


def test_local_full_default_profile_behavior_is_preserved() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

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
        artifact_payloads=_artifact_payload(),
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
        artifact_payloads=_artifact_payload(),
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


def test_governance_affecting_requires_exactly_one_artifact() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {"control_loop/policy.py"}

    result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
    )
    assert result.disposition == "REJECT_MISSING_DECLARATION"
    assert result.passed is False
    assert any("exactly one amendment artifact" in item for item in result.declaration_errors)


def test_governance_affecting_rejects_multiple_artifacts() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = {
        "control_loop/policy.py",
        ".control-loop/amendments/a.json",
        ".control-loop/amendments/b.json",
    }
    payload = {}
    payload.update(_artifact_payload(path=".control-loop/amendments/a.json"))
    payload.update(_artifact_payload(path=".control-loop/amendments/b.json"))

    result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        artifact_payloads=payload,
    )
    assert result.disposition == "REJECT_MISSING_DECLARATION"
    assert result.passed is False
    assert any("exactly one amendment artifact" in item for item in result.declaration_errors)


def test_artifact_amendment_id_must_match_filename_stem() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

    result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        artifact_payloads=_artifact_payload(amendment_id="different-id"),
    )
    assert result.disposition == "REJECT_MISSING_DECLARATION"
    assert result.passed is False
    assert any("amendment_id must match filename stem" in item for item in result.declaration_errors)


def test_artifact_requires_schema_version_v1() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

    result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        artifact_payloads=_artifact_payload(schema_version="2"),
    )
    assert result.disposition == "REJECT_MISSING_DECLARATION"
    assert result.passed is False
    assert any("schema_version='1'" in item for item in result.declaration_errors)


def test_pr_body_if_present_must_match_artifact() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

    mismatched_pr = "\n".join(
        [
            "## Constitutional Amendment Declaration (interim metadata source)",
            "- Legal object changed: governance runtime behavior",
            "- Affected layer: toolkit project policy",
            "- Candidate tier: C1",
            "- Expected constitutional effect: additive local-law adjustment",
            "- Draft status: draft",
        ]
    )

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=mismatched_pr,
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        artifact_payloads=_artifact_payload(candidate_tier="C2"),
    )
    assert result.disposition == "REJECT_MISSING_DECLARATION"
    assert result.passed is False
    assert any("PR-body declaration mismatch with amendment artifact" in item for item in result.declaration_errors)


def test_policy_driven_anchor_mapping_is_honored() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    custom_path = "runtime/custom_enforcer.py"

    for policy in [head, base, enacted]:
        policy["governance_survival"]["anchor_paths_by_category"]["governance_enforcement_runtime"] = [custom_path]

    changed = _with_artifact({custom_path})
    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(head),
        artifact_payloads=_artifact_payload(),
    )

    assert result.passed is True
    assert result.final_tier == "C1"
    assert result.disposition == "ACCEPT_C1_ESCALATED_REVIEW"


def test_policy_driven_ci_markers_are_honored() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()

    custom_markers = [{"name": "custom_survival_marker", "marker": "MANDATORY_SURVIVAL_MARKER"}]
    for policy in [head, base, enacted]:
        policy["governance_survival"]["ci_survival_markers"] = custom_markers

    changed = _with_artifact({".github/workflows/ci.yml"})
    head_ci = "name: ci\njobs:\n  verify:\n    steps:\n      - run: echo noop"
    baseline_ci = _ci_text() + "\n# MANDATORY_SURVIVAL_MARKER\n"

    result = assess_governance_survival(
        changed_files=changed,
        pr_body=_decl("C2"),
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=head_ci,
        base_ci=baseline_ci,
        enacted_ci=baseline_ci,
        head_present_paths=_all_anchor_paths(head),
        artifact_payloads=_artifact_payload(),
    )

    assert result.final_tier == "C0"
    assert result.disposition == "REJECT_INADMISSIBLE_WEAKENING"
    assert result.passed is False


def test_artifact_draft_status_must_be_exactly_draft() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

    result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        artifact_payloads=_artifact_payload(draft_status="draft-law"),
    )
    assert result.disposition == "REJECT_MISSING_DECLARATION"
    assert result.passed is False
    assert any("draft status must be exactly 'draft'" in item for item in result.declaration_errors)


def test_artifact_optional_fields_are_accepted() -> None:
    head = _policy()
    base = _policy()
    enacted = _policy()
    changed = _with_artifact({"control_loop/policy.py"})

    payload = _artifact_payload()
    payload[ARTIFACT_PATH]["rationale"] = "Narrow channel-hardening change."
    payload[ARTIFACT_PATH]["references"] = ["docs/PROCESS_CHANGELOG.md"]
    payload[ARTIFACT_PATH]["notes"] = "PR-body mirror omitted in overlap mode."

    result = assess_governance_survival(
        changed_files=changed,
        pr_body="",
        head_policy=head,
        base_policy=base,
        enacted_policy=enacted,
        head_ci=_ci_text(),
        base_ci=_ci_text(),
        enacted_ci=_ci_text(),
        head_present_paths=_all_anchor_paths(),
        artifact_payloads=payload,
    )
    assert result.passed is True
    assert result.disposition in {"ACCEPT_C1_ESCALATED_REVIEW", "ACCEPT_C2_AMENDMENT"}

