"""Control-system gate checks for CI and readiness validation."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from control_loop.policy import load_policy


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def find_successful_run_for_head(runs: Iterable[dict], head_sha: str, workflow_name: str) -> dict | None:
    for run in runs:
        if (
            run.get("headSha") == head_sha
            and run.get("workflowName") == workflow_name
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
        ):
            return run
    return None


def control_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return policy.get("control_gate", {})


def check_required_files(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    required = control_policy(policy).get("required_files", [])
    for path in required:
        if not Path(path).exists():
            failures.append(f"Missing required control artifact: {path}")
    if control_policy(policy).get("require_tests_dir", True) and not Path("tests").exists():
        failures.append("Missing tests directory")
    return failures


def resolve_command_tokens(cmd: list[str]) -> list[str]:
    resolved: list[str] = []
    for token in cmd:
        if token == "${PYTHON}":
            resolved.append(sys.executable)
        else:
            resolved.append(token)
    return resolved


def check_local_commands(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    commands = control_policy(policy).get("readiness_commands", [])
    for cmd in commands:
        resolved = resolve_command_tokens(cmd)
        rc, out, err = run_command(resolved)
        if rc != 0:
            message = err or out or "No output"
            failures.append(f"Command failed ({' '.join(resolved)}): {message}")
    return failures


def check_clean_worktree() -> list[str]:
    rc, out, err = run_command(["git", "status", "--short"])
    if rc != 0:
        return [f"Unable to inspect git worktree: {err or out}"]
    if out:
        return ["Git worktree is not clean"]
    return []


def check_readiness_tag(policy: dict[str, Any]) -> list[str]:
    tag_name = control_policy(policy).get("readiness_tag", "control-system-ready")
    rc_head, head_sha, err_head = run_command(["git", "rev-parse", "HEAD"])
    if rc_head != 0:
        return [f"Unable to resolve HEAD: {err_head or head_sha}"]

    rc_tag, tag_sha, _ = run_command(["git", "rev-list", "-n", "1", tag_name])
    if rc_tag != 0:
        return [f"Missing readiness tag: {tag_name}"]
    if head_sha != tag_sha:
        return [f"Readiness tag is stale: {tag_name} does not point to HEAD"]
    return []


def check_remote_ci_for_head(policy: dict[str, Any]) -> list[str]:
    workflow_name = control_policy(policy).get("ci_workflow_name", "ci")
    rc_origin, _, err_origin = run_command(["git", "remote", "get-url", "origin"])
    if rc_origin != 0:
        return [f"Missing git remote 'origin': {err_origin or 'not configured'}"]

    gh_bin = shutil.which("gh")
    if not gh_bin:
        return ["GitHub CLI (gh) not found on PATH"]

    rc_auth, out_auth, err_auth = run_command([gh_bin, "auth", "status"])
    if rc_auth != 0:
        return [f"GitHub auth check failed: {err_auth or out_auth}"]

    rc_head, head_sha, err_head = run_command(["git", "rev-parse", "HEAD"])
    if rc_head != 0:
        return [f"Unable to resolve HEAD: {err_head or head_sha}"]

    rc_runs, out_runs, err_runs = run_command(
        [
            gh_bin,
            "run",
            "list",
            "--workflow",
            workflow_name,
            "--limit",
            "40",
            "--json",
            "headSha,status,conclusion,workflowName,url",
        ]
    )
    if rc_runs != 0:
        return [f"Unable to query GitHub workflow runs: {err_runs or out_runs}"]

    try:
        runs = json.loads(out_runs) if out_runs else []
    except json.JSONDecodeError as exc:
        return [f"Failed to parse GitHub run list JSON: {exc}"]

    hit = find_successful_run_for_head(runs, head_sha, workflow_name)
    if not hit:
        return [f"No successful '{workflow_name}' workflow run found for current HEAD"]
    return []


def check_master_plan_guard(policy: dict[str, Any]) -> list[str]:
    path = Path("MASTER_PLAN.md")
    if not path.exists():
        return ["MASTER_PLAN.md not found"]
    text = path.read_text(encoding="utf-8")
    tokens = control_policy(policy).get("master_plan_tokens", ["Step 5", "| 5 |"])
    if not any(token in text for token in tokens):
        return ["MASTER_PLAN.md is missing readiness step tracking token"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control-system gates")
    parser.add_argument(
        "--mode",
        choices=["ci", "readiness"],
        default="ci",
        help="ci = static control checks, readiness = full closed-loop readiness checks",
    )
    parser.add_argument("--policy", default=None, help="Path to policy JSON override")
    args = parser.parse_args()

    try:
        policy = load_policy(args.policy)
    except Exception as exc:
        print(f"FAIL: policy load/validation error: {exc}")
        return 1
    failures: list[str] = []
    failures.extend(check_required_files(policy))
    failures.extend(check_master_plan_guard(policy))

    if args.mode == "readiness":
        failures.extend(check_clean_worktree())
        failures.extend(check_local_commands(policy))
        failures.extend(check_remote_ci_for_head(policy))
        failures.extend(check_readiness_tag(policy))

    if failures:
        for item in failures:
            print(f"FAIL: {item}")
        return 1

    print(f"PASS: control gate checks passed for mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
