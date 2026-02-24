"""Validate control backlog, setpoints, and roadmap coupling."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG_PATH = ROOT / ".control-loop" / "backlog.json"
DEFAULT_SETPOINTS_PATH = ROOT / ".control-loop" / "setpoints.json"
DEFAULT_ROADMAP_PATH = ROOT / "docs" / "ROADMAP.md"

SETPOINT_ID_PATTERN = re.compile(r"^SP-\d{3}$")
BACKLOG_ID_PATTERN = re.compile(r"^BL-\d{3}$")
ROADMAP_ITEM_PATTERN = re.compile(r"^- (BL-\d{3})\b")

ALLOWED_SETPOINT_STATUS = {"unknown", "on_track", "at_risk", "off_track"}
ALLOWED_TARGET_OPERATORS = {">=", "<=", "==", ">", "<"}
ALLOWED_ITEM_TYPES = {"issue", "suggestion", "future_plan"}
ALLOWED_ITEM_STATUS = {
    "captured",
    "triaged",
    "planned",
    "active",
    "blocked",
    "validated",
    "closed",
    "stale",
    "cancelled",
}
ALLOWED_ROADMAP_LANES = {"now", "next", "later"}
ALLOWED_STRENGTH = {"low", "medium", "high"}
ALLOWED_EFFORT = {"small", "medium", "large"}

ERROR_REDUCTION_SCORE = {"low": 1, "medium": 3, "high": 5}
CONFIDENCE_SCORE = {"low": 1, "medium": 3, "high": 5}
EFFORT_SCORE = {"small": 1, "medium": 3, "large": 5}


def load_json_file(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not path.exists():
        return None, [f"Missing {label}: {path.as_posix()}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON in {label} {path.as_posix()}: {exc}"]
    if not isinstance(data, dict):
        return None, [f"{label} must be a JSON object: {path.as_posix()}"]
    return data, failures


def required_fields_missing(item: dict[str, Any], required: set[str]) -> list[str]:
    return sorted([field for field in required if field not in item])


def compute_priority_score(item: dict[str, Any]) -> int:
    reduction = ERROR_REDUCTION_SCORE[str(item["expected_error_reduction"])]
    confidence = CONFIDENCE_SCORE[str(item["confidence"])]
    effort = EFFORT_SCORE[str(item["effort"])]
    blocker = 2 if bool(item["is_blocker"]) else 1
    raw = blocker * reduction * confidence / effort
    return round(raw * 10)


def validate_setpoints(data: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    failures: list[str] = []
    setpoints = data.get("setpoints")
    if not isinstance(setpoints, list):
        return ["Setpoints file must define 'setpoints' as an array."], {}

    by_id: dict[str, dict[str, Any]] = {}
    required = {
        "id",
        "name",
        "metric",
        "source",
        "status",
        "owner_role",
        "deadline",
        "current_value",
        "target",
    }

    for idx, item in enumerate(setpoints):
        label = f"setpoints[{idx}]"
        if not isinstance(item, dict):
            failures.append(f"{label} must be an object.")
            continue
        missing = required_fields_missing(item, required)
        if missing:
            failures.append(f"{label} missing required fields: {', '.join(missing)}")
            continue

        sp_id = str(item["id"])
        if not SETPOINT_ID_PATTERN.match(sp_id):
            failures.append(f"{label} has invalid id '{sp_id}' (expected SP-###).")
        elif sp_id in by_id:
            failures.append(f"Duplicate setpoint id: {sp_id}")
        else:
            by_id[sp_id] = item

        status = str(item["status"])
        if status not in ALLOWED_SETPOINT_STATUS:
            failures.append(
                f"{label} has invalid status '{status}' (allowed: {sorted(ALLOWED_SETPOINT_STATUS)})."
            )

        target = item.get("target")
        if not isinstance(target, dict):
            failures.append(f"{label} target must be an object.")
            continue
        operator = target.get("operator")
        value = target.get("value")
        if operator not in ALLOWED_TARGET_OPERATORS:
            failures.append(
                f"{label} target.operator '{operator}' invalid (allowed: {sorted(ALLOWED_TARGET_OPERATORS)})."
            )
        if not isinstance(value, (int, float)):
            failures.append(f"{label} target.value must be numeric.")

    return failures, by_id


def validate_backlog(data: dict[str, Any], setpoint_ids: set[str]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    failures: list[str] = []
    items = data.get("items")
    if not isinstance(items, list):
        return ["Backlog file must define 'items' as an array."], {}

    by_id: dict[str, dict[str, Any]] = {}
    required = {
        "id",
        "title",
        "type",
        "status",
        "roadmap_lane",
        "linked_setpoints",
        "is_blocker",
        "expected_error_reduction",
        "confidence",
        "effort",
        "priority_score",
        "owner_role",
        "next_action",
        "acceptance_checks",
        "created_on",
        "updated_on",
    }

    active_count = 0
    for idx, item in enumerate(items):
        label = f"items[{idx}]"
        if not isinstance(item, dict):
            failures.append(f"{label} must be an object.")
            continue
        missing = required_fields_missing(item, required)
        if missing:
            failures.append(f"{label} missing required fields: {', '.join(missing)}")
            continue

        item_id = str(item["id"])
        if not BACKLOG_ID_PATTERN.match(item_id):
            failures.append(f"{label} has invalid id '{item_id}' (expected BL-###).")
        elif item_id in by_id:
            failures.append(f"Duplicate backlog id: {item_id}")
        else:
            by_id[item_id] = item

        item_type = str(item["type"])
        status = str(item["status"])
        lane = str(item["roadmap_lane"])
        reduction = str(item["expected_error_reduction"])
        confidence = str(item["confidence"])
        effort = str(item["effort"])

        if item_type not in ALLOWED_ITEM_TYPES:
            failures.append(f"{label} has invalid type '{item_type}' (allowed: {sorted(ALLOWED_ITEM_TYPES)}).")
        if status not in ALLOWED_ITEM_STATUS:
            failures.append(f"{label} has invalid status '{status}' (allowed: {sorted(ALLOWED_ITEM_STATUS)}).")
        if lane not in ALLOWED_ROADMAP_LANES:
            failures.append(f"{label} has invalid roadmap_lane '{lane}' (allowed: {sorted(ALLOWED_ROADMAP_LANES)}).")
        if reduction not in ALLOWED_STRENGTH:
            failures.append(
                f"{label} has invalid expected_error_reduction '{reduction}' (allowed: {sorted(ALLOWED_STRENGTH)})."
            )
        if confidence not in ALLOWED_STRENGTH:
            failures.append(f"{label} has invalid confidence '{confidence}' (allowed: {sorted(ALLOWED_STRENGTH)}).")
        if effort not in ALLOWED_EFFORT:
            failures.append(f"{label} has invalid effort '{effort}' (allowed: {sorted(ALLOWED_EFFORT)}).")

        linked = item.get("linked_setpoints")
        if not isinstance(linked, list) or not linked:
            failures.append(f"{label} must link at least one setpoint via linked_setpoints.")
        else:
            for sp_id in linked:
                if sp_id not in setpoint_ids:
                    failures.append(f"{label} references unknown setpoint id '{sp_id}'.")

        checks = item.get("acceptance_checks")
        if not isinstance(checks, list) or not checks or not all(isinstance(entry, str) for entry in checks):
            failures.append(f"{label} acceptance_checks must be a non-empty string list.")

        score = item.get("priority_score")
        if not isinstance(score, int):
            failures.append(f"{label} priority_score must be an integer.")
        elif reduction in ALLOWED_STRENGTH and confidence in ALLOWED_STRENGTH and effort in ALLOWED_EFFORT:
            expected = compute_priority_score(item)
            if score != expected:
                failures.append(f"{label} priority_score={score} but expected {expected} from scoring rule.")

        if status == "active":
            active_count += 1

    if active_count > 1:
        failures.append("Backlog must have at most one active item to keep execution focused.")

    return failures, by_id


def parse_roadmap(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    failures: list[str] = []
    if not path.exists():
        return {}, [f"Missing roadmap file: {path.as_posix()}"]

    roadmap: dict[str, list[str]] = {"now": [], "next": [], "later": []}
    section_map = {"## Now": "now", "## Next": "next", "## Later": "later"}
    current_section: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped in section_map:
            current_section = section_map[stripped]
            continue
        if current_section is None:
            continue
        match = ROADMAP_ITEM_PATTERN.match(stripped)
        if match:
            roadmap[current_section].append(match.group(1))

    for heading, key in section_map.items():
        if not roadmap[key]:
            failures.append(f"Roadmap section '{heading}' must contain at least one backlog item.")

    return roadmap, failures


def validate_roadmap_links(roadmap: dict[str, list[str]], backlog: dict[str, dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for lane, ids in roadmap.items():
        for item_id in ids:
            if item_id in seen:
                failures.append(f"Roadmap includes duplicate backlog id: {item_id}")
            seen.add(item_id)
            if item_id not in backlog:
                failures.append(f"Roadmap references unknown backlog id: {item_id}")
                continue
            expected_lane = backlog[item_id]["roadmap_lane"]
            if expected_lane != lane:
                failures.append(
                    f"Roadmap places {item_id} in '{lane}' but backlog roadmap_lane is '{expected_lane}'."
                )

    for item_id, item in backlog.items():
        status = item["status"]
        if status in {"closed", "cancelled"}:
            continue
        if item_id not in seen:
            failures.append(f"Active backlog item {item_id} missing from roadmap.")

    return failures


def validate_artifacts(
    backlog_path: Path,
    setpoints_path: Path,
    roadmap_path: Path,
) -> tuple[list[str], dict[str, Any], dict[str, Any], dict[str, list[str]]]:
    failures: list[str] = []

    setpoints_data, setpoints_load_failures = load_json_file(setpoints_path, "setpoints file")
    failures.extend(setpoints_load_failures)
    backlog_data, backlog_load_failures = load_json_file(backlog_path, "backlog file")
    failures.extend(backlog_load_failures)
    roadmap_data, roadmap_failures = parse_roadmap(roadmap_path)
    failures.extend(roadmap_failures)

    if setpoints_data is None or backlog_data is None:
        return failures, {}, {}, roadmap_data

    setpoint_failures, setpoint_map = validate_setpoints(setpoints_data)
    failures.extend(setpoint_failures)
    backlog_failures, backlog_map = validate_backlog(backlog_data, set(setpoint_map))
    failures.extend(backlog_failures)
    failures.extend(validate_roadmap_links(roadmap_data, backlog_map))

    return failures, backlog_data, setpoints_data, roadmap_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control backlog, setpoints, and roadmap coupling.")
    parser.add_argument("--backlog", default=str(DEFAULT_BACKLOG_PATH), help="Path to backlog JSON file.")
    parser.add_argument("--setpoints", default=str(DEFAULT_SETPOINTS_PATH), help="Path to setpoints JSON file.")
    parser.add_argument("--roadmap", default=str(DEFAULT_ROADMAP_PATH), help="Path to roadmap markdown file.")
    parser.add_argument("--check", action="store_true", help="Run checks and fail on validation errors.")
    args = parser.parse_args()

    backlog_path = Path(args.backlog)
    setpoints_path = Path(args.setpoints)
    roadmap_path = Path(args.roadmap)

    failures, _, _, _ = validate_artifacts(backlog_path, setpoints_path, roadmap_path)
    if failures:
        print("FAIL: backlog/setpoint/roadmap validation failed")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PASS: backlog/setpoint/roadmap validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
