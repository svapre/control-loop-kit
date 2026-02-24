"""Render or sync-check the control dashboard from backlog/setpoints data."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .validate_backlog import (
        DEFAULT_BACKLOG_PATH,
        DEFAULT_ROADMAP_PATH,
        DEFAULT_SETPOINTS_PATH,
        validate_artifacts,
    )
except ImportError:
    from validate_backlog import (
        DEFAULT_BACKLOG_PATH,
        DEFAULT_ROADMAP_PATH,
        DEFAULT_SETPOINTS_PATH,
        validate_artifacts,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DASHBOARD_PATH = ROOT / "docs" / "CONTROL_DASHBOARD.md"


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def setpoint_target_label(item: dict[str, Any]) -> str:
    target = item.get("target", {})
    if not isinstance(target, dict):
        return "UNKNOWN"
    operator = target.get("operator", "?")
    value = target.get("value", "?")
    unit = item.get("unit")
    suffix = f" {unit}" if isinstance(unit, str) and unit else ""
    return f"{operator} {value}{suffix}"


def source_snapshot_label(backlog_data: dict[str, Any], setpoints_data: dict[str, Any]) -> str:
    backlog_stamp = "UNKNOWN"
    setpoint_stamp = "UNKNOWN"
    backlog_meta = backlog_data.get("meta")
    if isinstance(backlog_meta, dict) and isinstance(backlog_meta.get("last_updated"), str):
        backlog_stamp = backlog_meta["last_updated"]
    setpoint_meta = setpoints_data.get("meta")
    if isinstance(setpoint_meta, dict) and isinstance(setpoint_meta.get("last_updated"), str):
        setpoint_stamp = setpoint_meta["last_updated"]
    return f"backlog={backlog_stamp}, setpoints={setpoint_stamp}"


def render_dashboard(
    backlog_data: dict[str, Any],
    setpoints_data: dict[str, Any],
    roadmap_data: dict[str, list[str]],
) -> str:
    items = backlog_data.get("items", [])
    setpoints = setpoints_data.get("setpoints", [])
    item_by_id = {item["id"]: item for item in items if isinstance(item, dict) and "id" in item}
    snapshot = source_snapshot_label(backlog_data, setpoints_data)
    open_items = [item for item in items if item.get("status") not in {"closed", "cancelled"}]
    active = [item for item in items if item.get("status") == "active"]
    blocked = [item for item in items if item.get("status") == "blocked"]
    blockers = [item for item in open_items if bool(item.get("is_blocker"))]
    counts = Counter([str(item.get("status")) for item in items])

    sorted_queue = sorted(
        open_items,
        key=lambda item: (-int(item.get("priority_score", 0)), str(item.get("id"))),
    )
    top_queue = sorted_queue[:5]

    lines: list[str] = []
    lines.append("# Control Dashboard")
    lines.append("")
    lines.append(f"- Source snapshot: `{snapshot}`")
    lines.append(f"- Open backlog items: `{len(open_items)}`")
    lines.append(f"- Active items: `{len(active)}`")
    lines.append(f"- Blocked items: `{len(blocked)}`")
    lines.append(f"- Blocker items: `{len(blockers)}`")
    lines.append("")
    lines.append("## Status Breakdown")
    for status in sorted(counts):
        lines.append(f"- `{status}`: `{counts[status]}`")
    lines.append("")
    lines.append("## Setpoint Health")
    lines.append("| ID | Name | Current | Target | Status |")
    lines.append("|---|---|---:|---:|---|")
    for item in setpoints:
        lines.append(
            f"| {item['id']} | {item['name']} | {item['current_value']} | "
            f"{setpoint_target_label(item)} | {item['status']} |"
        )
    lines.append("")
    lines.append("## Top Priority Queue")
    if not top_queue:
        lines.append("- No open backlog items.")
    for item in top_queue:
        lines.append(
            f"- `{item['id']}` ({item['roadmap_lane']}, score={item['priority_score']}): "
            f"{item['title']} -> next: {item['next_action']}"
        )
    lines.append("")
    lines.append("## Roadmap Snapshot")
    section_names = [("now", "Now"), ("next", "Next"), ("later", "Later")]
    for key, heading in section_names:
        lines.append(f"### {heading}")
        ids = roadmap_data.get(key, [])
        for item_id in ids:
            item = item_by_id.get(item_id)
            if item is None:
                lines.append(f"- `{item_id}`: UNKNOWN")
                continue
            lines.append(f"- `{item_id}` ({item['status']}): {item['title']}")
    lines.append("")
    lines.append("## Immediate Focus")
    if blockers:
        for item in sorted(
            blockers,
            key=lambda entry: (-int(entry.get("priority_score", 0)), str(entry.get("id"))),
        ):
            lines.append(f"- `{item['id']}`: {item['title']}")
    else:
        lines.append("- No blocker items currently open.")
    lines.append("")
    lines.append("## Data Sources")
    lines.append("- `.control-loop/backlog.json`")
    lines.append("- `.control-loop/setpoints.json`")
    lines.append("- `docs/ROADMAP.md`")
    lines.append("")
    return "\n".join(lines)


def is_dashboard_synced(
    backlog_path: Path,
    setpoints_path: Path,
    roadmap_path: Path,
    dashboard_path: Path,
) -> tuple[bool, str]:
    failures, backlog_data, setpoints_data, roadmap_data = validate_artifacts(
        backlog_path,
        setpoints_path,
        roadmap_path,
    )
    if failures:
        detail = "; ".join(failures)
        return False, f"Validation failed before dashboard render: {detail}"

    expected = render_dashboard(backlog_data, setpoints_data, roadmap_data)
    if not dashboard_path.exists():
        return False, f"Dashboard file not found: {dashboard_path.as_posix()}"
    current = dashboard_path.read_text(encoding="utf-8")
    if normalize(current) != normalize(expected):
        return False, "Dashboard file is out of sync with backlog/setpoints/roadmap."
    return True, "Dashboard is in sync."


def write_dashboard(
    backlog_path: Path,
    setpoints_path: Path,
    roadmap_path: Path,
    dashboard_path: Path,
) -> None:
    failures, backlog_data, setpoints_data, roadmap_data = validate_artifacts(
        backlog_path,
        setpoints_path,
        roadmap_path,
    )
    if failures:
        detail = "\n".join([f"- {item}" for item in failures])
        raise ValueError(f"Cannot render dashboard due to validation failures:\n{detail}")
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(render_dashboard(backlog_data, setpoints_data, roadmap_data), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render/sync-check control dashboard.")
    parser.add_argument("--backlog", default=str(DEFAULT_BACKLOG_PATH), help="Path to backlog JSON file.")
    parser.add_argument("--setpoints", default=str(DEFAULT_SETPOINTS_PATH), help="Path to setpoints JSON file.")
    parser.add_argument("--roadmap", default=str(DEFAULT_ROADMAP_PATH), help="Path to roadmap markdown file.")
    parser.add_argument("--dashboard", default=str(DEFAULT_DASHBOARD_PATH), help="Path to dashboard markdown file.")
    parser.add_argument("--write", action="store_true", help="Write dashboard markdown file.")
    parser.add_argument("--check", action="store_true", help="Check if dashboard file is in sync.")
    args = parser.parse_args()

    backlog_path = Path(args.backlog)
    setpoints_path = Path(args.setpoints)
    roadmap_path = Path(args.roadmap)
    dashboard_path = Path(args.dashboard)

    if args.write:
        try:
            write_dashboard(backlog_path, setpoints_path, roadmap_path, dashboard_path)
        except ValueError as exc:
            print(f"FAIL: {exc}")
            return 1
        print(f"WROTE: {dashboard_path}")
        return 0

    if args.check:
        synced, message = is_dashboard_synced(backlog_path, setpoints_path, roadmap_path, dashboard_path)
        if not synced:
            print(f"FAIL: {message}")
            print(f"Run: python {Path(__file__).as_posix()} --write")
            return 1
        print(f"PASS: {message}")
        return 0

    failures, backlog_data, setpoints_data, roadmap_data = validate_artifacts(
        backlog_path,
        setpoints_path,
        roadmap_path,
    )
    if failures:
        print("FAIL: validation failed before rendering")
        for item in failures:
            print(f"- {item}")
        return 1
    print(render_dashboard(backlog_data, setpoints_data, roadmap_data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
