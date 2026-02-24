from __future__ import annotations

import json
from pathlib import Path

from scripts.sync_setpoints import apply_sp003_metric


def build_sources(
    tmp_path: Path,
    backlog_items: list[dict[str, object]],
    sp003_value: float = 0.0,
    sp003_status: str = "unknown",
) -> tuple[Path, Path]:
    control_dir = tmp_path / ".control-loop"
    control_dir.mkdir(parents=True, exist_ok=True)

    backlog_path = control_dir / "backlog.json"
    setpoints_path = control_dir / "setpoints.json"

    backlog_path.write_text(
        json.dumps(
            {
                "meta": {"schema_version": "1", "last_updated": "2026-02-24"},
                "items": backlog_items,
            }
        ),
        encoding="utf-8",
    )
    setpoints_path.write_text(
        json.dumps(
            {
                "meta": {"schema_version": "1", "last_updated": "2026-02-24"},
                "setpoints": [
                    {
                        "id": "SP-003",
                        "name": "Median issue-to-validated cycle time (days)",
                        "metric": "median_cycle_time_days",
                        "source": "backlog_audit",
                        "current_value": sp003_value,
                        "unit": "days",
                        "target": {"operator": "<=", "value": 7},
                        "status": sp003_status,
                        "owner_role": "controller",
                        "deadline": "2026-04-30",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return backlog_path, setpoints_path


def test_apply_sp003_metric_sets_unknown_when_no_samples(tmp_path: Path):
    backlog_items = [
        {
            "id": "BL-001",
            "status": "active",
            "linked_setpoints": ["SP-003"],
            "created_on": "2026-02-24",
            "updated_on": "2026-02-24",
        }
    ]
    backlog_path, setpoints_path = build_sources(tmp_path, backlog_items, sp003_value=4.0, sp003_status="on_track")
    backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    setpoints = json.loads(setpoints_path.read_text(encoding="utf-8"))

    updated, changed = apply_sp003_metric(backlog, setpoints)

    sp003 = updated["setpoints"][0]
    assert changed
    assert sp003["current_value"] == 0.0
    assert sp003["status"] == "unknown"


def test_apply_sp003_metric_computes_median_from_closed_items(tmp_path: Path):
    backlog_items = [
        {
            "id": "BL-001",
            "status": "closed",
            "linked_setpoints": ["SP-003"],
            "created_on": "2026-02-20",
            "updated_on": "2026-02-24",
        },
        {
            "id": "BL-002",
            "status": "closed",
            "linked_setpoints": ["SP-003"],
            "created_on": "2026-02-21",
            "updated_on": "2026-02-24",
        },
        {
            "id": "BL-003",
            "status": "closed",
            "linked_setpoints": ["SP-003"],
            "created_on": "2026-02-19",
            "updated_on": "2026-02-24",
        },
    ]
    backlog_path, setpoints_path = build_sources(tmp_path, backlog_items)
    backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    setpoints = json.loads(setpoints_path.read_text(encoding="utf-8"))

    updated, changed = apply_sp003_metric(backlog, setpoints)

    sp003 = updated["setpoints"][0]
    assert changed
    assert sp003["current_value"] == 4.0
    assert sp003["status"] == "on_track"


def test_apply_sp003_metric_sets_at_risk_when_target_breached(tmp_path: Path):
    backlog_items = [
        {
            "id": "BL-001",
            "status": "validated",
            "linked_setpoints": ["SP-003"],
            "created_on": "2026-01-01",
            "updated_on": "2026-01-20",
        }
    ]
    backlog_path, setpoints_path = build_sources(tmp_path, backlog_items)
    backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    setpoints = json.loads(setpoints_path.read_text(encoding="utf-8"))

    updated, _ = apply_sp003_metric(backlog, setpoints)

    sp003 = updated["setpoints"][0]
    assert sp003["current_value"] == 19.0
    assert sp003["status"] == "at_risk"
