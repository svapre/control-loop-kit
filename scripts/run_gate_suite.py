"""Gate suite runner. Executes a predefined suite of gates for CI/local verification."""

import argparse
import subprocess
import sys

# Gate suites correspond to definitions in docs/GATE_SUITES.md
SUITES = {
    "stage0": [
        ["python", "scripts/generate_model_catalog_prompt.py", "--check"],
        ["python", "scripts/validate_backlog.py", "--check"],
        ["python", "scripts/render_dashboard.py", "--check"],
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a predefined gate suite")
    parser.add_argument("--suite", choices=list(SUITES.keys()), required=True)
    args = parser.parse_args()

    commands = SUITES[args.suite]
    failures: int = 0

    print(f"Running '{args.suite}' gate suite ({len(commands)} steps)...")
    for i, cmd in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"❌ FAIL: Step {i} failed with exit code {result.returncode}")
            failures += 1
        else:
            print(f"✅ PASS: Step {i}")

    print("\n" + "=" * 40)
    if failures > 0:
        print(f"SUITE FAILED: {failures} step(s) failed.")
        return 1

    print("SUITE PASSED: All steps successful.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
