"""Policy loading and validation utilities for control-loop toolkit."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_POLICY_FILE = Path(__file__).with_name("default_policy.json")
ALLOWED_OVERRIDE_MODES = {"partial", "full"}
ALLOWED_WORK_MODES = {"routine", "design"}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def read_json(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Policy file is not an object: {path}")
    return data


def _assert_list_of_strings(obj: dict[str, Any], key: str, context: str) -> None:
    if key not in obj:
        return
    value = obj[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{context}.{key} must be an array of strings")


def validate_override_directive(policy: dict[str, Any], context: str) -> None:
    directive = policy.get("policy_override")
    if directive is None:
        return
    if not isinstance(directive, dict):
        raise ValueError(f"{context}.policy_override must be an object")

    mode = directive.get("mode", "partial")
    if mode not in ALLOWED_OVERRIDE_MODES:
        raise ValueError(f"{context}.policy_override.mode must be one of {sorted(ALLOWED_OVERRIDE_MODES)}")

    if mode == "full":
        waiver = directive.get("waiver")
        if not isinstance(waiver, dict):
            raise ValueError(f"{context}.policy_override.waiver must be provided for full override")
        required_waiver_fields = ["reason", "approved_by", "expires_on"]
        for field in required_waiver_fields:
            if not isinstance(waiver.get(field), str) or not waiver.get(field).strip():
                raise ValueError(f"{context}.policy_override.waiver.{field} must be a non-empty string")


def validate_control_gate_policy(control_policy: dict[str, Any], context: str) -> None:
    if not isinstance(control_policy, dict):
        raise ValueError(f"{context}.control_gate must be an object")

    _assert_list_of_strings(control_policy, "required_files", f"{context}.control_gate")
    _assert_list_of_strings(control_policy, "master_plan_tokens", f"{context}.control_gate")

    readiness_commands = control_policy.get("readiness_commands")
    if readiness_commands is not None:
        if not isinstance(readiness_commands, list):
            raise ValueError(f"{context}.control_gate.readiness_commands must be an array")
        for idx, cmd in enumerate(readiness_commands):
            if not isinstance(cmd, list) or any(not isinstance(token, str) for token in cmd):
                raise ValueError(
                    f"{context}.control_gate.readiness_commands[{idx}] must be an array of command tokens"
                )


def validate_process_guard_policy(process_policy: dict[str, Any], context: str) -> None:
    if not isinstance(process_policy, dict):
        raise ValueError(f"{context}.process_guard must be an object")

    array_keys = [
        "required_process_files",
        "implementation_prefixes",
        "implementation_files",
        "process_controlled_files",
        "proposal_ignored_files",
        "design_update_paths",
        "required_proposal_sections",
        "required_proposal_fields",
        "process_guideline_fields",
        "project_guideline_fields",
    ]
    for key in array_keys:
        _assert_list_of_strings(process_policy, key, f"{context}.process_guard")

    mode_rule = process_policy.get("mode_rule")
    if mode_rule is not None:
        if not isinstance(mode_rule, dict):
            raise ValueError(f"{context}.process_guard.mode_rule must be an object")
        allowed_modes = mode_rule.get("allowed_modes")
        if allowed_modes is not None:
            if not isinstance(allowed_modes, list) or any(not isinstance(item, str) for item in allowed_modes):
                raise ValueError(f"{context}.process_guard.mode_rule.allowed_modes must be an array of strings")
            normalized = {item.lower() for item in allowed_modes}
            if not normalized.issubset(ALLOWED_WORK_MODES):
                raise ValueError(
                    f"{context}.process_guard.mode_rule.allowed_modes must be subset of {sorted(ALLOWED_WORK_MODES)}"
                )

    no_assumption_rule = process_policy.get("no_assumption_rule")
    if no_assumption_rule is not None and not isinstance(no_assumption_rule, dict):
        raise ValueError(f"{context}.process_guard.no_assumption_rule must be an object")


def validate_policy(policy: dict[str, Any], context: str) -> None:
    validate_override_directive(policy, context)
    if "control_gate" in policy:
        validate_control_gate_policy(policy["control_gate"], context)
    if "process_guard" in policy:
        validate_process_guard_policy(policy["process_guard"], context)


def _strip_override_directive(policy: dict[str, Any]) -> dict[str, Any]:
    cleaned = deepcopy(policy)
    cleaned.pop("policy_override", None)
    return cleaned


def _resolve_override_policy(base_policy: dict[str, Any], override_policy: dict[str, Any]) -> dict[str, Any]:
    directive = override_policy.get("policy_override", {})
    mode = directive.get("mode", "partial") if isinstance(directive, dict) else "partial"
    override_clean = _strip_override_directive(override_policy)

    if mode == "full":
        if "control_gate" not in override_clean or "process_guard" not in override_clean:
            raise ValueError("Full override policy must define both control_gate and process_guard sections")
        return override_clean
    return deep_merge(base_policy, override_clean)


def load_policy(policy_path: str | None = None, repo_root: Path | None = None) -> dict[str, Any]:
    base_policy = read_json(DEFAULT_POLICY_FILE)
    validate_policy(base_policy, "base")

    if repo_root is None:
        repo_root = Path.cwd()

    override_candidate: Path | None = None
    if policy_path:
        override_candidate = Path(policy_path)
    elif os.getenv("CONTROL_LOOP_POLICY_PATH"):
        override_candidate = Path(os.environ["CONTROL_LOOP_POLICY_PATH"])
    else:
        candidate = repo_root / ".control-loop" / "policy.json"
        if candidate.exists():
            override_candidate = candidate

    if override_candidate and override_candidate.exists():
        override_policy = read_json(override_candidate)
        validate_policy(override_policy, "override")
        effective_policy = _resolve_override_policy(base_policy, override_policy)
    else:
        effective_policy = base_policy

    validate_policy(effective_policy, "effective")
    return effective_policy
