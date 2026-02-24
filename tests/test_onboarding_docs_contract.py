from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_onboarding_docs import validate_onboarding_docs


def write_valid_onboarding_files(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".control-loop").mkdir(parents=True, exist_ok=True)

    (tmp_path / "AGENTS.md").write_text(
        "\n".join(
            [
                "# Toolkit AI Entry Point",
                "## Mandatory Read Order",
                "1. `README.md`",
                "2. `docs/CONTROL_TOOLKIT_GUIDE.md`",
                "3. `docs/QUICKSTART.md`",
                "4. `docs/POLICY_SCHEMA.md`",
                "5. `docs/ROADMAP.md`",
                "6. `docs/CONTROL_DASHBOARD.md`",
                "7. `.control-loop/backlog.json`",
                "8. `.control-loop/setpoints.json`",
                "9. `.control-loop/contracts.json`",
            ]
        ),
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text("Read `AGENTS.md` first.\n", encoding="utf-8")
    (tmp_path / "docs/CONTROL_TOOLKIT_GUIDE.md").write_text(
        "Use `AGENTS.md` for AI onboarding.\n", encoding="utf-8"
    )
    (tmp_path / "docs/QUICKSTART.md").write_text("Read AGENTS.md before changes.\n", encoding="utf-8")
    (tmp_path / "docs/POLICY_SCHEMA.md").write_text("# Policy\n", encoding="utf-8")
    (tmp_path / "docs/ROADMAP.md").write_text("# Roadmap\n", encoding="utf-8")
    (tmp_path / "docs/CONTROL_DASHBOARD.md").write_text("# Dashboard\n", encoding="utf-8")
    (tmp_path / ".control-loop/backlog.json").write_text(
        json.dumps({"meta": {"schema_version": "1"}, "items": []}), encoding="utf-8"
    )
    (tmp_path / ".control-loop/setpoints.json").write_text(
        json.dumps({"meta": {"schema_version": "1"}, "setpoints": []}), encoding="utf-8"
    )
    (tmp_path / ".control-loop/contracts.json").write_text(
        json.dumps({"meta": {"schema_version": "1"}, "contracts": []}), encoding="utf-8"
    )


def test_onboarding_doc_validation_passes_for_default_toolkit_files():
    root = Path(__file__).resolve().parents[1]
    failures = validate_onboarding_docs(root)
    assert not failures


def test_onboarding_doc_validation_fails_when_required_file_missing(tmp_path: Path):
    write_valid_onboarding_files(tmp_path)
    (tmp_path / "docs/QUICKSTART.md").unlink()

    failures = validate_onboarding_docs(tmp_path)

    assert any("quickstart" in item.lower() for item in failures)


def test_onboarding_doc_validation_fails_when_read_order_is_wrong(tmp_path: Path):
    write_valid_onboarding_files(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "\n".join(
            [
                "# Toolkit AI Entry Point",
                "## Mandatory Read Order",
                "1. `docs/CONTROL_TOOLKIT_GUIDE.md`",
                "2. `README.md`",
                "3. `docs/QUICKSTART.md`",
                "4. `docs/POLICY_SCHEMA.md`",
                "5. `docs/ROADMAP.md`",
                "6. `docs/CONTROL_DASHBOARD.md`",
                "7. `.control-loop/backlog.json`",
                "8. `.control-loop/setpoints.json`",
                "9. `.control-loop/contracts.json`",
            ]
        ),
        encoding="utf-8",
    )

    failures = validate_onboarding_docs(tmp_path)

    assert any("out of order" in item.lower() for item in failures)
