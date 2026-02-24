"""Validate onboarding documentation completeness and consistency."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/CONTROL_TOOLKIT_GUIDE.md",
    "docs/QUICKSTART.md",
    "docs/POLICY_SCHEMA.md",
    "docs/ROADMAP.md",
    "docs/CONTROL_DASHBOARD.md",
    ".control-loop/backlog.json",
    ".control-loop/setpoints.json",
    ".control-loop/contracts.json",
]

REQUIRED_READ_ORDER = [
    "README.md",
    "docs/CONTROL_TOOLKIT_GUIDE.md",
    "docs/QUICKSTART.md",
    "docs/POLICY_SCHEMA.md",
    "docs/ROADMAP.md",
    "docs/CONTROL_DASHBOARD.md",
    ".control-loop/backlog.json",
    ".control-loop/setpoints.json",
    ".control-loop/contracts.json",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require_file(repo_root: Path, rel_path: str, failures: list[str]) -> Path:
    path = repo_root / rel_path
    if not path.exists():
        failures.append(f"Missing required onboarding file: {rel_path}")
    return path


def validate_read_order(agents_text: str, failures: list[str]) -> None:
    marker = "## Mandatory Read Order"
    if marker not in agents_text:
        failures.append("AGENTS.md must contain heading: '## Mandatory Read Order'.")
        return

    positions: list[int] = []
    for rel_path in REQUIRED_READ_ORDER:
        token = f"`{rel_path}`"
        index = agents_text.find(token)
        if index < 0:
            failures.append(f"AGENTS.md read order is missing entry: {rel_path}")
            continue
        positions.append(index)

    if len(positions) == len(REQUIRED_READ_ORDER):
        for idx in range(1, len(positions)):
            if positions[idx] <= positions[idx - 1]:
                failures.append("AGENTS.md read order entries are out of order.")
                break


def validate_onboarding_docs(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for rel_path in REQUIRED_FILES:
        require_file(repo_root, rel_path, failures)
    if failures:
        return failures

    agents_text = read_text(repo_root / "AGENTS.md")
    readme_text = read_text(repo_root / "README.md")
    guide_text = read_text(repo_root / "docs/CONTROL_TOOLKIT_GUIDE.md")
    quickstart_text = read_text(repo_root / "docs/QUICKSTART.md")

    validate_read_order(agents_text, failures)

    if "`AGENTS.md`" not in readme_text:
        failures.append("README.md must link to `AGENTS.md` as AI entrypoint.")
    if "`AGENTS.md`" not in guide_text:
        failures.append("docs/CONTROL_TOOLKIT_GUIDE.md must reference `AGENTS.md`.")
    if "AGENTS.md" not in quickstart_text:
        failures.append("docs/QUICKSTART.md must reference AGENTS.md before changes.")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate onboarding docs contract.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root path.")
    parser.add_argument("--check", action="store_true", help="Run checks and fail on violations.")
    args = parser.parse_args()

    repo_root = Path(args.root)
    failures = validate_onboarding_docs(repo_root)
    if failures:
        print("FAIL: onboarding docs validation failed")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS: onboarding docs validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
