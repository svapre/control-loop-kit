# Toolkit AI Entry Point

This file is the single starting point for any AI agent working in this repository.

## Mission
- Keep this repository as an AI-agnostic process toolkit.
- Improve process reliability through executable checks.
- Avoid project-specific hardcoding in toolkit defaults.

## Mandatory Read Order
Read these files in order before planning or editing:
1. `README.md`
2. `docs/CONTROL_TOOLKIT_GUIDE.md`
3. `docs/QUICKSTART.md`
4. `docs/POLICY_SCHEMA.md`
5. `.control-loop/policy.json`
6. `.control-loop/ai_settings.json`
7. `docs/USER_CONTEXT.md`
8. `docs/CONTEXT_INDEX.md`
9. `docs/ROADMAP.md`
10. `docs/CONTROL_DASHBOARD.md`
11. `.control-loop/backlog.json`
12. `.control-loop/setpoints.json`
13. `.control-loop/contracts.json`

## Operating Rules
- Work in two phases:
  - think: analyze and propose
  - implement: edit files and run checks
- Before implementation, state planned changes clearly and get user confirmation.
- If a requirement is ambiguous, ask instead of assuming.
- Keep toolkit policy generic; put project-specific rules in project overrides.

## Required Validation Before Completion Claim
Run and report:
- `python scripts/generate_model_catalog_prompt.py --check`
- `python scripts/validate_backlog.py --check`
- `python scripts/sync_setpoints.py --check`
- `python scripts/render_dashboard.py --check`
- `python scripts/validate_onboarding_docs.py --check`
- `python scripts/validate_release_hygiene.py --check --allow-unreleased-latest`
- `python -m ruff check .`
- `python -m pytest -q`

## Output Requirement
- Report what changed, what checks passed, and any remaining risks.
