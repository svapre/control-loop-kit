from __future__ import annotations

import json

from scripts.generate_model_catalog_prompt import CONTRACT_PATH, PROMPT_PATH, is_prompt_synced


def test_contract_supports_multiple_candidate_models_per_route():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    route_schema = contract["$defs"]["route"]["properties"]["candidate_model_ids"]

    assert route_schema["type"] == "array"
    assert route_schema["minItems"] >= 1
    assert route_schema["uniqueItems"] is True


def test_generated_prompt_is_synced_with_contract():
    synced, message = is_prompt_synced(CONTRACT_PATH, PROMPT_PATH)

    assert synced is True, message

