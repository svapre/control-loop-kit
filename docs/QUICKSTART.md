# Quickstart

## Install in a project
```powershell
git submodule add https://github.com/svapre/control-loop-kit.git tooling/control-loop-kit
git -C tooling/control-loop-kit fetch --tags
git -C tooling/control-loop-kit checkout v0.4.0
```

## Required local wrappers
- `scripts/control_gate.py`
- `scripts/process_guard.py`

Each wrapper should:
1. load toolkit path from `CONTROL_LOOP_KIT_PATH` or `tooling/control-loop-kit`
2. import toolkit module
3. execute `main()`

## Add policy file
Create `.control-loop/policy.json` for project-specific rules.

Create `.control-loop/ai_settings.json` for AI response and process-behavior settings.
Tune design/static guard strictness in `.control-loop/policy.json` using:
- `process_guard.design_principle_rules`
- `process_guard.static_guard_rules`

Default:
- partial override mode

For full override:
- set `policy_override.mode` to `full`
- include waiver metadata (`reason`, `approved_by`, `expires_on`)

Use templates:
- `docs/AI_SETTINGS_TEMPLATE.json`
- `docs/CONTEXT_INDEX_TEMPLATE.md`
- `docs/SESSION_TEMPLATE.md`

Add these project files:
- `docs/CONTEXT_INDEX.md`
- `docs/sessions/README.md`
- `docs/sessions/TEMPLATE.md`

## CI steps
1. checkout repo with `submodules: recursive`
2. install dependencies
3. lint
4. tests
5. `python scripts/process_guard.py --mode ci --base-sha ...`
6. `python scripts/control_gate.py --mode ci`

Toolkit self-check:
- run toolkit CI (`ruff` + `pytest`) in the toolkit repo itself.

## Local verification
```powershell
python -m ruff check .
python -m pytest -q
python scripts/process_guard.py --mode ci
python scripts/control_gate.py --mode ci
python scripts/generate_model_catalog_prompt.py --check
```
