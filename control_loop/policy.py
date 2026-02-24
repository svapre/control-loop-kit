"""Policy loading utilities for control-loop toolkit."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any

DEFAULT_POLICY_FILE = Path(__file__).with_name("default_policy.json")


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


def load_policy(policy_path: str | None = None, repo_root: Path | None = None) -> dict[str, Any]:
    base_policy = read_json(DEFAULT_POLICY_FILE)

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
        return deep_merge(base_policy, override_policy)

    return base_policy

