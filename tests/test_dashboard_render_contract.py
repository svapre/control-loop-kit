from __future__ import annotations

import json
from pathlib import Path

from scripts.render_dashboard import is_dashboard_synced, render_dashboard, write_dashboard
from scripts.validate_backlog import validate_artifacts


def write_valid_sources(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    control_dir = tmp_path / ".control-loop"
    docs_dir = tmp_path / "docs"
    control_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    setpoints_path = control_dir / "setpoints.json"
    backlog_path = control_dir / "backlog.json"
    roadmap_path = docs_dir / "ROADMAP.md"
    dashboard_path = docs_dir / "CONTROL_DASHBOARD.md"

    setpoints_path.write_text(
        json.dumps(
            {
                "meta": {"schema_version": "1", "last_updated": "2026-02-24"},
                "setpoints": [
                    {
                        "id": "SP-001",
                        "name": "CI pass rate",
                        "metric": "ci_pass_rate_30d",
                        "source": "github_actions.ci",
                        "current_value": 0.99,
                        "target": {"operator": ">=", "value": 0.98},
                        "status": "on_track",
                        "owner_role": "controller",
                        "deadline": "2026-03-31",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    backlog_path.write_text(
        json.dumps(
            {
                "meta": {"schema_version": "1", "last_updated": "2026-02-24"},
                "items": [
                    {
                        "id": "BL-001",
                        "title": "Example active item",
                        "type": "issue",
                        "status": "active",
                        "roadmap_lane": "now",
                        "linked_setpoints": ["SP-001"],
                        "is_blocker": True,
                        "expected_error_reduction": "high",
                        "confidence": "high",
                        "effort": "medium",
                        "priority_score": 167,
                        "owner_role": "thinking_ai",
                        "next_action": "Do work",
                        "acceptance_checks": ["python -m pytest -q"],
                        "created_on": "2026-02-24",
                        "updated_on": "2026-02-24",
                    },
                    {
                        "id": "BL-002",
                        "title": "Example next item",
                        "type": "future_plan",
                        "status": "planned",
                        "roadmap_lane": "next",
                        "linked_setpoints": ["SP-001"],
                        "is_blocker": False,
                        "expected_error_reduction": "medium",
                        "confidence": "medium",
                        "effort": "large",
                        "priority_score": 18,
                        "owner_role": "thinking_ai",
                        "next_action": "Plan work",
                        "acceptance_checks": ["python -m pytest -q"],
                        "created_on": "2026-02-24",
                        "updated_on": "2026-02-24",
                    },
                    {
                        "id": "BL-003",
                        "title": "Example later item",
                        "type": "suggestion",
                        "status": "triaged",
                        "roadmap_lane": "later",
                        "linked_setpoints": ["SP-001"],
                        "is_blocker": False,
                        "expected_error_reduction": "low",
                        "confidence": "medium",
                        "effort": "large",
                        "priority_score": 6,
                        "owner_role": "thinking_ai",
                        "next_action": "Review idea",
                        "acceptance_checks": ["python -m pytest -q"],
                        "created_on": "2026-02-24",
                        "updated_on": "2026-02-24",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    roadmap_path.write_text(
        "\n".join(
            [
                "# Roadmap",
                "",
                "## Now",
                "- BL-001 Example active item",
                "",
                "## Next",
                "- BL-002 Example next item",
                "",
                "## Later",
                "- BL-003 Example later item",
            ]
        ),
        encoding="utf-8",
    )

    return backlog_path, setpoints_path, roadmap_path, dashboard_path


def test_render_dashboard_contains_core_sections(tmp_path: Path):
    backlog_path, setpoints_path, roadmap_path, _ = write_valid_sources(tmp_path)
    failures, backlog_data, setpoints_data, roadmap_data = validate_artifacts(
        backlog_path,
        setpoints_path,
        roadmap_path,
    )
    assert not failures

    text = render_dashboard(backlog_data, setpoints_data, roadmap_data)
    assert "# Control Dashboard" in text
    assert "## Setpoint Health" in text
    assert "## Top Priority Queue" in text
    assert "BL-001" in text


def test_dashboard_sync_check_fails_when_file_is_stale(tmp_path: Path):
    backlog_path, setpoints_path, roadmap_path, dashboard_path = write_valid_sources(tmp_path)
    dashboard_path.write_text("# stale", encoding="utf-8")

    synced, message = is_dashboard_synced(backlog_path, setpoints_path, roadmap_path, dashboard_path)
    assert not synced
    assert "out of sync" in message.lower()


def test_dashboard_sync_check_passes_after_write(tmp_path: Path):
    backlog_path, setpoints_path, roadmap_path, dashboard_path = write_valid_sources(tmp_path)
    write_dashboard(backlog_path, setpoints_path, roadmap_path, dashboard_path)

    synced, message = is_dashboard_synced(backlog_path, setpoints_path, roadmap_path, dashboard_path)
    assert synced
    assert "in sync" in message.lower()
