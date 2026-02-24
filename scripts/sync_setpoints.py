"""Compute and sync derived setpoint metrics from backlog evidence."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG_PATH = ROOT / ".control-loop" / "backlog.json"
DEFAULT_SETPOINTS_PATH = ROOT / ".control-loop" / "setpoints.json"


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"Missing {label}: {path.as_posix()}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {label} {path.as_posix()}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object: {path.as_posix()}")
    return data


def parse_iso_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def compare_target(value: float, operator: str, target_value: float) -> bool:
    if operator == ">=":
        return value >= target_value
    if operator == "<=":
        return value <= target_value
    if operator == "==":
        return value == target_value
    if operator == ">":
        return value > target_value
    if operator == "<":
        return value < target_value
    return False


def lifecycle_cycle_samples(backlog_data: dict[str, Any]) -> list[float]:
    items = backlog_data.get("items", [])
    if not isinstance(items, list):
        return []

    samples: list[float] = []
    valid_statuses = {"validated", "closed"}
    for item in items:
        if not isinstance(item, dict):
            continue
        linked = item.get("linked_setpoints", [])
        if not isinstance(linked, list) or "SP-003" not in linked:
            continue
        status = str(item.get("status", "")).lower()
        if status not in valid_statuses:
            continue
        start = parse_iso_date(item.get("created_on"))
        end = parse_iso_date(item.get("updated_on"))
        if start is None or end is None or end < start:
            continue
        samples.append(float((end - start).days))

    return samples


def apply_sp003_metric(
    backlog_data: dict[str, Any],
    setpoints_data: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    updated = deepcopy(setpoints_data)
    setpoints = updated.get("setpoints")
    if not isinstance(setpoints, list):
        raise ValueError("setpoints file must define 'setpoints' as an array.")

    sp003: dict[str, Any] | None = None
    for item in setpoints:
        if isinstance(item, dict) and item.get("id") == "SP-003":
            sp003 = item
            break
    if sp003 is None:
        raise ValueError("SP-003 not found in setpoints file.")

    samples = lifecycle_cycle_samples(backlog_data)
    target = sp003.get("target", {})
    operator = str(target.get("operator", "<="))
    target_value = float(target.get("value", 7))

    if not samples:
        computed_value = 0.0
        computed_status = "unknown"
    else:
        computed_value = float(median(samples))
        if compare_target(computed_value, operator, target_value):
            computed_status = "on_track"
        else:
            computed_status = "at_risk"

    changed = False
    current_value = sp003.get("current_value")
    if not isinstance(current_value, (int, float)) or float(current_value) != computed_value:
        sp003["current_value"] = computed_value
        changed = True
    current_status = str(sp003.get("status", ""))
    if current_status != computed_status:
        sp003["status"] = computed_status
        changed = True

    meta = updated.get("meta")
    if changed and isinstance(meta, dict):
        meta["last_updated"] = date.today().isoformat()

    return updated, changed


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync derived setpoint metrics.")
    parser.add_argument("--backlog", default=str(DEFAULT_BACKLOG_PATH), help="Path to backlog JSON file.")
    parser.add_argument("--setpoints", default=str(DEFAULT_SETPOINTS_PATH), help="Path to setpoints JSON file.")
    parser.add_argument("--write", action="store_true", help="Write updated setpoints file when drift exists.")
    parser.add_argument("--check", action="store_true", help="Fail when derived setpoint values drift.")
    args = parser.parse_args()

    backlog_path = Path(args.backlog)
    setpoints_path = Path(args.setpoints)

    try:
        backlog_data = load_json(backlog_path, "backlog file")
        setpoints_data = load_json(setpoints_path, "setpoints file")
        expected, changed = apply_sp003_metric(backlog_data, setpoints_data)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    expected_text = json.dumps(expected, indent=2, ensure_ascii=True) + "\n"
    current_text = setpoints_path.read_text(encoding="utf-8")

    if args.write:
        if normalize(current_text) != normalize(expected_text):
            setpoints_path.write_text(expected_text, encoding="utf-8")
            print(f"WROTE: {setpoints_path}")
        else:
            print("PASS: setpoints already in sync")
        return 0

    if args.check:
        if normalize(current_text) != normalize(expected_text):
            print("FAIL: setpoints drift detected for derived metrics")
            print("Run: python scripts/sync_setpoints.py --write")
            return 1
        print("PASS: setpoints derived metrics are in sync")
        return 0

    if changed:
        print("INFO: derived setpoint drift detected")
    else:
        print("INFO: setpoints are already aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
