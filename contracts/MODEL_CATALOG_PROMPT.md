# Model Catalog Collection Prompt

Use this prompt with any AI assistant to produce a model catalog JSON file.

## Purpose
Give this prompt to any AI so it returns model data in the exact contract format.

## Inputs You Provide
- `{AS_OF_DATE_UTC}`
- `{PROVIDER_SCOPE}`
- `{MODEL_SOURCES_OR_FETCH_INSTRUCTION}`

## Required Output Rules
- Return JSON only. Do not include Markdown.
- Output must validate against this contract.
- If a value is unknown, use null and add a short note in the nearest notes field.

## Top-Level Required Keys
- `catalog_version`: `string`
- `generated_at_utc`: `string`
- `source`: `string`
- `models`: `array`
- `routes`: `array`

## JSON Skeleton (contract-aligned)
```json
{
  "catalog_version": "<string>",
  "generated_at_utc": "<string>",
  "source": "<string>",
  "models": [
    {
      "id": "<string>",
      "provider": "<string>",
      "model_name": "<string>",
      "tier": "fast",
      "strengths": [
        "mechanical_edits"
      ],
      "weaknesses": [
        "<string>"
      ],
      "status": "active",
      "context_window_tokens": 1,
      "pricing_hint": {
        "input_per_million_usd": 0.0,
        "output_per_million_usd": 0.0
      },
      "rate_limit_profile": {
        "risk": "low"
      },
      "last_verified_utc": "<string>",
      "source_url": "<string>"
    }
  ],
  "routes": [
    {
      "name": "<string>",
      "intent": [
        "plan"
      ],
      "scope": [
        "docs_only"
      ],
      "risk": [
        "low"
      ],
      "candidate_model_ids": [
        "<string>"
      ],
      "fallback_route": "<string>"
    }
  ]
}
```

## Prompt Text To Send
Copy from START to END.

START
You are preparing a model catalog for task routing.
Return only valid JSON. Do not include Markdown.
Use this exact contract and required keys.
If a value is unknown, set it to null and use a nearby notes field.

Inputs:
- {AS_OF_DATE_UTC}
- {PROVIDER_SCOPE}
- {MODEL_SOURCES_OR_FETCH_INSTRUCTION}

Output must follow this JSON skeleton:
{
  "catalog_version": "<string>",
  "generated_at_utc": "<string>",
  "source": "<string>",
  "models": [
    {
      "id": "<string>",
      "provider": "<string>",
      "model_name": "<string>",
      "tier": "fast",
      "strengths": [
        "mechanical_edits"
      ],
      "weaknesses": [
        "<string>"
      ],
      "status": "active",
      "context_window_tokens": 1,
      "pricing_hint": {
        "input_per_million_usd": 0.0,
        "output_per_million_usd": 0.0
      },
      "rate_limit_profile": {
        "risk": "low"
      },
      "last_verified_utc": "<string>",
      "source_url": "<string>"
    }
  ],
  "routes": [
    {
      "name": "<string>",
      "intent": [
        "plan"
      ],
      "scope": [
        "docs_only"
      ],
      "risk": [
        "low"
      ],
      "candidate_model_ids": [
        "<string>"
      ],
      "fallback_route": "<string>"
    }
  ]
}
END
