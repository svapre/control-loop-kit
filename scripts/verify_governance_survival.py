"""Verify constitutional survival non-regression for governance-affecting PRs.

Slice-1 scope:
- Uses STAGE0_TAG as interim enacted-baseline source.
- Uses structured amendment artifacts as primary metadata source.
- Supports optional PR-body declaration overlap consistency checks.
- Keeps semantic anchor categories separate from file/path realizations.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TIER_ORDER = {"C2": 0, "C1": 1, "C0": 2}
TIER_VALUES = set(TIER_ORDER.keys())
PROFILE_LOCAL_FULL = "local_full"
PROFILE_STAGE0_MIN_FLOOR = "stage0_min_floor"
PROFILE_VALUES = {PROFILE_LOCAL_FULL, PROFILE_STAGE0_MIN_FLOOR}

# Semantic anchor categories are stable constitutional concepts.
SEMANTIC_ANCHORS: dict[str, dict[str, str]] = {
    "governance_declaration_scope": {
        "tier": "C0",
        "description": "Governance declaration and scope anchor",
    },
    "universal_baseline_law": {
        "tier": "C0",
        "description": "Universal baseline law anchor",
    },
    "independent_adjudication_wiring": {
        "tier": "C0",
        "description": "Independent adjudication wiring anchor",
    },
    "governance_authority_verification": {
        "tier": "C0",
        "description": "Governance authority verification anchor",
    },
    "governance_integrity_verification": {
        "tier": "C0",
        "description": "Governance integrity verification anchor",
    },
    "governance_enforcement_runtime": {
        "tier": "C0",
        "description": "Executable governance interpretation/enforcement anchor",
    },
    "process_state_contract": {
        "tier": "C1",
        "description": "Canonical process-state contract continuity anchor",
    },
}

# Transitional fallback for historical baselines that do not yet expose
# governance_survival config in policy. Active repos should configure this
# through policy, not by relying on these defaults.
LEGACY_FALLBACK_ANCHOR_PATH_MAP: dict[str, list[str]] = {
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
}

LEGACY_FALLBACK_STAGE0_MIN_FLOOR_CATEGORIES = {
    "governance_declaration_scope",
    "universal_baseline_law",
    "independent_adjudication_wiring",
    "governance_authority_verification",
    "governance_integrity_verification",
    "governance_enforcement_runtime",
}

LEGACY_FALLBACK_CI_WORKFLOW_PATHS = [".github/workflows/ci.yml"]

AMENDMENT_ARTIFACT_DIR = ".control-loop/amendments"
AMENDMENT_SCHEMA_VERSION = "1"
GOVERNANCE_SURVIVAL_KEY = "governance_survival"

DECLARATION_MARKERS = {
    "legal_object_changed": "- Legal object changed:",
    "affected_layer": "- Affected layer:",
    "candidate_tier": "- Candidate tier:",
    "expected_constitutional_effect": "- Expected constitutional effect:",
    "draft_status": "- Draft status:",
}

LEGACY_FALLBACK_CI_SURVIVAL_MARKERS = [
    ("stage0_pin", "STAGE0_TAG"),
    ("human_gate_environment", "governance-amendment"),
    ("stage0_suite_invocation", "--suite stage0"),
    ("authority_check_step", "verify_governance_authority.py --check"),
]

STAGE0_CHECK_ORDER = {"ignore": 0, "warn": 1, "strict": 2}


@dataclass(frozen=True)
class AmendmentDeclaration:
    legal_object_changed: str
    affected_layer: str
    candidate_tier: str
    expected_constitutional_effect: str
    draft_status: str


@dataclass
class AssessmentResult:
    governance_affecting: bool
    declared_tier: str | None
    derived_tier: str
    final_tier: str
    disposition: str
    rationale: list[str]
    declaration_errors: list[str]
    c0_findings: list[str]
    baseline_results: dict[str, dict[str, Any]]
    passed: bool


@dataclass(frozen=True)
class SurvivalConfig:
    anchor_path_map: dict[str, list[str]]
    stage0_min_floor_categories: set[str]
    ci_workflow_paths: set[str]
    ci_survival_markers: list[tuple[str, str]]


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _get_marker_value(text: str, marker: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(marker):
            return line[len(marker) :].strip()
    return ""


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def effective_policy(default_policy: dict[str, Any], project_policy: dict[str, Any]) -> dict[str, Any]:
    override = project_policy.get("policy_override", {})
    mode = "partial"
    if isinstance(override, dict):
        mode = str(override.get("mode", "partial")).strip().lower() or "partial"
    if mode == "full":
        return dict(project_policy)
    return deep_merge(default_policy, project_policy)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            norm = item.strip()
            if norm:
                out.append(norm)
    return out


def _normalize_anchor_path_map(raw: Any) -> dict[str, list[str]]:
    fallback = {
        category: list(paths)
        for category, paths in LEGACY_FALLBACK_ANCHOR_PATH_MAP.items()
    }
    if not isinstance(raw, dict):
        return fallback

    out: dict[str, list[str]] = {}
    any_configured = False
    for category in SEMANTIC_ANCHORS:
        values = _string_list(raw.get(category))
        if values:
            any_configured = True
            out[category] = sorted(set(values))
        elif category in fallback:
            out[category] = list(fallback[category])
        else:
            out[category] = []
    return out if any_configured else fallback


def _normalize_stage0_categories(raw: Any) -> set[str]:
    categories = set(item for item in _string_list(raw) if item in SEMANTIC_ANCHORS)
    if categories:
        return categories
    return set(LEGACY_FALLBACK_STAGE0_MIN_FLOOR_CATEGORIES)


def _normalize_ci_markers(raw: Any) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            marker = str(item.get("marker", "")).strip()
            if name and marker:
                out.append((name, marker))
    if out:
        return out
    return list(LEGACY_FALLBACK_CI_SURVIVAL_MARKERS)


def _normalize_ci_workflow_paths(policy: dict[str, Any], raw: Any) -> set[str]:
    paths = set(_string_list(raw))
    if paths:
        return paths

    integrity = policy.get("control_loop_integrity", {})
    if isinstance(integrity, dict):
        ci_path = str(integrity.get("ci_workflow_path", "")).strip()
        if ci_path:
            return {ci_path}

    return set(LEGACY_FALLBACK_CI_WORKFLOW_PATHS)


def survival_config_from_policy(policy: dict[str, Any]) -> SurvivalConfig:
    raw = policy.get(GOVERNANCE_SURVIVAL_KEY, {})
    cfg = raw if isinstance(raw, dict) else {}
    return SurvivalConfig(
        anchor_path_map=_normalize_anchor_path_map(cfg.get("anchor_paths_by_category")),
        stage0_min_floor_categories=_normalize_stage0_categories(cfg.get("stage0_min_floor_categories")),
        ci_workflow_paths=_normalize_ci_workflow_paths(policy, cfg.get("ci_workflow_paths")),
        ci_survival_markers=_normalize_ci_markers(cfg.get("ci_survival_markers")),
    )


def merge_survival_configs(configs: list[SurvivalConfig]) -> SurvivalConfig:
    merged_map: dict[str, set[str]] = {category: set() for category in SEMANTIC_ANCHORS}
    merged_stage0_categories: set[str] = set()
    merged_ci_paths: set[str] = set()
    merged_markers: list[tuple[str, str]] = []
    seen_markers: set[tuple[str, str]] = set()

    for config in configs:
        for category, paths in config.anchor_path_map.items():
            if category in merged_map:
                merged_map[category].update(paths)
        merged_stage0_categories.update(item for item in config.stage0_min_floor_categories if item in SEMANTIC_ANCHORS)
        merged_ci_paths.update(config.ci_workflow_paths)
        for marker in config.ci_survival_markers:
            if marker not in seen_markers:
                seen_markers.add(marker)
                merged_markers.append(marker)

    if not merged_stage0_categories:
        merged_stage0_categories = set(LEGACY_FALLBACK_STAGE0_MIN_FLOOR_CATEGORIES)
    if not merged_ci_paths:
        merged_ci_paths = set(LEGACY_FALLBACK_CI_WORKFLOW_PATHS)
    if not merged_markers:
        merged_markers = list(LEGACY_FALLBACK_CI_SURVIVAL_MARKERS)

    return SurvivalConfig(
        anchor_path_map={
            category: sorted(paths)
            for category, paths in merged_map.items()
        },
        stage0_min_floor_categories=merged_stage0_categories,
        ci_workflow_paths=merged_ci_paths,
        ci_survival_markers=merged_markers,
    )


def is_amendment_artifact_path(path: str) -> bool:
    p = Path(path)
    if p.suffix.lower() != ".json":
        return False
    return p.parent.as_posix() == AMENDMENT_ARTIFACT_DIR


def amendment_artifact_paths(changed_files: set[str]) -> list[str]:
    return sorted(path for path in changed_files if is_amendment_artifact_path(path))


def load_amendment_artifact_json(
    path: str,
    artifact_payloads: dict[str, dict[str, Any]] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    if artifact_payloads is not None:
        payload = artifact_payloads.get(path)
        if payload is None:
            return None, f"Missing amendment artifact payload for {path}."
        if not isinstance(payload, dict):
            return None, f"Amendment artifact payload for {path} must be a JSON object."
        return payload, None

    full = ROOT / path
    if not full.is_file():
        return None, f"Amendment artifact file not found: {path}"
    try:
        data = json.loads(full.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in amendment artifact {path}: {exc}"
    if not isinstance(data, dict):
        return None, f"Amendment artifact {path} must be a JSON object."
    return data, None


def parse_amendment_declaration_from_text(text: str) -> AmendmentDeclaration | None:
    values = {key: _get_marker_value(text, marker) for key, marker in DECLARATION_MARKERS.items()}
    if not any(values.values()):
        return None
    return AmendmentDeclaration(
        legal_object_changed=values["legal_object_changed"],
        affected_layer=values["affected_layer"],
        candidate_tier=values["candidate_tier"].upper(),
        expected_constitutional_effect=values["expected_constitutional_effect"],
        draft_status=values["draft_status"],
    )


def parse_amendment_declaration_from_artifact(
    path: str,
    data: dict[str, Any],
) -> tuple[AmendmentDeclaration | None, list[str]]:
    failures: list[str] = []
    stem = Path(path).stem

    schema_version = data.get("schema_version")
    if str(schema_version).strip() != AMENDMENT_SCHEMA_VERSION:
        failures.append(
            f"Amendment artifact {path} must set schema_version='{AMENDMENT_SCHEMA_VERSION}'."
        )

    required_fields = [
        "amendment_id",
        "legal_object_changed",
        "affected_layer",
        "candidate_tier",
        "expected_constitutional_effect",
        "draft_status",
    ]
    values: dict[str, str] = {}
    for field in required_fields:
        raw = data.get(field, "")
        if not isinstance(raw, str) or not raw.strip():
            failures.append(f"Amendment artifact field is empty or invalid: {field}")
            values[field] = ""
        else:
            values[field] = raw.strip()

    amendment_id = values.get("amendment_id", "")
    if amendment_id and amendment_id != stem:
        failures.append(
            f"Amendment artifact amendment_id must match filename stem ('{stem}')."
        )

    if failures:
        return None, failures

    return (
        AmendmentDeclaration(
            legal_object_changed=values["legal_object_changed"],
            affected_layer=values["affected_layer"],
            candidate_tier=values["candidate_tier"].upper(),
            expected_constitutional_effect=values["expected_constitutional_effect"],
            draft_status=values["draft_status"],
        ),
        [],
    )


def validate_declaration(decl: AmendmentDeclaration | None) -> list[str]:
    if decl is None:
        return ["Missing constitutional amendment declaration artifact."]
    failures: list[str] = []
    if not decl.legal_object_changed.strip():
        failures.append("Declaration field is empty: legal object changed")
    if not decl.affected_layer.strip():
        failures.append("Declaration field is empty: affected layer")
    if decl.candidate_tier not in TIER_VALUES:
        failures.append(f"Declaration candidate tier must be one of {sorted(TIER_VALUES)}.")
    if not decl.expected_constitutional_effect.strip():
        failures.append("Declaration field is empty: expected constitutional effect")
    status = decl.draft_status.strip().lower()
    if not status:
        failures.append("Declaration field is empty: draft status")
    elif status != "draft":
        failures.append("Declaration draft status must be exactly 'draft'.")
    return failures


def compare_declarations_for_overlap(
    artifact_decl: AmendmentDeclaration,
    pr_decl: AmendmentDeclaration,
) -> list[str]:
    failures: list[str] = []
    checks = [
        (
            "legal object changed",
            artifact_decl.legal_object_changed.strip(),
            pr_decl.legal_object_changed.strip(),
        ),
        ("affected layer", artifact_decl.affected_layer.strip(), pr_decl.affected_layer.strip()),
        ("candidate tier", artifact_decl.candidate_tier.strip().upper(), pr_decl.candidate_tier.strip().upper()),
        (
            "expected constitutional effect",
            artifact_decl.expected_constitutional_effect.strip(),
            pr_decl.expected_constitutional_effect.strip(),
        ),
        ("draft status", artifact_decl.draft_status.strip().lower(), pr_decl.draft_status.strip().lower()),
    ]
    for label, artifact_value, pr_value in checks:
        if artifact_value != pr_value:
            failures.append(
                f"PR-body declaration mismatch with amendment artifact for {label}."
            )
    return failures


def max_tier(left: str, right: str) -> str:
    return left if TIER_ORDER[left] >= TIER_ORDER[right] else right


def governance_files_from_policy(data: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    authority = data.get("governance_human_authority_rule", {})
    if isinstance(authority, dict):
        files = authority.get("governance_files", [])
        if isinstance(files, list):
            out.update({item for item in files if isinstance(item, str) and item.strip()})
    amendment = data.get("governance_amendment_rule", {})
    if isinstance(amendment, dict):
        files = amendment.get("governance_files", [])
        if isinstance(files, list):
            out.update({item for item in files if isinstance(item, str) and item.strip()})
    return out


def anchor_paths_for_tier(tier: str, anchor_path_map: dict[str, list[str]]) -> set[str]:
    paths: set[str] = set()
    for category, meta in SEMANTIC_ANCHORS.items():
        if meta["tier"] == tier:
            paths.update(anchor_path_map.get(category, []))
    return paths


def anchor_paths_for_categories(categories: set[str], anchor_path_map: dict[str, list[str]]) -> set[str]:
    paths: set[str] = set()
    for category in categories:
        paths.update(anchor_path_map.get(category, []))
    return paths


def all_anchor_paths(anchor_path_map: dict[str, list[str]]) -> set[str]:
    out: set[str] = set()
    for paths in anchor_path_map.values():
        out.update(paths)
    return out


def policy_stage0_check_value(policy: dict[str, Any]) -> str:
    integrity = policy.get("control_loop_integrity", {})
    if not isinstance(integrity, dict):
        return "warn"
    value = str(integrity.get("stage0_check", "warn")).lower()
    if value not in STAGE0_CHECK_ORDER:
        return "warn"
    return value


def authority_cfg(policy: dict[str, Any]) -> dict[str, Any]:
    cfg = policy.get("governance_human_authority_rule", {})
    if isinstance(cfg, dict):
        return cfg
    return {}


def check_policy_regression(
    head_policy: dict[str, Any],
    baseline_policy: dict[str, Any],
    baseline_name: str,
    anchor_path_map: dict[str, list[str]],
) -> list[str]:
    findings: list[str] = []
    head_scope = governance_files_from_policy(head_policy)
    base_scope = governance_files_from_policy(baseline_policy)

    # De-scoping of protected C0 anchors from governance scope is survival degradation.
    for path in sorted(anchor_paths_for_tier("C0", anchor_path_map)):
        if path in base_scope and path not in head_scope:
            findings.append(
                f"{baseline_name}: governance scope de-scoped protected C0 path '{path}' from policy governance files."
            )

    base_auth = authority_cfg(baseline_policy)
    head_auth = authority_cfg(head_policy)

    if bool(base_auth.get("enabled", False)) and not bool(head_auth.get("enabled", False)):
        findings.append(f"{baseline_name}: governance human authority rule was disabled.")

    base_min = base_auth.get("minimum_approvals")
    head_min = head_auth.get("minimum_approvals")
    if isinstance(base_min, int) and isinstance(head_min, int) and head_min < base_min:
        findings.append(
            f"{baseline_name}: minimum_approvals weakened from {base_min} to {head_min}."
        )

    for flag in ["require_approval_on_latest_commit", "require_human_reviewers"]:
        if bool(base_auth.get(flag, False)) and not bool(head_auth.get(flag, False)):
            findings.append(f"{baseline_name}: authority safeguard weakened: {flag}=false.")

    if not bool(base_auth.get("allow_pr_authority_bypass", False)) and bool(head_auth.get("allow_pr_authority_bypass", False)):
        findings.append(f"{baseline_name}: authority bypass was enabled (weaker authority posture).")

    base_marker_required = bool(base_auth.get("authority_bypass_requires_pr_marker", True))
    head_marker_required = bool(head_auth.get("authority_bypass_requires_pr_marker", True))
    if base_marker_required and not head_marker_required and bool(head_auth.get("allow_pr_authority_bypass", False)):
        findings.append(
            f"{baseline_name}: authority bypass marker requirement was removed while bypass remains enabled."
        )

    base_stage0 = policy_stage0_check_value(baseline_policy)
    head_stage0 = policy_stage0_check_value(head_policy)
    if STAGE0_CHECK_ORDER[head_stage0] < STAGE0_CHECK_ORDER[base_stage0]:
        findings.append(
            f"{baseline_name}: stage0_check weakened from {base_stage0} to {head_stage0}."
        )

    return findings


def check_ci_regression(
    head_ci_texts: dict[str, str],
    baseline_ci_texts: dict[str, str],
    baseline_name: str,
    ci_markers: list[tuple[str, str]],
) -> list[str]:
    findings: list[str] = []
    head_text = "\n".join(head_ci_texts.values())
    baseline_text = "\n".join(baseline_ci_texts.values())
    for marker_name, marker in ci_markers:
        if marker in baseline_text and marker not in head_text:
            findings.append(
                f"{baseline_name}: CI survival marker removed ({marker_name}: '{marker}')."
            )
    return findings


def governance_affecting_scope(policies: list[dict[str, Any]], anchor_path_map: dict[str, list[str]]) -> set[str]:
    scope: set[str] = set(all_anchor_paths(anchor_path_map))
    for policy in policies:
        scope.update(governance_files_from_policy(policy))
    return scope


def touched_anchor_categories(changed_files: set[str], anchor_path_map: dict[str, list[str]]) -> set[str]:
    touched: set[str] = set()
    for category, paths in anchor_path_map.items():
        if any(path in changed_files for path in paths):
            touched.add(category)
    return touched


def stage0_overlap_scope_paths(config: SurvivalConfig) -> set[str]:
    return anchor_paths_for_categories(
        config.stage0_min_floor_categories,
        config.anchor_path_map,
    )


def resolve_declaration_for_scope(
    *,
    changed_files: set[str],
    governance_affecting: bool,
    pr_body: str,
    artifact_payloads: dict[str, dict[str, Any]] | None,
) -> tuple[AmendmentDeclaration | None, list[str]]:
    if not governance_affecting:
        return None, []

    failures: list[str] = []
    artifact_paths = amendment_artifact_paths(changed_files)
    if len(artifact_paths) != 1:
        failures.append(
            f"Governance-affecting PR must include exactly one amendment artifact under "
            f"{AMENDMENT_ARTIFACT_DIR}/ (found {len(artifact_paths)})."
        )
        return None, failures

    artifact_path = artifact_paths[0]
    artifact_json, load_err = load_amendment_artifact_json(artifact_path, artifact_payloads)
    if load_err:
        return None, [load_err]

    decl, parse_errors = parse_amendment_declaration_from_artifact(artifact_path, artifact_json or {})
    if parse_errors:
        return None, parse_errors

    failures.extend(validate_declaration(decl))

    # Overlap mode: PR-body declaration is optional, but if present it must match.
    pr_decl = parse_amendment_declaration_from_text(pr_body)
    if pr_decl is not None and decl is not None:
        failures.extend(compare_declarations_for_overlap(decl, pr_decl))

    return decl, failures


def derive_tier_signals(
    changed_files: set[str],
    touched_categories: set[str],
    declaration: AmendmentDeclaration | None,
    c0_findings: list[str],
    protected_policy_fields_changed: bool,
) -> tuple[str, list[str]]:
    rationale: list[str] = []
    derived = "C2"

    if c0_findings:
        derived = "C0"
        rationale.append("Detected survival-floor regression findings (C0).")
        return derived, rationale

    # Policy file edits are common for ordinary local-law changes.
    # Escalate only when protected constitutional fields are involved.
    c1_sensitive = {item for item in touched_categories if item != "governance_declaration_scope"}
    if c1_sensitive:
        derived = max_tier(derived, "C1")
        labels = ", ".join(sorted(c1_sensitive))
        rationale.append(f"Touched protected anchor category/categories requiring at least C1: {labels}.")

    if protected_policy_fields_changed:
        derived = max_tier(derived, "C1")
        rationale.append("Governance declaration anchor changed in protected constitutional fields (C1).")

    if declaration is not None:
        effect = declaration.expected_constitutional_effect.strip().lower()
        if "migration" in effect or "refactor" in effect:
            derived = max_tier(derived, "C1")
            rationale.append("Declaration indicates migration/refactor effect (C1).")

    if derived == "C2":
        rationale.append("No C0/C1 effects detected; ordinary governance amendment posture (C2).")

    return derived, rationale


def protected_policy_fields_changed(head_policy: dict[str, Any], baseline_policy: dict[str, Any]) -> bool:
    protected_paths = [
        ("governance_human_authority_rule",),
        ("governance_amendment_rule",),
        ("control_loop_integrity",),
    ]
    for path in protected_paths:
        head_node: Any = head_policy
        base_node: Any = baseline_policy
        for key in path:
            head_node = head_node.get(key, {}) if isinstance(head_node, dict) else {}
            base_node = base_node.get(key, {}) if isinstance(base_node, dict) else {}
        if head_node != base_node:
            return True
    return False


def assess_local_full(
    *,
    changed_files: set[str],
    pr_body: str,
    head_policy: dict[str, Any],
    base_policy: dict[str, Any],
    enacted_policy: dict[str, Any],
    head_ci_texts: dict[str, str],
    base_ci_texts: dict[str, str],
    enacted_ci_texts: dict[str, str],
    head_present_paths: set[str],
    survival_config: SurvivalConfig,
    artifact_payloads: dict[str, dict[str, Any]] | None = None,
) -> AssessmentResult:
    scope = governance_affecting_scope(
        [head_policy, base_policy, enacted_policy],
        survival_config.anchor_path_map,
    )
    governance_affecting = any(path in scope for path in changed_files)

    declaration, declaration_errors = resolve_declaration_for_scope(
        changed_files=changed_files,
        governance_affecting=governance_affecting,
        pr_body=pr_body,
        artifact_payloads=artifact_payloads,
    )
    declared_tier = declaration.candidate_tier if declaration is not None and declaration.candidate_tier in TIER_VALUES else None

    c0_findings: list[str] = []
    baseline_results: dict[str, dict[str, Any]] = {}

    touched_categories = touched_anchor_categories(changed_files, survival_config.anchor_path_map)

    for baseline_name, baseline_policy, baseline_ci_text in [
        ("base", base_policy, base_ci_texts),
        ("enacted", enacted_policy, enacted_ci_texts),
    ]:
        findings = []
        findings.extend(
            check_policy_regression(
                head_policy,
                baseline_policy,
                baseline_name,
                survival_config.anchor_path_map,
            )
        )
        findings.extend(
            check_ci_regression(
                head_ci_texts,
                baseline_ci_text,
                baseline_name,
                survival_config.ci_survival_markers,
            )
        )
        baseline_results[baseline_name] = {
            "status": "fail" if findings else "pass",
            "findings": findings,
        }
        c0_findings.extend(findings)

    # Direct anchor deletion check (current candidate workspace view).
    for path in sorted(anchor_paths_for_tier("C0", survival_config.anchor_path_map)):
        if path in changed_files and path not in head_present_paths:
            c0_findings.append(f"candidate: protected C0 anchor file deleted or missing: {path}")

    # C1 continuity anchor deletion is migration-sensitive escalation (not immediate C0 reject).
    c1_deletion_flag = False
    for path in sorted(anchor_paths_for_tier("C1", survival_config.anchor_path_map)):
        if path in changed_files and path not in head_present_paths:
            c1_deletion_flag = True

    policy_protected_change = protected_policy_fields_changed(head_policy, base_policy) or protected_policy_fields_changed(
        head_policy, enacted_policy
    )

    derived_tier, rationale = derive_tier_signals(
        changed_files,
        touched_categories,
        declaration,
        c0_findings,
        policy_protected_change,
    )

    if c1_deletion_flag and not c0_findings:
        derived_tier = max_tier(derived_tier, "C1")
        rationale.append("Detected C1 continuity anchor deletion signal; migration-sensitive posture required.")

    final_tier = derived_tier
    if declared_tier is not None:
        final_tier = max_tier(final_tier, declared_tier)
        if final_tier != declared_tier:
            rationale.append(f"Auto-escalated from declared tier {declared_tier} to {final_tier} (highest-risk-tier-wins).")

    if not governance_affecting:
        disposition = "PASS_NON_GOVERNANCE"
        passed = True
    elif declaration_errors:
        disposition = "REJECT_MISSING_DECLARATION"
        passed = False
    elif c0_findings:
        disposition = "REJECT_INADMISSIBLE_WEAKENING"
        passed = False
    elif final_tier == "C0":
        disposition = "ACCEPT_C0_HARDENING"
        passed = True
    elif final_tier == "C1":
        disposition = "ACCEPT_C1_ESCALATED_REVIEW"
        passed = True
    else:
        disposition = "ACCEPT_C2_AMENDMENT"
        passed = True

    return AssessmentResult(
        governance_affecting=governance_affecting,
        declared_tier=declared_tier,
        derived_tier=derived_tier,
        final_tier=final_tier,
        disposition=disposition,
        rationale=rationale,
        declaration_errors=declaration_errors,
        c0_findings=c0_findings,
        baseline_results=baseline_results,
        passed=passed,
    )


def assess_stage0_min_floor(
    *,
    changed_files: set[str],
    pr_body: str,
    head_policy: dict[str, Any],
    base_policy: dict[str, Any],
    enacted_policy: dict[str, Any],
    head_ci_texts: dict[str, str],
    base_ci_texts: dict[str, str],
    enacted_ci_texts: dict[str, str],
    head_present_paths: set[str],
    survival_config: SurvivalConfig,
    artifact_payloads: dict[str, dict[str, Any]] | None = None,
) -> AssessmentResult:
    overlap_scope = stage0_overlap_scope_paths(survival_config)
    governance_affecting = any(path in overlap_scope for path in changed_files)

    declaration, declaration_errors = resolve_declaration_for_scope(
        changed_files=changed_files,
        governance_affecting=governance_affecting,
        pr_body=pr_body,
        artifact_payloads=artifact_payloads,
    )
    declared_tier = declaration.candidate_tier if declaration is not None and declaration.candidate_tier in TIER_VALUES else None

    c0_findings: list[str] = []
    baseline_results: dict[str, dict[str, Any]] = {}
    rationale: list[str] = []

    if governance_affecting:
        for baseline_name, baseline_policy, baseline_ci_text in [
            ("base", base_policy, base_ci_texts),
            ("enacted", enacted_policy, enacted_ci_texts),
        ]:
            findings = []
            findings.extend(
                check_policy_regression(
                    head_policy,
                    baseline_policy,
                    baseline_name,
                    survival_config.anchor_path_map,
                )
            )
            findings.extend(
                check_ci_regression(
                    head_ci_texts,
                    baseline_ci_text,
                    baseline_name,
                    survival_config.ci_survival_markers,
                )
            )
            baseline_results[baseline_name] = {
                "status": "fail" if findings else "pass",
                "findings": findings,
            }
            c0_findings.extend(findings)

        for path in sorted(anchor_paths_for_tier("C0", survival_config.anchor_path_map)):
            if path in changed_files and path not in head_present_paths:
                c0_findings.append(f"candidate: protected C0 anchor file deleted or missing: {path}")
    else:
        baseline_results = {
            "base": {"status": "skipped", "findings": []},
            "enacted": {"status": "skipped", "findings": []},
        }

    derived_tier = "C0" if c0_findings else "C2"
    if c0_findings:
        rationale.append("Detected Stage0 minimum-floor C0 regression finding(s).")
    elif governance_affecting:
        rationale.append("No Stage0 minimum-floor C0 degradation detected in overlap scope.")

    final_tier = derived_tier
    if declared_tier is not None:
        final_tier = max_tier(final_tier, declared_tier)
        if final_tier != declared_tier:
            rationale.append(f"Auto-escalated from declared tier {declared_tier} to {final_tier} (highest-risk-tier-wins).")

    if not governance_affecting:
        disposition = "PASS_NON_GOVERNANCE"
        passed = True
    elif declaration_errors:
        disposition = "REJECT_MISSING_DECLARATION"
        passed = False
    elif c0_findings:
        disposition = "REJECT_INADMISSIBLE_WEAKENING"
        passed = False
    elif final_tier == "C0":
        disposition = "ACCEPT_C0_HARDENING"
        passed = True
    else:
        disposition = "ACCEPT_C2_AMENDMENT"
        passed = True

    return AssessmentResult(
        governance_affecting=governance_affecting,
        declared_tier=declared_tier,
        derived_tier=derived_tier,
        final_tier=final_tier,
        disposition=disposition,
        rationale=rationale,
        declaration_errors=declaration_errors,
        c0_findings=c0_findings,
        baseline_results=baseline_results,
        passed=passed,
    )


def assess_governance_survival(
    *,
    changed_files: set[str],
    pr_body: str,
    head_policy: dict[str, Any],
    base_policy: dict[str, Any],
    enacted_policy: dict[str, Any],
    head_ci_texts: dict[str, str] | None = None,
    base_ci_texts: dict[str, str] | None = None,
    enacted_ci_texts: dict[str, str] | None = None,
    head_ci: str | None = None,
    base_ci: str | None = None,
    enacted_ci: str | None = None,
    head_present_paths: set[str] | None = None,
    profile: str = PROFILE_LOCAL_FULL,
    survival_config: SurvivalConfig | None = None,
    artifact_payloads: dict[str, dict[str, Any]] | None = None,
) -> AssessmentResult:
    if survival_config is None:
        survival_config = merge_survival_configs(
            [
                survival_config_from_policy(head_policy),
                survival_config_from_policy(base_policy),
                survival_config_from_policy(enacted_policy),
            ]
        )
    default_ci_path = sorted(survival_config.ci_workflow_paths)[0]
    if head_ci_texts is None:
        head_ci_texts = {default_ci_path: head_ci or ""}
    if base_ci_texts is None:
        base_ci_texts = {default_ci_path: base_ci or ""}
    if enacted_ci_texts is None:
        enacted_ci_texts = {default_ci_path: enacted_ci or ""}
    if head_present_paths is None:
        head_present_paths = present_paths(all_anchor_paths(survival_config.anchor_path_map))

    if profile == PROFILE_LOCAL_FULL:
        return assess_local_full(
            changed_files=changed_files,
            pr_body=pr_body,
            head_policy=head_policy,
            base_policy=base_policy,
            enacted_policy=enacted_policy,
            head_ci_texts=head_ci_texts,
            base_ci_texts=base_ci_texts,
            enacted_ci_texts=enacted_ci_texts,
            head_present_paths=head_present_paths,
            survival_config=survival_config,
            artifact_payloads=artifact_payloads,
        )
    if profile == PROFILE_STAGE0_MIN_FLOOR:
        return assess_stage0_min_floor(
            changed_files=changed_files,
            pr_body=pr_body,
            head_policy=head_policy,
            base_policy=base_policy,
            enacted_policy=enacted_policy,
            head_ci_texts=head_ci_texts,
            base_ci_texts=base_ci_texts,
            enacted_ci_texts=enacted_ci_texts,
            head_present_paths=head_present_paths,
            survival_config=survival_config,
            artifact_payloads=artifact_payloads,
        )
    raise ValueError(f"Unsupported profile: {profile}")


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Missing JSON file: {path.as_posix()}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.as_posix()}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must be an object: {path.as_posix()}")
    return data


def load_json_from_git_ref(ref: str, repo_path: str) -> tuple[dict[str, Any], str | None]:
    rc, out, err = run_command(["git", "show", f"{ref}:{repo_path}"])
    if rc != 0:
        return {}, f"Unable to load {repo_path} from {ref}: {err.strip() or out.strip()}"
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        return {}, f"Invalid JSON in {repo_path} at {ref}: {exc}"
    if not isinstance(data, dict):
        return {}, f"{repo_path} at {ref} is not a JSON object."
    return data, None


def load_text_from_git_ref(ref: str, repo_path: str) -> tuple[str, str | None]:
    rc, out, err = run_command(["git", "show", f"{ref}:{repo_path}"])
    if rc != 0:
        return "", f"Unable to load {repo_path} from {ref}: {err.strip() or out.strip()}"
    return out, None


def load_optional_text_from_git_ref(ref: str, repo_path: str) -> tuple[str | None, str | None]:
    rc, out, err = run_command(["git", "show", f"{ref}:{repo_path}"])
    if rc == 0:
        return out, None

    detail = (err.strip() or out.strip()).lower()
    missing_markers = [
        "does not exist in",
        "exists on disk, but not in",
        "path '",
    ]
    if any(marker in detail for marker in missing_markers):
        return None, None
    return None, f"Unable to load {repo_path} from {ref}: {err.strip() or out.strip()}"


def load_effective_policy_from_workspace() -> tuple[dict[str, Any], str | None]:
    try:
        default_policy = read_json_file(ROOT / "control_loop/default_policy.json")
        project_policy = read_json_file(ROOT / ".control-loop/policy.json")
    except ValueError as exc:
        return {}, str(exc)
    return effective_policy(default_policy, project_policy), None


def load_effective_policy_from_git_ref(ref: str) -> tuple[dict[str, Any], str | None]:
    default_policy, default_err = load_json_from_git_ref(ref, "control_loop/default_policy.json")
    if default_err:
        return {}, default_err
    project_policy, project_err = load_json_from_git_ref(ref, ".control-loop/policy.json")
    if project_err:
        return {}, project_err
    return effective_policy(default_policy, project_policy), None


def load_workspace_texts(paths: set[str]) -> tuple[dict[str, str], str | None]:
    texts: dict[str, str] = {}
    for path in sorted(paths):
        full = ROOT / path
        if not full.is_file():
            continue
        try:
            texts[path] = full.read_text(encoding="utf-8")
        except Exception as exc:
            return {}, f"Unable to load {path} from workspace: {exc}"
    return texts, None


def load_ref_texts(ref: str, paths: set[str]) -> tuple[dict[str, str], str | None]:
    texts: dict[str, str] = {}
    for path in sorted(paths):
        text, err = load_optional_text_from_git_ref(ref, path)
        if err:
            return {}, err
        if text is not None:
            texts[path] = text
    return texts, None


def resolve_enacted_baseline_ref() -> tuple[str | None, str | None]:
    # Isolated baseline-resolution logic for future replacement with enactment register.
    value = os.getenv("STAGE0_TAG", "").strip()
    if not value:
        return None, "Missing STAGE0_TAG for enacted baseline resolution."
    return value, None


def gather_changed_files(base_sha: str, head_sha: str) -> tuple[set[str], str | None]:
    rc, out, err = run_command(["git", "diff", "--name-only", base_sha, head_sha])
    if rc != 0:
        return set(), f"Unable to compute changed files: {err.strip() or out.strip()}"
    changed = {line.strip() for line in out.splitlines() if line.strip()}
    return changed, None


def present_paths(paths: set[str]) -> set[str]:
    return {path for path in paths if (ROOT / path).exists()}


def print_trace(result: AssessmentResult) -> None:
    print(f"TRACE: governance_affecting={result.governance_affecting}")
    print(f"TRACE: declared_tier={result.declared_tier or 'NONE'}")
    print(f"TRACE: derived_tier={result.derived_tier}")
    print(f"TRACE: final_tier={result.final_tier}")
    print(f"TRACE: disposition={result.disposition}")

    if result.rationale:
        print("TRACE: rationale:")
        for item in result.rationale:
            print(f"- {item}")
    if result.declaration_errors:
        print("TRACE: declaration_errors:")
        for item in result.declaration_errors:
            print(f"- {item}")
    if result.c0_findings:
        print("TRACE: c0_findings:")
        for item in result.c0_findings:
            print(f"- {item}")

    print("TRACE: baseline_results:")
    for name, data in result.baseline_results.items():
        print(f"- {name}: {data.get('status', 'unknown')}")
        findings = data.get("findings", [])
        if isinstance(findings, list):
            for finding in findings:
                print(f"  - {finding}")

    payload = {
        "governance_affecting": result.governance_affecting,
        "declared_tier": result.declared_tier,
        "derived_tier": result.derived_tier,
        "final_tier": result.final_tier,
        "disposition": result.disposition,
        "rationale": result.rationale,
        "declaration_errors": result.declaration_errors,
        "c0_findings": result.c0_findings,
        "baseline_results": result.baseline_results,
        "passed": result.passed,
    }
    print("TRACE_JSON: " + json.dumps(payload, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify governance survival non-regression.")
    parser.add_argument("--check", action="store_true", help="Run checks.")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_VALUES),
        default=PROFILE_LOCAL_FULL,
        help=f"Assessment profile (default: {PROFILE_LOCAL_FULL}).",
    )
    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return 0

    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    if event_name not in {"pull_request", "pull_request_target"}:
        print("PASS: governance survival check skipped (non-PR event).")
        return 0

    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path or not Path(event_path).is_file():
        print("FAIL: missing GITHUB_EVENT_PATH for pull_request event.")
        return 1

    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pull_request = event.get("pull_request", {})
    if not isinstance(pull_request, dict):
        print("FAIL: event payload missing pull_request object.")
        return 1

    base_sha = str(((pull_request.get("base") or {}).get("sha")) or "")
    head_sha = str(((pull_request.get("head") or {}).get("sha")) or "")
    if not base_sha or not head_sha:
        print("FAIL: pull_request base/head SHA is missing.")
        return 1

    changed_files, diff_err = gather_changed_files(base_sha, head_sha)
    if diff_err:
        print(f"FAIL: {diff_err}")
        return 1

    enacted_ref, enacted_err = resolve_enacted_baseline_ref()
    if enacted_err:
        print(f"FAIL: {enacted_err}")
        return 1

    head_policy, head_policy_err = load_effective_policy_from_workspace()
    if head_policy_err:
        print(f"FAIL: {head_policy_err}")
        return 1

    base_policy, base_policy_err = load_effective_policy_from_git_ref(base_sha)
    if base_policy_err:
        print(f"FAIL: {base_policy_err}")
        return 1
    enacted_policy, enacted_policy_err = load_effective_policy_from_git_ref(str(enacted_ref))
    if enacted_policy_err:
        print(f"FAIL: {enacted_policy_err}")
        return 1

    survival_config = merge_survival_configs(
        [
            survival_config_from_policy(head_policy),
            survival_config_from_policy(base_policy),
            survival_config_from_policy(enacted_policy),
        ]
    )

    head_ci_texts, head_ci_err = load_workspace_texts(survival_config.ci_workflow_paths)
    if head_ci_err:
        print(f"FAIL: {head_ci_err}")
        return 1

    base_ci_texts, base_ci_err = load_ref_texts(base_sha, survival_config.ci_workflow_paths)
    if base_ci_err:
        print(f"FAIL: {base_ci_err}")
        return 1

    enacted_ci_texts, enacted_ci_err = load_ref_texts(str(enacted_ref), survival_config.ci_workflow_paths)
    if enacted_ci_err:
        print(f"FAIL: {enacted_ci_err}")
        return 1

    pr_body = str(pull_request.get("body", "") or "")
    tracked_anchor_paths = all_anchor_paths(survival_config.anchor_path_map)
    result = assess_governance_survival(
        changed_files=changed_files,
        pr_body=pr_body,
        head_policy=head_policy,
        base_policy=base_policy,
        enacted_policy=enacted_policy,
        head_ci_texts=head_ci_texts,
        base_ci_texts=base_ci_texts,
        enacted_ci_texts=enacted_ci_texts,
        head_present_paths=present_paths(tracked_anchor_paths),
        profile=args.profile,
        survival_config=survival_config,
    )

    print_trace(result)

    if result.passed:
        print("PASS: governance survival verification passed.")
        return 0

    print("FAIL: governance survival verification failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
