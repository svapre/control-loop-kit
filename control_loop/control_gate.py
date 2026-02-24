"""Control-system gate checks for CI and readiness validation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_FILES = [
    "MASTER_PLAN.md",
    "SPEC.md",
    "SYSTEM.md",
    "AGENTS.md",
    "DESIGN.md",
    "GOVERNANCE.md",
    "docs/USER_CONTEXT.md",
    "docs/PROCESS_CHANGELOG.md",
    "docs/proposals/README.md",
    "docs/proposals/TEMPLATE.md",
    ".github/workflows/ci.yml",
    ".github/pull_request_template.md",
    "pyproject.toml",
    "requirements-dev.txt",
    "scripts/process_guard.py",
]


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def find_successful_run_for_head(runs: Iterable[dict], head_sha: str) -> dict | None:
    for run in runs:
        if (
            run.get("headSha") == head_sha
            and run.get("workflowName") == "ci"
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
        ):
            return run
    return None


def check_required_files() -> list[str]:
    failures: list[str] = []
    for path in REQUIRED_FILES:
        if not Path(path).exists():
            failures.append(f"Missing required control artifact: {path}")
    if not Path("tests").exists():
        failures.append("Missing tests directory")
    return failures


def check_local_commands() -> list[str]:
    failures: list[str] = []

    cmds = [
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        [sys.executable, "scripts/process_guard.py", "--mode", "ci"],
    ]

    for cmd in cmds:
        rc, out, err = run_command(cmd)
        if rc != 0:
            joined = " ".join(cmd)
            message = err or out or "No output"
            failures.append(f"Command failed ({joined}): {message}")
    return failures


def check_clean_worktree() -> list[str]:
    rc, out, err = run_command(["git", "status", "--short"])
    if rc != 0:
        return [f"Unable to inspect git worktree: {err or out}"]
    if out:
        return ["Git worktree is not clean"]
    return []


def check_readiness_tag() -> list[str]:
    failures: list[str] = []

    rc_head, head_sha, err_head = run_command(["git", "rev-parse", "HEAD"])
    if rc_head != 0:
        return [f"Unable to resolve HEAD: {err_head or head_sha}"]

    rc_tag, tag_sha, err_tag = run_command(["git", "rev-list", "-n", "1", "control-system-ready"])
    if rc_tag != 0:
        return ["Missing readiness tag: control-system-ready"]

    if head_sha != tag_sha:
        failures.append("Readiness tag is stale: control-system-ready does not point to HEAD")

    return failures


def check_remote_ci_for_head() -> list[str]:
    failures: list[str] = []

    rc_origin, _, err_origin = run_command(["git", "remote", "get-url", "origin"])
    if rc_origin != 0:
        return [f"Missing git remote 'origin': {err_origin or 'not configured'}"]

    gh_bin = shutil.which("gh")
    if not gh_bin:
        return ["GitHub CLI (gh) not found on PATH"]

    rc_auth, out_auth, err_auth = run_command([gh_bin, "auth", "status"])
    if rc_auth != 0:
        failures.append(f"GitHub auth check failed: {err_auth or out_auth}")
        return failures

    rc_head, head_sha, err_head = run_command(["git", "rev-parse", "HEAD"])
    if rc_head != 0:
        failures.append(f"Unable to resolve HEAD: {err_head or head_sha}")
        return failures

    rc_runs, out_runs, err_runs = run_command(
        [
            gh_bin,
            "run",
            "list",
            "--workflow",
            "ci",
            "--limit",
            "40",
            "--json",
            "headSha,status,conclusion,workflowName,url",
        ]
    )
    if rc_runs != 0:
        failures.append(f"Unable to query GitHub workflow runs: {err_runs or out_runs}")
        return failures

    try:
        runs = json.loads(out_runs) if out_runs else []
    except json.JSONDecodeError as exc:
        failures.append(f"Failed to parse GitHub run list JSON: {exc}")
        return failures

    hit = find_successful_run_for_head(runs, head_sha)
    if not hit:
        failures.append("No successful 'ci' workflow run found for current HEAD")

    return failures


def check_master_plan_guard() -> list[str]:
    path = Path("MASTER_PLAN.md")
    if not path.exists():
        return ["MASTER_PLAN.md not found"]

    text = path.read_text(encoding="utf-8")
    if "Step 5" not in text and "| 5 |" not in text:
        return ["MASTER_PLAN.md is missing Step 5 tracking"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control-system gates")
    parser.add_argument(
        "--mode",
        choices=["ci", "readiness"],
        default="ci",
        help="ci = static control checks, readiness = full closed-loop readiness checks",
    )
    args = parser.parse_args()

    failures: list[str] = []
    failures.extend(check_required_files())
    failures.extend(check_master_plan_guard())

    if args.mode == "readiness":
        failures.extend(check_clean_worktree())
        failures.extend(check_local_commands())
        failures.extend(check_remote_ci_for_head())
        failures.extend(check_readiness_tag())

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(f"PASS: control gate checks passed for mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

