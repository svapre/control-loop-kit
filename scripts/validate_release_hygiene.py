"""Validate release hygiene between changelog, version file, and tags."""

from __future__ import annotations

import argparse
import re
import subprocess
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHANGELOG = ROOT / "CHANGELOG.md"
DEFAULT_PYPROJECT = ROOT / "pyproject.toml"
VERSION_HEADER = re.compile(r"^##\s+v(\d+\.\d+\.\d+)\s*$")


def run_command(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def changelog_versions(path: Path) -> list[str]:
    versions: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = VERSION_HEADER.match(line.strip())
        if match:
            versions.append(match.group(1))
    return versions


def pyproject_version(path: Path) -> str:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml missing [project] section.")
    version = project.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("pyproject.toml missing project.version.")
    return version.strip()


def git_tags(repo_root: Path) -> set[str]:
    rc, out, err = run_command(["git", "tag", "--list"], repo_root)
    if rc != 0:
        raise ValueError(f"Unable to read git tags: {err or out}")
    return {line.strip() for line in out.splitlines() if line.strip()}


def validate_release_hygiene(
    repo_root: Path,
    changelog_path: Path,
    pyproject_path: Path,
    allow_unreleased_latest: bool,
) -> list[str]:
    failures: list[str] = []
    if not changelog_path.exists():
        return [f"Missing changelog file: {changelog_path.as_posix()}"]
    if not pyproject_path.exists():
        return [f"Missing pyproject file: {pyproject_path.as_posix()}"]

    versions = changelog_versions(changelog_path)
    if not versions:
        return ["CHANGELOG.md has no release headings of form '## vX.Y.Z'."]

    latest_changelog = versions[0]
    project_version = pyproject_version(pyproject_path)
    if project_version != latest_changelog:
        failures.append(
            f"Version mismatch: pyproject={project_version}, changelog_latest={latest_changelog}"
        )

    tags = git_tags(repo_root)
    required_versions = versions[1:] if allow_unreleased_latest else versions
    for version in required_versions:
        tag_name = f"v{version}"
        if tag_name not in tags:
            failures.append(f"Missing release tag for changelog version: {tag_name}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release hygiene.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root path.")
    parser.add_argument("--changelog", default=str(DEFAULT_CHANGELOG), help="Path to CHANGELOG.md.")
    parser.add_argument("--pyproject", default=str(DEFAULT_PYPROJECT), help="Path to pyproject.toml.")
    parser.add_argument(
        "--allow-unreleased-latest",
        action="store_true",
        help="Allow latest changelog version to exist without a git tag.",
    )
    parser.add_argument("--check", action="store_true", help="Run checks and fail on hygiene violations.")
    args = parser.parse_args()

    failures = validate_release_hygiene(
        repo_root=Path(args.root),
        changelog_path=Path(args.changelog),
        pyproject_path=Path(args.pyproject),
        allow_unreleased_latest=bool(args.allow_unreleased_latest),
    )
    if failures:
        print("FAIL: release hygiene validation failed")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS: release hygiene validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
