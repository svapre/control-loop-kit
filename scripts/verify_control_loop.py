"""Control-loop integrity verification. Validates that consumer projects have wired the feedback loop correctly."""

import argparse
import sys
from pathlib import Path
from typing import Any

# Add project root to sys.path so we can import control_loop
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_loop.policy import load_policy  # noqa: E402


def check_directory_exists(path_str: str, name: str) -> list[str]:
    path = Path(path_str)
    failures = []
    if not path.is_dir():
        failures.append(f"Missing {name} directory at: {path_str}")
    else:
        if not (path / "README.md").is_file():
            failures.append(f"Missing README.md in {name} directory: {path_str}/README.md")
        if not (path / "TEMPLATE.md").is_file():
            failures.append(f"Missing TEMPLATE.md in {name} directory: {path_str}/TEMPLATE.md")
    return failures


def check_ci_wiring(policy_config: dict[str, Any]) -> tuple[list[str], list[str]]:
    failures = []
    warnings = []
    
    ci_path_str = policy_config.get("ci_workflow_path", ".github/workflows/ci.yml")
    ci_path = Path(ci_path_str)
    
    if not ci_path.is_file():
        failures.append(f"Missing CI workflow file at configured path: {ci_path_str}")
        return failures, warnings

    content = ci_path.read_text(encoding="utf-8")
    
    # Check required gates are invoked
    for marker in policy_config.get("required_gate_markers", ["process_guard", "control_gate"]):
        if marker not in content:
            failures.append(f"CI workflow '{ci_path_str}' does not appear to invoke required gate: {marker}")

    # Check stage0 configuration
    stage0_check = policy_config.get("stage0_check", "warn")
    if stage0_check != "ignore":
        stage0_marker = policy_config.get("stage0_marker", "STAGE0_TAG")
        if stage0_marker not in content:
            msg = f"CI workflow '{ci_path_str}' does not appear to configure Stage0 external governance (missing '{stage0_marker}')"
            if stage0_check == "strict":
                failures.append(msg)
            else:
                warnings.append(msg)

    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify control-loop integrity")
    parser.add_argument("--check", action="store_true", help="Run verification checks")
    parser.add_argument("--policy", default=None, help="Path to policy JSON override")
    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return 0

    try:
        policy = load_policy(args.policy)
    except Exception as exc:
        print(f"FAIL: policy load/validation error: {exc}")
        return 1

    integrity_config = policy.get("control_loop_integrity", {})
    if not integrity_config:
        # Provide defaults if not strictly in policy
        integrity_config = {
            "ci_workflow_path": ".github/workflows/ci.yml",
            "required_gate_markers": ["process_guard", "control_gate"],
            "stage0_check": "warn",
            "stage0_marker": "STAGE0_TAG"
        }

    failures = []
    warnings = []

    # 1. Check CI wiring
    ci_fails, ci_warns = check_ci_wiring(integrity_config)
    failures.extend(ci_fails)
    warnings.extend(ci_warns)

    # 2. Check infrastructure elements
    failures.extend(check_directory_exists("docs/sessions", "sessions"))
    failures.extend(check_directory_exists("docs/proposals", "proposals"))

    if warnings:
        for w in warnings:
            print(f"WARN: {w}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1

    print("PASS: Control-loop integrity validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
