"""Generate and sync-check the model-catalog collection prompt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "model_catalog.contract.json"
PROMPT_PATH = ROOT / "contracts" / "MODEL_CATALOG_PROMPT.md"


def load_contract(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Contract must be a JSON object: {path}")
    return data


def resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local refs are supported: {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise ValueError(f"Invalid ref segment '{part}' in ref: {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise ValueError(f"Resolved ref is not an object: {ref}")
    return node


def pick_type(schema: dict[str, Any]) -> str:
    type_value = schema.get("type")
    if isinstance(type_value, list):
        for token in type_value:
            if token != "null":
                return str(token)
        return "null"
    if isinstance(type_value, str):
        return type_value
    return "string"


def schema_placeholder(schema: dict[str, Any], root: dict[str, Any]) -> Any:
    if "$ref" in schema:
        return schema_placeholder(resolve_ref(root, str(schema["$ref"])), root)

    if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
        return schema["enum"][0]

    schema_type = pick_type(schema)
    if schema_type == "object":
        props = schema.get("properties", {})
        required = schema.get("required", [])
        if not isinstance(props, dict) or not isinstance(required, list):
            return {}
        output: dict[str, Any] = {}
        for key in required:
            if key in props and isinstance(props[key], dict):
                output[key] = schema_placeholder(props[key], root)
            else:
                output[key] = "<value>"
        return output

    if schema_type == "array":
        items = schema.get("items")
        if isinstance(items, dict):
            return [schema_placeholder(items, root)]
        return []

    if schema_type == "integer":
        minimum = schema.get("minimum")
        if isinstance(minimum, int):
            return minimum
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return False
    if schema_type == "null":
        return None
    return "<string>"


def schema_type_label(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return f"ref:{schema['$ref']}"
    type_value = schema.get("type")
    if isinstance(type_value, list):
        return " | ".join([str(x) for x in type_value])
    if isinstance(type_value, str):
        return type_value
    return "unknown"


def top_level_lines(contract: dict[str, Any]) -> list[str]:
    properties = contract.get("properties", {})
    required = contract.get("required", [])
    lines: list[str] = []
    if not isinstance(properties, dict) or not isinstance(required, list):
        return lines

    for key in required:
        schema = properties.get(key, {})
        if not isinstance(schema, dict):
            continue
        label = schema_type_label(schema)
        line = f"- `{key}`: `{label}`"
        if "enum" in schema and isinstance(schema["enum"], list):
            values = ", ".join([str(item) for item in schema["enum"]])
            line += f" (allowed: {values})"
        lines.append(line)
    return lines


def render_prompt_text(contract: dict[str, Any]) -> str:
    prompt_cfg = contract.get("prompt_generation", {})
    title = "Model Catalog Collection Prompt"
    purpose = "Collect model metadata and output strict JSON."
    output_rules: list[str] = []
    placeholders: list[str] = []
    if isinstance(prompt_cfg, dict):
        if isinstance(prompt_cfg.get("title"), str):
            title = prompt_cfg["title"]
        if isinstance(prompt_cfg.get("purpose"), str):
            purpose = prompt_cfg["purpose"]
        if isinstance(prompt_cfg.get("output_rules"), list):
            output_rules = [str(item) for item in prompt_cfg["output_rules"]]
        if isinstance(prompt_cfg.get("input_placeholders"), list):
            placeholders = [str(item) for item in prompt_cfg["input_placeholders"]]

    skeleton = schema_placeholder(contract, contract)
    skeleton_text = json.dumps(skeleton, indent=2, ensure_ascii=True)

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("Use this prompt with any AI assistant to produce a model catalog JSON file.")
    lines.append("")
    lines.append("## Purpose")
    lines.append(purpose)
    lines.append("")
    lines.append("## Inputs You Provide")
    if placeholders:
        for item in placeholders:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `<no explicit placeholders configured>`")
    lines.append("")
    lines.append("## Required Output Rules")
    if output_rules:
        for item in output_rules:
            lines.append(f"- {item}")
    else:
        lines.append("- Return JSON only.")
    lines.append("")
    lines.append("## Top-Level Required Keys")
    for line in top_level_lines(contract):
        lines.append(line)
    lines.append("")
    lines.append("## JSON Skeleton (contract-aligned)")
    lines.append("```json")
    lines.append(skeleton_text)
    lines.append("```")
    lines.append("")
    lines.append("## Prompt Text To Send")
    lines.append("Copy from START to END.")
    lines.append("")
    lines.append("START")
    lines.append("You are preparing a model catalog for task routing.")
    lines.append("Return only valid JSON. Do not include Markdown.")
    lines.append("Use this exact contract and required keys.")
    lines.append("If a value is unknown, set it to null and use a nearby notes field.")
    lines.append("")
    lines.append("Inputs:")
    if placeholders:
        for item in placeholders:
            lines.append(f"- {item}")
    else:
        lines.append("- <none>")
    lines.append("")
    lines.append("Output must follow this JSON skeleton:")
    lines.append(skeleton_text)
    lines.append("END")
    lines.append("")
    return "\n".join(lines)


def normalized_text(text: str) -> str:
    return text.replace("\r\n", "\n")


def is_prompt_synced(contract_path: Path, prompt_path: Path) -> tuple[bool, str]:
    contract = load_contract(contract_path)
    expected = render_prompt_text(contract)
    if not prompt_path.exists():
        return False, "Prompt file does not exist."
    current = prompt_path.read_text(encoding="utf-8")
    if normalized_text(current) != normalized_text(expected):
        return False, "Prompt file is out of sync with contract."
    return True, "Prompt file is in sync with contract."


def write_prompt(contract_path: Path, prompt_path: Path) -> None:
    contract = load_contract(contract_path)
    text = render_prompt_text(contract)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate model-catalog prompt from contract.")
    parser.add_argument("--contract", default=str(CONTRACT_PATH), help="Path to model contract JSON file.")
    parser.add_argument("--prompt", default=str(PROMPT_PATH), help="Path to generated prompt markdown file.")
    parser.add_argument("--write", action="store_true", help="Write generated prompt to prompt path.")
    parser.add_argument("--check", action="store_true", help="Check if prompt file is in sync.")
    args = parser.parse_args()

    contract_path = Path(args.contract)
    prompt_path = Path(args.prompt)

    if args.write:
        write_prompt(contract_path, prompt_path)
        print(f"WROTE: {prompt_path}")
        return 0

    if args.check:
        synced, message = is_prompt_synced(contract_path, prompt_path)
        if not synced:
            print(f"FAIL: {message}")
            print(f"Run: python {Path(__file__).as_posix()} --write")
            return 1
        print(f"PASS: {message}")
        return 0

    contract = load_contract(contract_path)
    print(render_prompt_text(contract))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
