"""Gate suite runner. Executes a predefined suite of gates for CI/local verification."""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Gate suites correspond to definitions in docs/GATE_SUITES.md
SUITES = {
    "stage0": [
        ["python", "scripts/generate_model_catalog_prompt.py", "--check"],
        ["python", "scripts/validate_backlog.py", "--check"],
        ["python", "scripts/render_dashboard.py", "--check"],
        ["python", "scripts/verify_control_loop.py", "--check"],
        ["python", "-m", "ruff", "check", "."],
        ["python", "-m", "pytest", "-q"],
    ],
    "stage1": [
        ["python", "scripts/generate_model_catalog_prompt.py", "--check"],
        ["python", "scripts/validate_backlog.py", "--check"],
        ["python", "scripts/sync_setpoints.py", "--check"],
        ["python", "scripts/render_dashboard.py", "--check"],
        ["python", "scripts/validate_onboarding_docs.py", "--check"],
        ["python", "scripts/validate_release_hygiene.py", "--check", "--allow-unreleased-latest"],
        ["python", "scripts/verify_control_loop.py", "--check"],
        ["python", "-m", "ruff", "check", "."],
        ["python", "-m", "pytest", "-q"],
    ],
}


def resolve_command(cmd: list[str]) -> list[str]:
    """Resolve script paths against this toolkit root so Stage0 runs trusted scripts."""
    if len(cmd) >= 2 and cmd[0] == "python" and cmd[1].startswith("scripts/"):
        return ["python", str((ROOT / cmd[1]).as_posix()), *cmd[2:]]
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a predefined gate suite")
    parser.add_argument("--suite", choices=list(SUITES.keys()), required=True)
    parser.add_argument(
        "--target-root",
        default=".",
        help="Working directory to run checks against (default: current directory).",
    )
    args = parser.parse_args()

    commands = SUITES[args.suite]
    target_root = Path(args.target_root).resolve()
    if not target_root.is_dir():
        print(f"FAIL: target root is not a directory: {target_root}")
        return 1
    failures: int = 0

    print(
        f"Running '{args.suite}' gate suite ({len(commands)} steps) "
        f"against: {target_root}"
    )
    for i, raw_cmd in enumerate(commands, 1):
        cmd = resolve_command(raw_cmd)
        print(f"\n[{i}/{len(commands)}] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=str(target_root))
        if result.returncode != 0:
            print(f"FAIL: Step {i} failed with exit code {result.returncode}")
            failures += 1
        else:
            print(f"PASS: Step {i}")

    print("\n" + "=" * 40)
    if failures > 0:
        print(f"SUITE FAILED: {failures} step(s) failed.")
        return 1

    print("SUITE PASSED: All steps successful.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
