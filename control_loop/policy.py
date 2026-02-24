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
ALLOWED_ENFORCEMENT_MODES = {"strict", "advisory"}
ALLOWED_RESPONSE_DETAIL_LEVELS = {"short", "normal", "detailed"}
ALLOWED_LANGUAGE_STYLES = {"simple", "mixed", "technical"}
ALLOWED_EXPLANATION_STYLES = {"action_only", "action_reason", "teaching"}
ALLOWED_PROGRESS_UPDATE_STYLES = {"minimal", "frequent", "silent_until_done"}
ALLOWED_ASSUMPTION_POLICIES = {"ask_first", "low_risk_allowed"}
ALLOWED_BRAINSTORM_RULE_STRICTNESS = {"strict", "flexible"}
ALLOWED_RULE_ENFORCEMENTS = {"strict", "warn", "manual_review"}


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


def _assert_string_enum(obj: dict[str, Any], key: str, values: set[str], context: str) -> None:
    if key not in obj:
        return
    value = obj[key]
    if not isinstance(value, str) or value not in values:
        raise ValueError(f"{context}.{key} must be one of {sorted(values)}")


def _assert_bool(obj: dict[str, Any], key: str, context: str) -> None:
    if key not in obj:
        return
    value = obj[key]
    if not isinstance(value, bool):
        raise ValueError(f"{context}.{key} must be a boolean")


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

    phase_rules = process_policy.get("execution_phase_rules")
    if phase_rules is not None:
        if not isinstance(phase_rules, dict):
            raise ValueError(f"{context}.process_guard.execution_phase_rules must be an object")
        _assert_list_of_strings(phase_rules, "allowed_phases", f"{context}.process_guard.execution_phase_rules")
        _assert_list_of_strings(phase_rules, "allowed_scopes", f"{context}.process_guard.execution_phase_rules")
        _assert_list_of_strings(phase_rules, "toolkit_prefixes", f"{context}.process_guard.execution_phase_rules")
        for key in [
            "phase_field",
            "change_scope_field",
            "implementation_approval_token_field",
            "required_implementation_approval_token",
        ]:
            if key in phase_rules and not isinstance(phase_rules[key], str):
                raise ValueError(f"{context}.process_guard.execution_phase_rules.{key} must be a string")

    design_rules = process_policy.get("design_principle_rules")
    if design_rules is not None:
        if not isinstance(design_rules, dict):
            raise ValueError(f"{context}.process_guard.design_principle_rules must be an object")
        _assert_list_of_strings(
            design_rules,
            "null_tokens",
            f"{context}.process_guard.design_principle_rules",
        )
        rules = design_rules.get("required_value_rules")
        if rules is not None:
            if not isinstance(rules, list):
                raise ValueError(
                    f"{context}.process_guard.design_principle_rules.required_value_rules must be an array"
                )
            for idx, item in enumerate(rules):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"{context}.process_guard.design_principle_rules.required_value_rules[{idx}] must be an object"
                    )
                field = item.get("field")
                enforcement = item.get("enforcement", "strict")
                if not isinstance(field, str) or not field.strip():
                    raise ValueError(
                        f"{context}.process_guard.design_principle_rules.required_value_rules[{idx}].field "
                        "must be a non-empty string"
                    )
                if not isinstance(enforcement, str) or enforcement not in ALLOWED_RULE_ENFORCEMENTS:
                    raise ValueError(
                        f"{context}.process_guard.design_principle_rules.required_value_rules[{idx}].enforcement "
                        f"must be one of {sorted(ALLOWED_RULE_ENFORCEMENTS)}"
                    )

    static_rules = process_policy.get("static_guard_rules")
    if static_rules is not None:
        if not isinstance(static_rules, dict):
            raise ValueError(f"{context}.process_guard.static_guard_rules must be an object")
        _assert_list_of_strings(static_rules, "scan_extensions", f"{context}.process_guard.static_guard_rules")
        _assert_list_of_strings(static_rules, "include_prefixes", f"{context}.process_guard.static_guard_rules")
        _assert_list_of_strings(static_rules, "include_files", f"{context}.process_guard.static_guard_rules")
        rules = static_rules.get("rules")
        if rules is not None:
            if not isinstance(rules, list):
                raise ValueError(f"{context}.process_guard.static_guard_rules.rules must be an array")
            for idx, item in enumerate(rules):
                if not isinstance(item, dict):
                    raise ValueError(
                        f"{context}.process_guard.static_guard_rules.rules[{idx}] must be an object"
                    )
                pattern = item.get("pattern")
                enforcement = item.get("enforcement", "strict")
                if not isinstance(pattern, str) or not pattern.strip():
                    raise ValueError(
                        f"{context}.process_guard.static_guard_rules.rules[{idx}].pattern must be a non-empty string"
                    )
                if not isinstance(enforcement, str) or enforcement not in ALLOWED_RULE_ENFORCEMENTS:
                    raise ValueError(
                        f"{context}.process_guard.static_guard_rules.rules[{idx}].enforcement "
                        f"must be one of {sorted(ALLOWED_RULE_ENFORCEMENTS)}"
                    )


def validate_ai_settings_loader(loader: dict[str, Any], context: str) -> None:
    if not isinstance(loader, dict):
        raise ValueError(f"{context}.ai_settings_loader must be an object")
    if "default_path" in loader and not isinstance(loader["default_path"], str):
        raise ValueError(f"{context}.ai_settings_loader.default_path must be a string")
    if "env_var" in loader and not isinstance(loader["env_var"], str):
        raise ValueError(f"{context}.ai_settings_loader.env_var must be a string")


def validate_ai_settings(settings: dict[str, Any], context: str) -> None:
    if not isinstance(settings, dict):
        raise ValueError(f"{context}.ai_settings must be an object")

    global_switch = settings.get("global_switch")
    if global_switch is not None:
        if not isinstance(global_switch, dict):
            raise ValueError(f"{context}.ai_settings.global_switch must be an object")
        _assert_bool(global_switch, "enabled", f"{context}.ai_settings.global_switch")
        _assert_string_enum(
            global_switch,
            "mode",
            ALLOWED_ENFORCEMENT_MODES,
            f"{context}.ai_settings.global_switch",
        )
        _assert_bool(
            global_switch,
            "require_waiver_when_disabled",
            f"{context}.ai_settings.global_switch",
        )

        enabled = global_switch.get("enabled", True)
        require_waiver = global_switch.get("require_waiver_when_disabled", False)
        if not enabled and require_waiver:
            waiver = global_switch.get("waiver")
            if not isinstance(waiver, dict):
                raise ValueError(
                    f"{context}.ai_settings.global_switch.waiver must be provided when disabled and waiver is required"
                )
            for field in ["reason", "approved_by", "expires_on"]:
                value = waiver.get(field)
                if (
                    not isinstance(value, str)
                    or not value.strip()
                    or value.strip().lower() in {"n/a", "na", "none"}
                ):
                    raise ValueError(
                        f"{context}.ai_settings.global_switch.waiver.{field} must be a non-empty string"
                    )

    response = settings.get("response")
    if response is not None:
        if not isinstance(response, dict):
            raise ValueError(f"{context}.ai_settings.response must be an object")
        _assert_string_enum(
            response,
            "detail_level",
            ALLOWED_RESPONSE_DETAIL_LEVELS,
            f"{context}.ai_settings.response",
        )
        _assert_string_enum(
            response,
            "language_style",
            ALLOWED_LANGUAGE_STYLES,
            f"{context}.ai_settings.response",
        )
        _assert_string_enum(
            response,
            "explanation_style",
            ALLOWED_EXPLANATION_STYLES,
            f"{context}.ai_settings.response",
        )
        _assert_string_enum(
            response,
            "progress_update_style",
            ALLOWED_PROGRESS_UPDATE_STYLES,
            f"{context}.ai_settings.response",
        )

    execution = settings.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            raise ValueError(f"{context}.ai_settings.execution must be an object")
        _assert_bool(execution, "confirm_before_changes", f"{context}.ai_settings.execution")
        _assert_string_enum(
            execution,
            "assumption_policy",
            ALLOWED_ASSUMPTION_POLICIES,
            f"{context}.ai_settings.execution",
        )
        _assert_string_enum(
            execution,
            "brainstorming_rule_strictness",
            ALLOWED_BRAINSTORM_RULE_STRICTNESS,
            f"{context}.ai_settings.execution",
        )

    context_management = settings.get("context_management")
    if context_management is not None:
        if not isinstance(context_management, dict):
            raise ValueError(f"{context}.ai_settings.context_management must be an object")
        if "context_index_path" in context_management and not isinstance(context_management["context_index_path"], str):
            raise ValueError(f"{context}.ai_settings.context_management.context_index_path must be a string")
        _assert_list_of_strings(context_management, "required_tiers", f"{context}.ai_settings.context_management")

    session_log = settings.get("session_log")
    if session_log is not None:
        if not isinstance(session_log, dict):
            raise ValueError(f"{context}.ai_settings.session_log must be an object")
        if "root" in session_log and not isinstance(session_log["root"], str):
            raise ValueError(f"{context}.ai_settings.session_log.root must be a string")
        array_keys = [
            "ignored_files",
            "required_for_prefixes",
            "required_for_files",
            "required_sections",
            "required_fields",
            "null_tokens",
        ]
        for key in array_keys:
            _assert_list_of_strings(session_log, key, f"{context}.ai_settings.session_log")
        for key in [
            "user_approval_status_field",
            "user_approval_evidence_field",
            "failure_observed_field",
            "corrective_change_field",
        ]:
            if key in session_log and not isinstance(session_log[key], str):
                raise ValueError(f"{context}.ai_settings.session_log.{key} must be a string")


def validate_policy(policy: dict[str, Any], context: str) -> None:
    validate_override_directive(policy, context)
    if "control_gate" in policy:
        validate_control_gate_policy(policy["control_gate"], context)
    if "process_guard" in policy:
        validate_process_guard_policy(policy["process_guard"], context)
    if "ai_settings_loader" in policy:
        validate_ai_settings_loader(policy["ai_settings_loader"], context)
    if "ai_settings" in policy:
        validate_ai_settings(policy["ai_settings"], context)


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


def _resolve_ai_settings_override_path(effective_policy: dict[str, Any], repo_root: Path) -> Path | None:
    loader = effective_policy.get("ai_settings_loader", {})
    env_name = "CONTROL_LOOP_AI_SETTINGS_PATH"
    if isinstance(loader, dict) and isinstance(loader.get("env_var"), str):
        env_name = loader["env_var"]

    env_override = os.getenv(env_name)
    if env_override:
        return Path(env_override)

    default_path = ".control-loop/ai_settings.json"
    if isinstance(loader, dict) and isinstance(loader.get("default_path"), str):
        default_path = loader["default_path"]

    candidate = Path(default_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    if candidate.exists():
        return candidate
    return None


def _apply_ai_settings_override(effective_policy: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    override_path = _resolve_ai_settings_override_path(effective_policy, repo_root)
    if not override_path:
        return effective_policy

    override_obj = read_json(override_path)
    if "ai_settings" in override_obj:
        override_data = override_obj["ai_settings"]
        if not isinstance(override_data, dict):
            raise ValueError("AI settings override file key 'ai_settings' must be an object")
    else:
        override_data = override_obj

    base_ai = effective_policy.get("ai_settings", {})
    if not isinstance(base_ai, dict):
        raise ValueError("Effective policy ai_settings must be an object")

    merged = deep_merge(base_ai, override_data)
    validate_ai_settings(merged, "effective")

    updated = deepcopy(effective_policy)
    updated["ai_settings"] = merged
    return updated


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

    effective_policy = _apply_ai_settings_override(effective_policy, repo_root)
    validate_policy(effective_policy, "effective")
    return effective_policy
