# Gate Suites

This document defines the two-controller gate suites for this repository.
Stage0 is the pinned, trusted controller used as the external judge.
Stage1 is the editable candidate controller being validated for promotion.

## Stage0 Minimum Gate Suite
These commands are the stable baseline gates that Stage0 (trusted controller) must run:

1. `python scripts/generate_model_catalog_prompt.py --check` - verify deterministic prompt generation is in sync.
2. `python scripts/validate_backlog.py --check` - enforce backlog/setpoint contract consistency.
3. `python scripts/render_dashboard.py --check` - verify dashboard output is deterministic and up to date.
4. `ruff check .` - enforce static lint baseline.
5. `pytest -q` - enforce executable behavior contracts.

## Stage1 Full Gate Suite
These commands are the current full candidate-controller gates:

1. `python scripts/generate_model_catalog_prompt.py --check`
2. `python scripts/validate_backlog.py --check`
3. `python scripts/sync_setpoints.py --check`
4. `python scripts/render_dashboard.py --check`
5. `python scripts/validate_onboarding_docs.py --check`
6. `python scripts/validate_release_hygiene.py --check --allow-unreleased-latest`
7. `ruff check .`
8. `pytest -q`

## Promotion Rule
Promote Stage1 to a new Stage0 tag only when:

1. Stage0 Minimum Gate Suite is green.
2. Stage1 Full Gate Suite is green.
3. Human approval is granted.
4. A new release tag is created.

## Local Run (Windows)
Example runner paths:

- Stage0 runner: `D:\UPSC\venvs\clk-stage0-v064\Scripts\python.exe`
- Stage1 runner: `D:\UPSC\venvs\clk-stage1\Scripts\python.exe`

Example command pattern (run from `D:\UPSC\control-loop-kit`):

- `& 'D:\UPSC\venvs\clk-stage1\Scripts\python.exe' scripts/validate_backlog.py --check`
