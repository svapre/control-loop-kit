# Quickstart

## Install in a project
```powershell
git submodule add https://github.com/svapre/control-loop-kit.git tooling/control-loop-kit
git -C tooling/control-loop-kit fetch --tags
git -C tooling/control-loop-kit checkout v0.6.3
```

Before making changes, read `tooling/control-loop-kit/AGENTS.md`.

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
- `docs/POLICY_TEMPLATE.json`
- `docs/BACKLOG_TEMPLATE.json`
- `docs/SETPOINTS_TEMPLATE.json`
- `docs/CONTRACTS_TEMPLATE.json`
- `docs/CONTEXT_INDEX_TEMPLATE.md`
- `docs/SESSION_TEMPLATE.md`
- `docs/ROADMAP_TEMPLATE.md`
- `docs/CONTROL_DASHBOARD_TEMPLATE.md`

## New project setup (greenfield)
Create/copy these starter files in your project root:
- `.control-loop/policy.json` from `docs/POLICY_TEMPLATE.json`
- `.control-loop/ai_settings.json` from `docs/AI_SETTINGS_TEMPLATE.json`
- `.control-loop/backlog.json` from `docs/BACKLOG_TEMPLATE.json`
- `.control-loop/setpoints.json` from `docs/SETPOINTS_TEMPLATE.json`
- `.control-loop/contracts.json` from `docs/CONTRACTS_TEMPLATE.json`
- `docs/ROADMAP.md` from `docs/ROADMAP_TEMPLATE.md`
- `docs/CONTROL_DASHBOARD.md` from `docs/CONTROL_DASHBOARD_TEMPLATE.md`
- `docs/CONTEXT_INDEX.md` from `docs/CONTEXT_INDEX_TEMPLATE.md`
- `docs/sessions/TEMPLATE.md` from `docs/SESSION_TEMPLATE.md`

Replace all `YYYY-MM-DD` placeholders with real dates.

Run verification checks:
```powershell
python scripts/validate_backlog.py --check --backlog .control-loop/backlog.json --setpoints .control-loop/setpoints.json --roadmap docs/ROADMAP.md
python scripts/sync_setpoints.py --check --backlog .control-loop/backlog.json --setpoints .control-loop/setpoints.json
python scripts/render_dashboard.py --check --backlog .control-loop/backlog.json --setpoints .control-loop/setpoints.json --roadmap docs/ROADMAP.md --dashboard docs/CONTROL_DASHBOARD.md
python scripts/validate_onboarding_docs.py --check
python scripts/validate_release_hygiene.py --check --allow-unreleased-latest
```

Add these project files:
- `docs/CONTEXT_INDEX.md`
- `docs/sessions/README.md`
- `docs/sessions/TEMPLATE.md`
- `.control-loop/setpoints.json`
- `.control-loop/backlog.json`
- `.control-loop/contracts.json`
- `docs/ROADMAP.md`
- `docs/CONTROL_DASHBOARD.md`

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
python scripts/validate_backlog.py --check
python scripts/sync_setpoints.py --check
python scripts/render_dashboard.py --check
python scripts/validate_onboarding_docs.py --check
python scripts/validate_release_hygiene.py --check --allow-unreleased-latest
python scripts/generate_model_catalog_prompt.py --check
```

## Execution Harness v1
Use harness commands to create session evidence and run phase-specific checks locally.

```powershell
python -m control_loop.harness start --phase think --task "plan next change"
python -m control_loop.harness run --phase think --latest

python -m control_loop.harness start --phase implement --task "apply approved change"
python -m control_loop.harness run --phase implement --latest
python -m control_loop.harness finalize --latest --result pass --note "completed"
```
