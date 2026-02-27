"""Process-governance checks to keep planning and design discipline enforceable."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from control_loop.policy import load_policy


FALLBACK_NON_IMPLEMENTATION_PREFIXES = (
    ".control-loop/",
    "docs/",
    ".github/",
    "tests/",
    "contracts/",
)


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def process_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return policy.get("process_guard", {})


def ai_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return policy.get("ai_settings", {})


def ai_global_switch(policy: dict[str, Any]) -> dict[str, Any]:
    return ai_policy(policy).get("global_switch", {})


def execution_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return ai_policy(policy).get("execution", {})


def session_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return ai_policy(policy).get("session_log", {})


def context_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return ai_policy(policy).get("context_management", {})


def design_rule_config(policy: dict[str, Any]) -> dict[str, Any]:
    return process_policy(policy).get("design_principle_rules", {})


def static_rule_config(policy: dict[str, Any]) -> dict[str, Any]:
    return process_policy(policy).get("static_guard_rules", {})


def phase_rule_config(policy: dict[str, Any]) -> dict[str, Any]:
    return process_policy(policy).get("execution_phase_rules", {})


def contract_rule_config(policy: dict[str, Any]) -> dict[str, Any]:
    return process_policy(policy).get("contract_lifecycle_rules", {})


def governance_rule_config(policy: dict[str, Any]) -> dict[str, Any]:
    return policy.get("governance_amendment_rule", {})


def process_enforcement_state(policy: dict[str, Any]) -> tuple[bool, str]:
    switch = ai_global_switch(policy)
    enabled = bool(switch.get("enabled", True))
    mode = str(switch.get("mode", "strict")).lower()
    if mode not in {"strict", "advisory"}:
        mode = "strict"
    return enabled, mode


def classify_issue(
    enforcement: str,
    message: str,
    failures: list[str],
    warnings: list[str] | None = None,
    manual_reviews: list[str] | None = None,
) -> None:
    normalized = (enforcement or "strict").lower()
    if normalized == "strict":
        failures.append(message)
    elif normalized == "warn":
        if warnings is not None:
            warnings.append(message)
    elif normalized == "manual_review":
        if manual_reviews is not None:
            manual_reviews.append(message)
        elif warnings is not None:
            warnings.append(message)
    else:
        failures.append(f"Invalid enforcement level '{enforcement}' for issue: {message}")


def check_required_process_files(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = process_policy(policy).get("required_process_files", [])
    for file_path in required:
        if not Path(file_path).exists():
            failures.append(f"Missing process artifact: {file_path}")
    context_index_path = context_policy(policy).get("context_index_path")
    if isinstance(context_index_path, str) and context_index_path and not Path(context_index_path).exists():
        failures.append(f"Missing context index artifact: {context_index_path}")
    return failures


def resolve_base_sha(base_sha: str | None, policy: dict[str, Any]) -> str | None:
    if base_sha and not base_sha.startswith("000000"):
        return base_sha

    default_branch = process_policy(policy).get("default_branch", "master")
    rc_merge_base, out_merge_base, _ = run_command(["git", "merge-base", "HEAD", f"origin/{default_branch}"])
    if rc_merge_base == 0 and out_merge_base:
        return out_merge_base

    rc, out, _ = run_command(["git", "rev-parse", "HEAD^"])
    if rc == 0 and out:
        return out
    return None


def get_uncommitted_files(warnings: list[str]) -> set[str]:
    changed: set[str] = set()
    commands = [
        ["git", "diff", "--name-only"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    for cmd in commands:
        rc, out, err = run_command(cmd)
        if rc != 0:
            warnings.append(f"Unable to inspect local changes via {' '.join(cmd)}: {err or out}")
            continue
        changed.update({line.strip() for line in out.splitlines() if line.strip()})
    return changed


def get_changed_files(base_sha: str | None, policy: dict[str, Any]) -> tuple[set[str], list[str]]:
    warnings: list[str] = []
    changed: set[str] = set()
    resolved = resolve_base_sha(base_sha, policy)

    if resolved:
        rc, out, err = run_command(["git", "diff", "--name-only", resolved, "HEAD"])
        if rc != 0:
            warnings.append(f"Unable to compute changed files against base SHA: {err or out}")
        else:
            changed.update({line.strip() for line in out.splitlines() if line.strip()})
    else:
        warnings.append("Could not determine base SHA for commit-diff checks; using worktree changes only.")

    changed.update(get_uncommitted_files(warnings))
    return changed, warnings


def is_fallback_implementation_path(path: str) -> bool:
    if not path:
        return False
    return not any(path.startswith(prefix) for prefix in FALLBACK_NON_IMPLEMENTATION_PREFIXES)


def is_implementation_path(path: str, policy: dict[str, Any]) -> bool:
    exact_files = set(process_policy(policy).get("implementation_files", []))
    prefixes = tuple(process_policy(policy).get("implementation_prefixes", []))
    if exact_files or prefixes:
        return path in exact_files or any(path.startswith(prefix) for prefix in prefixes)
    return is_fallback_implementation_path(path)


def is_toolkit_path(path: str, policy: dict[str, Any]) -> bool:
    cfg = phase_rule_config(policy)
    prefixes = tuple(cfg.get("toolkit_prefixes", ["tooling/control-loop-kit"]))
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in prefixes)


def is_session_trigger_path(path: str, policy: dict[str, Any]) -> bool:
    cfg = session_policy(policy)
    exact_files = set(cfg.get("required_for_files", []))
    prefixes = tuple(cfg.get("required_for_prefixes", []))
    if exact_files or prefixes:
        return path in exact_files or any(path.startswith(prefix) for prefix in prefixes)
    return is_implementation_path(path, policy)


def static_scan_target(path: str, policy: dict[str, Any]) -> bool:
    cfg = static_rule_config(policy)
    if not cfg.get("enabled", False):
        return False

    include_prefixes = tuple(cfg.get("include_prefixes", process_policy(policy).get("implementation_prefixes", [])))
    include_files = set(cfg.get("include_files", process_policy(policy).get("implementation_files", [])))
    scan_extensions = {ext.lower() for ext in cfg.get("scan_extensions", [".py"])}

    if include_files or include_prefixes:
        target = path in include_files or any(path.startswith(prefix) for prefix in include_prefixes)
    else:
        target = is_implementation_path(path, policy)

    if not target:
        return False
    suffix = Path(path).suffix.lower()
    return suffix in scan_extensions


def get_changed_proposal_files(changed_files: set[str], policy: dict[str, Any]) -> list[str]:
    proposal_root = process_policy(policy).get("proposal_root", "docs/proposals/")
    ignored = set(process_policy(policy).get("proposal_ignored_files", []))
    return sorted([path for path in changed_files if path.startswith(proposal_root) and path not in ignored])


def get_changed_session_files(changed_files: set[str], policy: dict[str, Any]) -> list[str]:
    cfg = session_policy(policy)
    session_root = cfg.get("root", "docs/sessions/")
    ignored = set(cfg.get("ignored_files", []))
    return sorted([path for path in changed_files if path.startswith(session_root) and path not in ignored])


def get_required_proposal_fields(policy: dict[str, Any]) -> list[str]:
    process_cfg = process_policy(policy)
    combined: list[str] = []
    for key in ["required_proposal_fields", "process_guideline_fields", "project_guideline_fields"]:
        combined.extend(process_cfg.get(key, []))

    deduped: list[str] = []
    seen: set[str] = set()
    for item in combined:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def get_marker_value(text: str, marker: str) -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(marker.lower()):
            return line.split(":", 1)[1].strip() if ":" in line else ""
    return ""


def is_null_marker_value(value: str, policy: dict[str, Any]) -> bool:
    null_tokens = set(session_policy(policy).get("null_tokens", ["none", "n/a", "na", ""]))
    return value.strip().lower() in {token.lower() for token in null_tokens}


def is_null_text_value(value: str, null_tokens: set[str]) -> bool:
    return value.strip().lower() in null_tokens


def check_mode_rule(text: str, proposal_file: str, policy: dict[str, Any]) -> list[str]:
    rule = process_policy(policy).get("mode_rule", {})
    if not rule.get("enabled", False):
        return []

    mode_marker = rule.get("selected_mode_field", "- Selected work mode:")
    allowed = {item.lower() for item in rule.get("allowed_modes", ["routine", "design"])}
    selected = get_marker_value(text, mode_marker).lower()
    if not selected:
        return [f"Proposal {proposal_file} has empty selected mode field: {mode_marker}"]
    if selected not in allowed:
        return [f"Proposal {proposal_file} mode '{selected}' not allowed; expected one of {sorted(allowed)}"]
    return []


def check_no_assumption_rule(text: str, proposal_file: str, policy: dict[str, Any]) -> list[str]:
    rule = process_policy(policy).get("no_assumption_rule", {})
    if not rule.get("enabled", False):
        return []

    assumptions_marker = rule.get("assumptions_field", "- Assumptions made:")
    confirm_required_marker = rule.get(
        "confirmation_required_field", "- User confirmation required before implementation:"
    )
    evidence_marker = rule.get("confirmation_evidence_field", "- User confirmation evidence:")

    assumptions = get_marker_value(text, assumptions_marker)
    confirm_required = get_marker_value(text, confirm_required_marker).lower()
    evidence = get_marker_value(text, evidence_marker)

    failures: list[str] = []
    if not assumptions:
        failures.append(f"Proposal {proposal_file} has empty assumptions field: {assumptions_marker}")

    assumptions_is_none = assumptions.lower() in {"none", "n/a", "na"}
    confirmation_is_yes = confirm_required in {"yes", "true"}
    confirmation_is_no = confirm_required in {"no", "false"}

    if not confirmation_is_yes and not confirmation_is_no:
        failures.append(
            f"Proposal {proposal_file} must set {confirm_required_marker} to yes/no (or true/false)."
        )

    if not assumptions_is_none and not confirmation_is_yes:
        failures.append(
            f"Proposal {proposal_file} lists assumptions but does not require user confirmation."
        )

    if confirmation_is_yes and evidence.lower() in {"", "none", "n/a", "na"}:
        failures.append(
            f"Proposal {proposal_file} requires confirmation but has empty evidence marker: {evidence_marker}"
        )

    return failures


def check_design_principle_rules(
    text: str,
    proposal_file: str,
    policy: dict[str, Any],
    warnings: list[str] | None = None,
    manual_reviews: list[str] | None = None,
) -> list[str]:
    cfg = design_rule_config(policy)
    rules = cfg.get("required_value_rules", [])
    null_tokens = {token.lower() for token in cfg.get("null_tokens", ["", "none", "n/a", "na", "tbd", "todo"])}
    manual_evidence_field = cfg.get("manual_review_evidence_field", "- Manual review evidence:")

    failures: list[str] = []
    for item in rules:
        if not isinstance(item, dict):
            failures.append(f"Invalid design rule entry in policy: {item}")
            continue

        field = item.get("field")
        enforcement = str(item.get("enforcement", "strict")).lower()
        if not isinstance(field, str) or not field.strip():
            failures.append(f"Invalid design rule field marker in policy entry: {item}")
            continue

        value = get_marker_value(text, field)
        is_null = is_null_text_value(value, null_tokens)

        if enforcement in {"strict", "warn"} and is_null:
            classify_issue(
                enforcement,
                f"Proposal {proposal_file} has empty design evidence field: {field}",
                failures,
                warnings,
                manual_reviews,
            )
            continue

        if enforcement == "manual_review" and not is_null:
            classify_issue(
                "manual_review",
                f"Proposal {proposal_file} includes special-case evidence in {field}; manual review required.",
                failures,
                warnings,
                manual_reviews,
            )
            evidence = get_marker_value(text, manual_evidence_field)
            if is_null_text_value(evidence, null_tokens):
                failures.append(
                    f"Proposal {proposal_file} requires manual review evidence but has empty field: {manual_evidence_field}"
                )

    return failures


def check_proposal_sections(
    proposal_files: list[str],
    policy: dict[str, Any],
    warnings: list[str] | None = None,
    manual_reviews: list[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    required_sections = process_policy(policy).get("required_proposal_sections", [])
    required_fields = get_required_proposal_fields(policy)

    for path in proposal_files:
        proposal_path = Path(path)
        if not proposal_path.exists():
            failures.append(f"Proposal file is referenced in changes but not found: {path}")
            continue

        text = proposal_path.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                failures.append(f"Proposal {path} missing required section: {section}")
        for field in required_fields:
            if field not in text:
                failures.append(f"Proposal {path} missing required field marker: {field}")

        failures.extend(check_mode_rule(text, path, policy))
        failures.extend(check_no_assumption_rule(text, path, policy))
        failures.extend(check_design_principle_rules(text, path, policy, warnings, manual_reviews))

    return failures


def check_session_approval_rule(text: str, session_file: str, policy: dict[str, Any]) -> list[str]:
    cfg = session_policy(policy)
    exec_cfg = execution_policy(policy)

    status_marker = cfg.get("user_approval_status_field", "- User approval status:")
    evidence_marker = cfg.get("user_approval_evidence_field", "- User approval evidence:")

    status = get_marker_value(text, status_marker).strip().lower()
    evidence = get_marker_value(text, evidence_marker).strip()

    failures: list[str] = []
    confirm_before_changes = bool(exec_cfg.get("confirm_before_changes", False))
    approved_tokens = {"yes", "true"}
    rejected_tokens = {"no", "false"}

    if not status:
        failures.append(f"Session {session_file} has empty approval status field: {status_marker}")
    elif status not in approved_tokens and status not in rejected_tokens:
        failures.append(f"Session {session_file} must set {status_marker} to yes/no (or true/false).")

    if confirm_before_changes and status not in approved_tokens:
        failures.append(
            f"Session {session_file} requires explicit user approval before changes, but status is not approved."
        )

    if status in approved_tokens and is_null_marker_value(evidence, policy):
        failures.append(
            f"Session {session_file} shows approved status but has empty approval evidence field: {evidence_marker}"
        )

    return failures


def check_session_failure_correction_rule(text: str, session_file: str, policy: dict[str, Any]) -> list[str]:
    cfg = session_policy(policy)
    failure_marker = cfg.get("failure_observed_field", "- Failure observed:")
    corrective_marker = cfg.get("corrective_change_field", "- Corrective change made:")

    failure_value = get_marker_value(text, failure_marker)
    corrective_value = get_marker_value(text, corrective_marker)

    if not is_null_marker_value(failure_value, policy) and is_null_marker_value(corrective_value, policy):
        return [
            f"Session {session_file} records a failure but does not record a corrective change before retry."
        ]
    return []


def check_session_sections(session_files: list[str], policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cfg = session_policy(policy)
    required_sections = cfg.get("required_sections", [])
    required_fields = cfg.get("required_fields", [])

    for path in session_files:
        session_path = Path(path)
        if not session_path.exists():
            failures.append(f"Session file is referenced in changes but not found: {path}")
            continue

        text = session_path.read_text(encoding="utf-8")
        for section in required_sections:
            if section not in text:
                failures.append(f"Session {path} missing required section: {section}")
        for field in required_fields:
            if field not in text:
                failures.append(f"Session {path} missing required field marker: {field}")

        failures.extend(check_session_approval_rule(text, path, policy))
        failures.extend(check_session_failure_correction_rule(text, path, policy))

    return failures


def path_matches_rule(path: str, rule: str) -> bool:
    normalized = rule.strip()
    if not normalized:
        return False
    if normalized.endswith("/"):
        return path.startswith(normalized)
    if path == normalized:
        return True
    return path.startswith(f"{normalized}/")


def path_matches_any(path: str, rules: list[str]) -> bool:
    return any(path_matches_rule(path, rule) for rule in rules)


def check_static_guard_rules(
    changed_files: set[str],
    policy: dict[str, Any],
    warnings: list[str] | None = None,
    manual_reviews: list[str] | None = None,
) -> list[str]:
    cfg = static_rule_config(policy)
    if not cfg.get("enabled", False):
        return []

    failures: list[str] = []
    rules = cfg.get("rules", [])
    compiled_rules: list[tuple[str, str, str, re.Pattern[str]]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            failures.append(f"Invalid static guard rule entry in policy: {rule}")
            continue
        name = str(rule.get("name", "unnamed-rule"))
        pattern = rule.get("pattern")
        enforcement = str(rule.get("enforcement", "strict")).lower()
        message = str(rule.get("message", "Static guard rule matched."))
        if not isinstance(pattern, str) or not pattern:
            failures.append(f"Static guard rule {name} has invalid regex pattern.")
            continue
        flags = re.IGNORECASE if bool(rule.get("ignore_case", False)) else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as exc:
            failures.append(f"Static guard rule {name} has invalid regex: {exc}")
            continue
        compiled_rules.append((name, enforcement, message, regex))

    for path in sorted(changed_files):
        if not static_scan_target(path, policy):
            continue
        file_path = Path(path)
        if not file_path.exists():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception:
            failures.append(f"Unable to read file for static guard scan: {path}")
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for name, enforcement, message, regex in compiled_rules:
                if regex.search(line):
                    classify_issue(
                        enforcement,
                        f"{path}:{line_no}: [{name}] {message}",
                        failures,
                        warnings,
                        manual_reviews,
                    )

    return failures


def resolve_primary_session_file(session_files: list[str]) -> Path | None:
    if not session_files:
        return None
    return Path(sorted(session_files)[-1])


def check_phase_scope_rules(
    changed_files: set[str],
    session_files: list[str],
    policy: dict[str, Any],
    run_mode: str,
) -> list[str]:
    cfg = phase_rule_config(policy)
    if not cfg.get("enabled", False):
        return []

    failures: list[str] = []
    implementation_changed = any(is_implementation_path(path, policy) for path in changed_files)
    toolkit_changed = any(is_toolkit_path(path, policy) for path in changed_files)
    if not implementation_changed and not toolkit_changed:
        return failures

    phase_field = cfg.get("phase_field", "- Workflow phase:")
    scope_field = cfg.get("change_scope_field", "- Change scope:")
    token_field = cfg.get("implementation_approval_token_field", "- Implementation approval token:")
    required_token = cfg.get("required_implementation_approval_token", "APPROVE_IMPLEMENT")
    allowed_phases = {item.lower() for item in cfg.get("allowed_phases", ["think", "implement"])}
    allowed_scopes = {item.lower() for item in cfg.get("allowed_scopes", ["project", "toolkit", "both"])}

    primary_session = resolve_primary_session_file(session_files)
    if primary_session is None:
        failures.append("Implementation/toolkit changes require a session log update.")
        return failures
    if not primary_session.exists():
        failures.append(f"Primary session file not found: {primary_session.as_posix()}")
        return failures

    text = primary_session.read_text(encoding="utf-8")
    phase = get_marker_value(text, phase_field).lower()
    scope = get_marker_value(text, scope_field).lower()
    token = get_marker_value(text, token_field)

    if phase not in allowed_phases:
        failures.append(
            f"Session {primary_session.as_posix()} has invalid phase '{phase}'. "
            f"Expected one of {sorted(allowed_phases)}."
        )
        return failures

    if run_mode == "think":
        if phase != "think":
            failures.append(
                f"Session {primary_session.as_posix()} must declare think phase when running --mode think."
            )
        failures.append(
            "Think mode detected implementation/toolkit changes. "
            "Use planning/docs only in think mode, or switch to implement phase."
        )
        return failures

    if phase != "implement":
        failures.append(
            f"Session {primary_session.as_posix()} must declare implement phase for implementation/toolkit changes."
        )
    if token != required_token:
        failures.append(
            f"Session {primary_session.as_posix()} is missing required implementation approval token in {token_field}"
        )

    if scope not in allowed_scopes:
        failures.append(
            f"Session {primary_session.as_posix()} has invalid scope '{scope}'. "
            f"Expected one of {sorted(allowed_scopes)}."
        )
        return failures

    if implementation_changed and scope not in {"project", "both"}:
        failures.append(
            f"Session {primary_session.as_posix()} scope '{scope}' is invalid for project implementation changes."
        )
    if toolkit_changed and scope not in {"toolkit", "both"}:
        failures.append(
            f"Session {primary_session.as_posix()} scope '{scope}' is invalid for toolkit changes."
        )

    return failures


def contract_target_paths(changed_files: set[str], policy: dict[str, Any]) -> list[str]:
    cfg = contract_rule_config(policy)
    enforce_prefixes = cfg.get(
        "enforce_prefixes",
        process_policy(policy).get("implementation_prefixes", []),
    )
    enforce_files = cfg.get("enforce_files", process_policy(policy).get("implementation_files", []))
    ignore_prefixes = cfg.get("ignore_prefixes", [])
    ignore_files = cfg.get("ignore_files", [])

    targets: list[str] = []
    use_fallback = not enforce_files and not enforce_prefixes
    for path in sorted(changed_files):
        if path in ignore_files or path_matches_any(path, ignore_prefixes):
            continue
        if use_fallback and is_implementation_path(path, policy):
            targets.append(path)
            continue
        if path in enforce_files or path_matches_any(path, enforce_prefixes):
            targets.append(path)
    return targets


def load_contracts_file(contract_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not contract_path.exists():
        return None, [f"Missing contract lifecycle file: {contract_path.as_posix()}"]
    try:
        data = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON in contract lifecycle file {contract_path.as_posix()}: {exc}"]
    if not isinstance(data, dict):
        return None, [f"Contract lifecycle file must be an object: {contract_path.as_posix()}"]
    return data, failures


def normalize_contract_list(raw: Any, contract_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    failures: list[str] = []
    if not isinstance(raw, list):
        return [], [f"Contract lifecycle file {contract_path.as_posix()} must define 'contracts' as an array."]
    contracts: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            failures.append(f"contracts[{idx}] in {contract_path.as_posix()} must be an object.")
            continue
        contracts.append(item)
    return contracts, failures


def resolve_contract_repo_path(contract_path: Path) -> str:
    if not contract_path.is_absolute():
        return contract_path.as_posix()
    try:
        relative = contract_path.relative_to(Path.cwd())
        return relative.as_posix()
    except ValueError:
        return contract_path.as_posix()


def load_contracts_from_git_ref(base_sha: str, contract_repo_path: str) -> tuple[list[dict[str, Any]], list[str], bool]:
    """Load contracts file content from a previous git ref.

    Returns: (contracts, failures, exists_in_base)
    """
    rc, out, err = run_command(["git", "show", f"{base_sha}:{contract_repo_path}"])
    if rc != 0:
        detail = (err or out or "").lower()
        # Missing in base can be valid for first introduction of contracts.
        if "does not exist" in detail or "exists on disk" in detail or "path '" in detail:
            return [], [], False
        return [], [
            f"Unable to load contract lifecycle file from base commit '{base_sha}': {err or out}"
        ], False

    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        return [], [f"Invalid JSON in base contract file {contract_repo_path}: {exc}"], True
    if not isinstance(data, dict):
        return [], [f"Base contract file must be an object: {contract_repo_path}"], True

    contracts, failures = normalize_contract_list(data.get("contracts"), Path(contract_repo_path))
    return contracts, failures, True


def contracts_status_map(contracts: list[dict[str, Any]]) -> tuple[dict[str, str], list[str]]:
    status_by_id: dict[str, str] = {}
    failures: list[str] = []
    for idx, item in enumerate(contracts):
        contract_id = str(item.get("id", "")).strip()
        if not contract_id:
            failures.append(f"contracts[{idx}] is missing id.")
            continue
        if contract_id in status_by_id:
            failures.append(f"Duplicate contract id in lifecycle file: {contract_id}")
            continue
        status_by_id[contract_id] = str(item.get("status", "")).strip().lower()
    return status_by_id, failures


def check_contract_transition_rules(
    changed_files: set[str],
    contracts_current: list[dict[str, Any]],
    contract_repo_path: str,
    cfg: dict[str, Any],
    base_sha: str | None,
    warnings: list[str] | None = None,
) -> list[str]:
    failures: list[str] = []
    if not bool(cfg.get("enforce_transition_on_contract_change", False)):
        return failures
    if contract_repo_path not in changed_files:
        return failures
    if not base_sha:
        if warnings is not None:
            warnings.append(
                "Skipping contract transition check because base SHA is unavailable."
            )
        return failures

    previous_contracts, previous_failures, exists_in_base = load_contracts_from_git_ref(base_sha, contract_repo_path)
    failures.extend(previous_failures)
    if not exists_in_base:
        return failures

    current_map, current_failures = contracts_status_map(contracts_current)
    previous_map, previous_map_failures = contracts_status_map(previous_contracts)
    failures.extend(current_failures)
    failures.extend(previous_map_failures)
    if failures:
        return failures

    transition_map_raw = cfg.get("allowed_transitions", {})
    transition_map: dict[str, set[str]] = {}
    if isinstance(transition_map_raw, dict):
        for source, targets in transition_map_raw.items():
            if isinstance(source, str) and isinstance(targets, list):
                transition_map[source.lower()] = {
                    str(item).lower() for item in targets if isinstance(item, str)
                }

    removal_allowed_statuses = {
        str(item).lower() for item in cfg.get("removal_allowed_statuses", ["completed", "cancelled"])
        if isinstance(item, str)
    }

    for contract_id, current_status in current_map.items():
        previous_status = previous_map.get(contract_id)
        if previous_status is None or previous_status == current_status:
            continue
        allowed_targets = transition_map.get(previous_status, set())
        if current_status not in allowed_targets:
            failures.append(
                f"Contract {contract_id} has invalid status transition: "
                f"{previous_status} -> {current_status}."
            )

    for contract_id, previous_status in previous_map.items():
        if contract_id in current_map:
            continue
        if previous_status not in removal_allowed_statuses:
            failures.append(
                f"Contract {contract_id} was removed from lifecycle file while in "
                f"non-terminal status '{previous_status}'."
            )

    return failures


def check_contract_base_staleness(base_commit: str, max_commits: int) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    rc, _, err = run_command(["git", "cat-file", "-e", f"{base_commit}^{{commit}}"])
    if rc != 0:
        failures.append(f"Contract base commit '{base_commit}' is not a valid commit: {err or 'git cat-file failed'}")
        return failures, warnings

    rc, _, _ = run_command(["git", "merge-base", "--is-ancestor", base_commit, "HEAD"])
    if rc != 0:
        failures.append(
            f"Contract base commit '{base_commit}' is not an ancestor of HEAD. Mark contract stale and re-approve."
        )
        return failures, warnings

    if max_commits > 0:
        rc, out, err = run_command(["git", "rev-list", "--count", f"{base_commit}..HEAD"])
        if rc != 0:
            warnings.append(f"Unable to measure commits since contract base '{base_commit}': {err or out}")
            return failures, warnings
        try:
            distance = int(out.strip())
        except ValueError:
            warnings.append(f"Unexpected commit distance output for contract base '{base_commit}': {out}")
            return failures, warnings
        if distance > max_commits:
            failures.append(
                f"Contract is stale: {distance} commits since base '{base_commit}' exceeds allowed {max_commits}."
            )
    return failures, warnings


def check_contract_lifecycle_rules(
    changed_files: set[str],
    policy: dict[str, Any],
    warnings: list[str] | None = None,
    run_mode: str = "ci",
    base_sha: str | None = None,
) -> list[str]:
    cfg = contract_rule_config(policy)
    if not cfg.get("enabled", False):
        return []
    if run_mode == "think":
        return []

    targets = contract_target_paths(changed_files, policy)
    if not targets:
        return []

    contract_path_raw = cfg.get("contract_path", ".control-loop/contracts.json")
    contract_path = Path(contract_path_raw)
    if not contract_path.is_absolute():
        contract_path = Path.cwd() / contract_path
    contract_repo_path = resolve_contract_repo_path(Path(contract_path_raw))

    data, load_failures = load_contracts_file(contract_path)
    failures: list[str] = list(load_failures)
    if data is None:
        return failures

    contracts, contract_failures = normalize_contract_list(data.get("contracts"), contract_path)
    failures.extend(contract_failures)
    if not contracts:
        failures.append(f"No contracts defined in {contract_path.as_posix()} for controlled changes.")
        return failures

    id_pattern = cfg.get("id_pattern", r"^CT-\d{3}$")
    allowed_statuses = {item.lower() for item in cfg.get("allowed_statuses", ["active"])}
    active_statuses = {item.lower() for item in cfg.get("active_statuses", ["active"])}
    approval_flag_field = cfg.get("approval_flag_field", "approved")
    approval_actor_field = cfg.get("approval_actor_field", "approved_by")
    backlog_field = cfg.get("backlog_item_id_field", "backlog_item_id")
    base_commit_field = cfg.get("base_commit_field", "base_commit")
    include_field = cfg.get("include_paths_field", "include_paths")
    exclude_field = cfg.get("exclude_paths_field", "exclude_paths")
    require_backlog_link = bool(cfg.get("require_backlog_item_link", True))
    require_approval = bool(cfg.get("require_approval", True))
    require_base_validation = bool(cfg.get("require_base_commit_validation", True))
    max_commits = int(cfg.get("max_commits_since_base", 0))

    try:
        contract_id_regex = re.compile(id_pattern)
    except re.error as exc:
        return [f"Invalid contract id regex in policy: {exc}"]

    active: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for idx, item in enumerate(contracts):
        label = f"contracts[{idx}]"
        contract_id = str(item.get("id", "")).strip()
        status = str(item.get("status", "")).strip().lower()

        if not contract_id_regex.match(contract_id):
            failures.append(f"{label} has invalid contract id '{contract_id}'.")
        if contract_id in seen_ids:
            failures.append(f"Duplicate contract id in lifecycle file: {contract_id}")
        seen_ids.add(contract_id)
        if status not in allowed_statuses:
            failures.append(f"{label} has invalid status '{status}'.")
            continue
        if status in active_statuses:
            active.append(item)

    if len(active) != 1:
        failures.append(
            f"Contract lifecycle requires exactly one active contract for controlled changes; found {len(active)}."
        )
        return failures

    contract = active[0]
    contract_id = str(contract.get("id", "UNKNOWN"))

    if require_approval:
        approved_value = contract.get(approval_flag_field)
        if not isinstance(approved_value, bool) or not approved_value:
            failures.append(f"Active contract {contract_id} must set {approval_flag_field}=true.")
        approved_by = contract.get(approval_actor_field, "")
        if not isinstance(approved_by, str) or not approved_by.strip():
            failures.append(f"Active contract {contract_id} must include non-empty {approval_actor_field}.")

    if require_backlog_link:
        backlog_id = contract.get(backlog_field, "")
        if not isinstance(backlog_id, str) or not re.match(r"^BL-\d{3}$", backlog_id.strip()):
            failures.append(f"Active contract {contract_id} must include valid {backlog_field} (BL-###).")

    include_paths = contract.get(include_field, [])
    exclude_paths = contract.get(exclude_field, [])
    if not isinstance(include_paths, list) or not include_paths or any(not isinstance(item, str) for item in include_paths):
        failures.append(f"Active contract {contract_id} must include non-empty string list field: {include_field}.")
        include_paths = []
    if not isinstance(exclude_paths, list) or any(not isinstance(item, str) for item in exclude_paths):
        failures.append(f"Active contract {contract_id} field {exclude_field} must be a string list.")
        exclude_paths = []

    for path in targets:
        if include_paths and not path_matches_any(path, include_paths):
            failures.append(f"Path {path} is outside active contract {contract_id} include scope.")
        if exclude_paths and path_matches_any(path, exclude_paths):
            failures.append(f"Path {path} is explicitly excluded by active contract {contract_id}.")

    if require_base_validation:
        base_commit = contract.get(base_commit_field, "")
        if not isinstance(base_commit, str) or not base_commit.strip():
            failures.append(f"Active contract {contract_id} must include non-empty {base_commit_field}.")
        else:
            base_failures, base_warnings = check_contract_base_staleness(base_commit.strip(), max_commits)
            failures.extend(base_failures)
            if warnings is not None:
                warnings.extend(base_warnings)

    failures.extend(
        check_contract_transition_rules(
            changed_files,
            contracts,
            contract_repo_path,
            cfg,
            base_sha,
            warnings,
        )
    )

    return failures


def check_governance_amendment_rule(
    changed_files: set[str],
    session_files: list[str],
    policy: dict[str, Any],
) -> list[str]:
    """Block any change to national governance files unless a GOVERNANCE_CHANGE token
    and explicit human review evidence are present in the session log.

    This is the 'constitutional amendment' gate — a higher bar than regular
    implementation changes, analogous to a presidential sign-off requirement.
    """
    cfg = governance_rule_config(policy)
    if not cfg.get("enabled", False):
        return []

    governance_files = set(cfg.get("governance_files", []))
    if not governance_files:
        return []

    changed_governance = [f for f in changed_files if f in governance_files]
    if not changed_governance:
        return []

    token_field = cfg.get("required_token_field", "- Governance change token:")
    token_value = cfg.get("required_token_value", "GOVERNANCE_CHANGE")
    evidence_field = cfg.get("review_evidence_field", "- Governance review evidence:")
    null_tokens = {"none", "n/a", "na", ""}

    primary_session = resolve_primary_session_file(session_files)
    if primary_session is None:
        return [
            f"Governance file(s) changed ({', '.join(sorted(changed_governance))}) "
            "but no session log found. "
            f"Session must contain '{token_field} {token_value}' and "
            f"non-empty '{evidence_field}' before this can be merged."
        ]

    if not primary_session.exists():
        return [f"Primary session file not found: {primary_session.as_posix()}"]

    text = primary_session.read_text(encoding="utf-8")
    failures: list[str] = []

    token = get_marker_value(text, token_field).strip()
    if token != token_value:
        failures.append(
            f"Governance file(s) changed ({', '.join(sorted(changed_governance))}). "
            f"Session {primary_session.as_posix()} must contain "
            f"'{token_field} {token_value}' to confirm this is a deliberate governance amendment."
        )

    evidence = get_marker_value(text, evidence_field).strip()
    if evidence.lower() in null_tokens:
        failures.append(
            f"Governance file(s) changed ({', '.join(sorted(changed_governance))}). "
            f"Session {primary_session.as_posix()} must contain non-empty "
            f"'{evidence_field}' with evidence of human review and approval."
        )

    return failures


def evaluate_change_coupling(
    changed_files: set[str],
    policy: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    manual_reviews: list[str] | None = None,
    run_mode: str = "ci",
    base_sha: str | None = None,
) -> list[str]:
    if policy is None:
        policy = load_policy()

    failures: list[str] = []
    proposal_root = process_policy(policy).get("proposal_root", "docs/proposals/")
    design_paths = process_policy(policy).get("design_update_paths", ["DESIGN.md", "docs/adr/"])
    process_files = set(process_policy(policy).get("process_controlled_files", []))
    process_changelog = process_policy(policy).get("process_changelog_path", "docs/PROCESS_CHANGELOG.md")

    implementation_changed = any(is_implementation_path(path, policy) for path in changed_files)
    process_changed = any(path in process_files for path in changed_files)
    proposal_files = get_changed_proposal_files(changed_files, policy)
    session_files = get_changed_session_files(changed_files, policy)
    session_triggered = any(is_session_trigger_path(path, policy) for path in changed_files)

    if implementation_changed:
        has_proposal_update = bool(proposal_files) or any(
            path.startswith(proposal_root) and path not in set(process_policy(policy).get("proposal_ignored_files", []))
            for path in changed_files
        )
        has_design_update = any(any(path_matches_rule(path, rule) for rule in design_paths) for path in changed_files)

        if not has_proposal_update:
            failures.append(
                "Implementation changed without proposal update under docs/proposals/. "
                "Create/update a proposal with design-compliance notes."
            )
        if not has_design_update:
            failures.append(
                "Implementation changed without DESIGN.md or docs/adr/ update. "
                "Record design impact before merge."
            )

    if process_changed and process_changelog not in changed_files:
        failures.append(
            "Process files changed without docs/PROCESS_CHANGELOG.md update. "
            "Record what changed and why."
        )

    if proposal_files:
        failures.extend(check_proposal_sections(proposal_files, policy, warnings, manual_reviews))

    if session_triggered and not session_files:
        session_root = session_policy(policy).get("root", "docs/sessions/")
        failures.append(
            f"Changed code/process files require a session log update under {session_root} "
            "to record planned actions, approval, and corrective evidence."
        )

    if session_files:
        failures.extend(check_session_sections(session_files, policy))

    failures.extend(check_phase_scope_rules(changed_files, session_files, policy, run_mode))

    failures.extend(check_contract_lifecycle_rules(changed_files, policy, warnings, run_mode, base_sha))

    failures.extend(check_governance_amendment_rule(changed_files, session_files, policy))

    if run_mode != "think":
        failures.extend(check_static_guard_rules(changed_files, policy, warnings, manual_reviews))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate process-governance rules")
    parser.add_argument("--mode", choices=["ci", "think"], default="ci")
    parser.add_argument("--base-sha", default=None, help="Base SHA for changed-file coupling checks")
    parser.add_argument("--policy", default=None, help="Path to policy JSON override")
    args = parser.parse_args()

    try:
        policy = load_policy(args.policy)
    except Exception as exc:
        print(f"FAIL: policy load/validation error: {exc}")
        return 1
    failures: list[str] = []
    warnings: list[str] = []
    manual_reviews: list[str] = []

    failures.extend(check_required_process_files(policy))
    resolved_base = resolve_base_sha(args.base_sha, policy)
    changed_files, diff_warnings = get_changed_files(args.base_sha, policy)
    warnings.extend(diff_warnings)
    if changed_files:
        failures.extend(
            evaluate_change_coupling(
                changed_files,
                policy,
                warnings,
                manual_reviews,
                args.mode,
                resolved_base,
            )
        )

    for warning in warnings:
        print(f"WARN: {warning}")
    for item in manual_reviews:
        print(f"MANUAL_REVIEW: {item}")

    if failures:
        enabled, mode = process_enforcement_state(policy)
        if not enabled:
            for item in failures:
                print(f"WARN: {item}")
            print("PASS: process guard checks reported warnings (global switch disabled)")
            return 0
        if mode == "advisory":
            for item in failures:
                print(f"WARN: {item}")
            print("PASS: process guard checks reported warnings (advisory mode)")
            return 0
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(f"PASS: process guard checks passed for mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

