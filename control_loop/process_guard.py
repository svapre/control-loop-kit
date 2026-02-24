"""Process-governance checks to keep planning and design discipline enforceable."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from control_loop.policy import load_policy


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


def process_enforcement_state(policy: dict[str, Any]) -> tuple[bool, str]:
    switch = ai_global_switch(policy)
    enabled = bool(switch.get("enabled", True))
    mode = str(switch.get("mode", "strict")).lower()
    if mode not in {"strict", "advisory"}:
        mode = "strict"
    return enabled, mode


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


def is_implementation_path(path: str, policy: dict[str, Any]) -> bool:
    exact_files = set(process_policy(policy).get("implementation_files", []))
    prefixes = tuple(process_policy(policy).get("implementation_prefixes", []))
    return path in exact_files or any(path.startswith(prefix) for prefix in prefixes)


def is_session_trigger_path(path: str, policy: dict[str, Any]) -> bool:
    cfg = session_policy(policy)
    exact_files = set(cfg.get("required_for_files", []))
    prefixes = tuple(cfg.get("required_for_prefixes", []))
    return path in exact_files or any(path.startswith(prefix) for prefix in prefixes)


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


def check_proposal_sections(proposal_files: list[str], policy: dict[str, Any]) -> list[str]:
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
    if rule.endswith("/"):
        return path.startswith(rule)
    return path == rule


def evaluate_change_coupling(changed_files: set[str], policy: dict[str, Any] | None = None) -> list[str]:
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
        failures.extend(check_proposal_sections(proposal_files, policy))

    if session_triggered and not session_files:
        session_root = session_policy(policy).get("root", "docs/sessions/")
        failures.append(
            f"Changed code/process files require a session log update under {session_root} "
            "to record planned actions, approval, and corrective evidence."
        )

    if session_files:
        failures.extend(check_session_sections(session_files, policy))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate process-governance rules")
    parser.add_argument("--mode", choices=["ci"], default="ci")
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

    failures.extend(check_required_process_files(policy))
    changed_files, diff_warnings = get_changed_files(args.base_sha, policy)
    warnings.extend(diff_warnings)
    if changed_files:
        failures.extend(evaluate_change_coupling(changed_files, policy))

    for warning in warnings:
        print(f"WARN: {warning}")

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

    print("PASS: process guard checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
