from __future__ import annotations

from pathlib import Path

from scripts.validate_release_hygiene import changelog_versions, pyproject_version, validate_release_hygiene


def write_minimal_release_files(tmp_path: Path, changelog_text: str, pyproject_version_text: str) -> tuple[Path, Path]:
    changelog = tmp_path / "CHANGELOG.md"
    pyproject = tmp_path / "pyproject.toml"
    changelog.write_text(changelog_text, encoding="utf-8")
    pyproject.write_text(
        "\n".join(
            [
                "[project]",
                'name = "control-loop-kit"',
                f'version = "{pyproject_version_text}"',
            ]
        ),
        encoding="utf-8",
    )
    return changelog, pyproject


def test_changelog_version_parser_extracts_release_versions(tmp_path: Path):
    changelog, _ = write_minimal_release_files(
        tmp_path,
        "# Changelog\n\n## v0.6.4\n- x\n\n## v0.6.3\n- y\n",
        "0.6.4",
    )
    assert changelog_versions(changelog) == ["0.6.4", "0.6.3"]


def test_pyproject_version_parser_reads_project_version(tmp_path: Path):
    _, pyproject = write_minimal_release_files(
        tmp_path,
        "# Changelog\n\n## v0.6.4\n- x\n",
        "0.6.4",
    )
    assert pyproject_version(pyproject) == "0.6.4"


def test_release_hygiene_fails_on_version_mismatch(tmp_path: Path):
    changelog, pyproject = write_minimal_release_files(
        tmp_path,
        "# Changelog\n\n## v0.6.4\n- x\n\n## v0.6.3\n- y\n",
        "0.6.3",
    )

    failures = validate_release_hygiene(
        repo_root=Path(__file__).resolve().parents[1],
        changelog_path=changelog,
        pyproject_path=pyproject,
        allow_unreleased_latest=True,
    )

    assert any("Version mismatch" in item for item in failures)


def test_release_hygiene_passes_for_default_toolkit_repo():
    root = Path(__file__).resolve().parents[1]
    failures = validate_release_hygiene(
        repo_root=root,
        changelog_path=root / "CHANGELOG.md",
        pyproject_path=root / "pyproject.toml",
        allow_unreleased_latest=True,
    )
    assert not failures
