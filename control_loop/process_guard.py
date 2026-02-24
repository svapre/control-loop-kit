"""Process-governance checks to keep planning and design discipline enforceable."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REQUIRED_PROCESS_FILES = [
    "GOVERNANCE.md",
    "DESIGN.md",
    "docs/USER_CONTEXT.md",
    "docs/PROCESS_CHANGELOG.md",
    "docs/proposals/README.md",
    "docs/proposals/TEMPLATE.md",
    ".github/pull_request_template.md",
]

IMPLEMENTATION_PREFIXES = ("core/", "data_models/", "utils/")
IMPLEMENTATION_FILES = {"main.py"}

PROCESS_CONTROLLED_FILES = {
    "AGENTS.md",
    "SPEC.md",
    "SYSTEM.md",
    "GOVERNANCE.md",
    "DESIGN.md",
    "docs/USER_CONTEXT.md",
    "docs/proposals/README.md",
    "docs/proposals/TEMPLATE.md",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "scripts/control_gate.py",
    "scripts/process_guard.py",
}

PROPOSAL_IGNORED_FILES = {
    "docs/proposals/README.md",
    "docs/proposals/TEMPLATE.md",
}

REQUIRED_PROPOSAL_SECTIONS = [
    "## Problem",
    "## Options Considered",
    "## Design Parameter Compliance",
    "## Exception Register",
    "## Decision Scorecard",
    "## Decision",
    "## Risks and Mitigations",
    "## Validation Plan",
]

REQUIRED_PROPOSAL_FIELDS = [
    "- Structural correctness:",
    "- Deterministic behavior:",
    "- Traceable decisions:",
    "- No silent guessing:",
    "- Configuration over hardcoding:",
    "- Idempotent processing:",
    "- Fail loudly on invalid state:",
    "- Performance budget awareness:",
    "- Extensible module boundaries:",
    "- Evidence-backed claims:",
    "- Violated parameter(s):",
    "- Why alternatives are worse:",
    "- Risk:",
    "- Mitigation:",
    "- Rollback plan:",
    "- Why this is best overall now:",
]


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def check_required_process_files() -> list[str]:
    failures: list[str] = []
    for file_path in REQUIRED_PROCESS_FILES:
        if not Path(file_path).exists():
            failures.append(f"Missing process artifact: {file_path}")
    return failures


def resolve_base_sha(base_sha: str | None) -> str | None:
    if base_sha and not base_sha.startswith("000000"):
        return base_sha

    rc_merge_base, out_merge_base, _ = run_command(["git", "merge-base", "HEAD", "origin/master"])
    if rc_merge_base == 0 and out_merge_base:
        return out_merge_base

    rc, out, _ = run_command(["git", "rev-parse", "HEAD^"])
    if rc == 0 and out:
        return out
    return None


def get_changed_files(base_sha: str | None) -> tuple[set[str], list[str]]:
    warnings: list[str] = []
    resolved = resolve_base_sha(base_sha)
    changed: set[str] = set()

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


def is_implementation_path(path: str) -> bool:
    return path in IMPLEMENTATION_FILES or any(path.startswith(prefix) for prefix in IMPLEMENTATION_PREFIXES)


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


def get_changed_proposal_files(changed_files: set[str]) -> list[str]:
    return sorted(
        [
            path
            for path in changed_files
            if path.startswith("docs/proposals/") and path not in PROPOSAL_IGNORED_FILES
        ]
    )


def check_proposal_sections(proposal_files: list[str]) -> list[str]:
    failures: list[str] = []
    for path in proposal_files:
        proposal_path = Path(path)
        if not proposal_path.exists():
            failures.append(f"Proposal file is referenced in changes but not found: {path}")
            continue

        text = proposal_path.read_text(encoding="utf-8")
        for section in REQUIRED_PROPOSAL_SECTIONS:
            if section not in text:
                failures.append(f"Proposal {path} missing required section: {section}")
        for field in REQUIRED_PROPOSAL_FIELDS:
            if field not in text:
                failures.append(f"Proposal {path} missing required field marker: {field}")
    return failures


def evaluate_change_coupling(changed_files: set[str]) -> list[str]:
    failures: list[str] = []

    implementation_changed = any(is_implementation_path(path) for path in changed_files)
    process_changed = any(path in PROCESS_CONTROLLED_FILES for path in changed_files)
    proposal_files = get_changed_proposal_files(changed_files)

    if implementation_changed:
        has_proposal_update = bool(proposal_files)
        has_design_update = "DESIGN.md" in changed_files or any(path.startswith("docs/adr/") for path in changed_files)

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

    if process_changed and "docs/PROCESS_CHANGELOG.md" not in changed_files:
        failures.append(
            "Process files changed without docs/PROCESS_CHANGELOG.md update. "
            "Record what changed and why."
        )

    if proposal_files:
        failures.extend(check_proposal_sections(proposal_files))

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate process-governance rules")
    parser.add_argument("--mode", choices=["ci"], default="ci")
    parser.add_argument("--base-sha", default=None, help="Base SHA for changed-file coupling checks")
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []

    failures.extend(check_required_process_files())
    changed_files, diff_warnings = get_changed_files(args.base_sha)
    warnings.extend(diff_warnings)
    if changed_files:
        failures.extend(evaluate_change_coupling(changed_files))

    for warning in warnings:
        print(f"WARN: {warning}")

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print("PASS: process guard checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
