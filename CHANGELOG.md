# Changelog

## v0.6.4
- Completed BL-005 release hygiene objective:
  - added release checklist (`docs/RELEASE_CHECKLIST.md`),
  - added automated release-hygiene validator (`scripts/validate_release_hygiene.py`),
  - added CI enforcement (`python scripts/validate_release_hygiene.py --check --allow-unreleased-latest`),
  - backfilled missing release tags for `v0.4.0` through `v0.6.3`.
- Added release-hygiene contract tests:
  - `tests/test_release_hygiene_contract.py`.
- Updated backlog state:
  - closed BL-005,
  - activated BL-006 as current focus.

## v0.6.3
- Completed BL-002 contract lifecycle state machine enforcement:
  - validates contract status transitions when `.control-loop/contracts.json` changes,
  - blocks invalid contract removal unless prior state is terminal,
  - keeps scope/approval/base-commit checks intact.
- Extended contract lifecycle policy schema with:
  - `enforce_transition_on_contract_change`
  - `allowed_transitions`
  - `removal_allowed_statuses`
- Added tests for transition and removal enforcement:
  - `tests/test_process_guard_contract.py`
  - `tests/test_policy_contract.py`
- Updated backlog/roadmap state:
  - closed BL-002,
  - activated BL-005 as current focus,
  - regenerated control dashboard.

## v0.6.2
- Added toolkit-level AI entrypoint file:
  - `AGENTS.md` with mandatory read order and pre-change operating rules.
- Added onboarding documentation contract checker:
  - `scripts/validate_onboarding_docs.py`.
- Added onboarding contract tests:
  - `tests/test_onboarding_docs_contract.py`.
- Updated CI enforcement with onboarding docs check:
  - `python scripts/validate_onboarding_docs.py --check`.
- Updated docs for entrypoint/read-order consistency:
  - `README.md`
  - `docs/CONTROL_TOOLKIT_GUIDE.md`
  - `docs/QUICKSTART.md`
- Updated control cockpit state:
  - closed BL-004 (branch protection complete),
  - closed BL-007 (AI entrypoint complete),
  - closed BL-008 (onboarding docs CI guard complete),
  - refreshed roadmap and dashboard.

## v0.6.1
- Added contract lifecycle artifact:
  - `.control-loop/contracts.json` baseline contract file for execution gating workflows.
- Added process-guard contract lifecycle enforcement (policy-driven, optional):
  - active-contract requirement for controlled implementation paths,
  - scope checks (`include_paths` / `exclude_paths`),
  - approval evidence checks,
  - backlog-link checks,
  - stale contract checks from base-commit ancestry and commit-distance threshold.
- Added policy schema/validation for:
  - `process_guard.contract_lifecycle_rules`.
- Updated tracker state and roadmap priorities:
  - closed BL-001,
  - activated BL-002,
  - added BL-004 (branch protection), BL-005 (release hygiene), BL-006 (SP-003 metric automation),
  - regenerated `docs/CONTROL_DASHBOARD.md`.
- Added tests for contract lifecycle behavior and policy validation:
  - `tests/test_process_guard_contract.py`
  - `tests/test_policy_contract.py`

## v0.6.0
- Added control cockpit source files:
  - `.control-loop/setpoints.json` for measurable target outputs.
  - `.control-loop/backlog.json` for issues/suggestions/plans with priority scoring inputs.
  - `docs/ROADMAP.md` for `Now / Next / Later` planning lanes.
  - `docs/CONTROL_DASHBOARD.md` generated state view for humans and agents.
- Added `scripts/validate_backlog.py`:
  - validates backlog and setpoint schema contracts,
  - validates roadmap coupling and lane alignment,
  - enforces single active item and deterministic priority score calculation.
- Added `scripts/render_dashboard.py`:
  - renders dashboard from source data,
  - provides `--check` sync enforcement and `--write` regeneration.
- Added tests:
  - `tests/test_backlog_contract.py`
  - `tests/test_dashboard_render_contract.py`
- Updated toolkit CI to enforce:
  - `python scripts/validate_backlog.py --check`
  - `python scripts/render_dashboard.py --check`
- Updated docs (`README.md`, `docs/CONTROL_TOOLKIT_GUIDE.md`, `docs/QUICKSTART.md`) with cockpit workflow and commands.

## v0.5.1
- Re-based toolkit defaults to stay project-agnostic:
  - generic proposal field markers (`Validation coverage evidence`, `Single-case exception`),
  - removed PDF-project-specific defaults from toolkit policy.
- Added execution-phase governance controls in process guard:
  - session markers for workflow phase, change scope, and implementation approval token,
  - `--mode think` enforcement to block implementation/toolkit code edits in think-only runs.
- Extended policy validation to include `process_guard.execution_phase_rules`.
- Updated toolkit docs and session template for phase/scope/token markers.
- Added policy contract test to prevent project-specific marker regressions in toolkit defaults.

## v0.5.0
- Added policy-driven design robustness checks in `process_guard`:
  - design principle value checks with per-rule severity (`strict`, `warn`, `manual_review`),
  - manual-review evidence requirement for declared special-cases.
- Added static guard scan support for changed implementation files:
  - regex rules and severity defined in policy,
  - default rules detect absolute path literals and hardcoded PDF filename literals.
- Extended default policy with robustness field markers for:
  - generality scope,
  - corpus and holdout evidence,
  - config externalization evidence,
  - determinism and idempotency evidence.
- Extended policy validation for:
  - `design_principle_rules`,
  - `static_guard_rules`.
- Updated docs to describe rule-severity and static-guard behavior.

## v0.4.1
- Added model-catalog contract at `contracts/model_catalog.contract.json`.
- Added prompt generator and sync checker:
  - `scripts/generate_model_catalog_prompt.py`
  - generated artifact `contracts/MODEL_CATALOG_PROMPT.md`
- Added toolkit CI enforcement for generated prompt sync.
- Added tests for model-catalog contract routing shape and prompt sync.
- Updated docs with contract-driven model-catalog workflow.

## v0.4.0
- Added AI settings model to default policy:
  - response style settings,
  - execution behavior settings,
  - global process switch (`strict` or `advisory`),
  - session log configuration,
  - context-management configuration.
- Added AI settings loader support in `control_loop/policy.py`:
  - loads `.control-loop/ai_settings.json` by default,
  - supports env override (`CONTROL_LOOP_AI_SETTINGS_PATH`),
  - validates AI settings schema and waiver requirements.
- Extended `process_guard` with:
  - session-log enforcement for code/process changes,
  - required approval evidence checks,
  - failure-to-correction evidence checks,
  - advisory-mode behavior through global switch.
- Updated default required artifacts:
  - `.control-loop/ai_settings.json`,
  - `docs/CONTEXT_INDEX.md`,
  - `docs/sessions/README.md`,
  - `docs/sessions/TEMPLATE.md`.
- Added toolkit templates:
  - `docs/AI_SETTINGS_TEMPLATE.json`,
  - `docs/CONTEXT_INDEX_TEMPLATE.md`,
  - `docs/SESSION_TEMPLATE.md`.
- Expanded docs (`README.md`, `docs/CONTROL_TOOLKIT_GUIDE.md`, `docs/QUICKSTART.md`, `docs/POLICY_SCHEMA.md`).
- Added and extended tests for AI settings and session-enforcement behavior.

## v0.3.0
- Added strict policy validation in loader (`control_loop/policy.py`).
- Added controlled override mechanism:
  - partial merge mode,
  - full override mode with mandatory waiver metadata.
- Added process-vs-project guideline field separation in default policy.
- Updated `process_guard` to use separated guideline fields and fail gracefully on policy errors.
- Updated `control_gate` to fail gracefully on policy load/validation errors.
- Added toolkit test suite:
  - `tests/test_policy_contract.py`
  - `tests/test_process_guard_contract.py`
- Added toolkit CI workflow at `.github/workflows/ci.yml`.
- Added `requirements-dev.txt`.

## v0.2.1
- Added comprehensive single-file onboarding guide: `docs/CONTROL_TOOLKIT_GUIDE.md`.
- Added manual setup quickstart: `docs/QUICKSTART.md`.
- Added practical policy schema reference: `docs/POLICY_SCHEMA.md`.
- Updated README to point to new docs.

## v0.2.0
- Added policy-driven configuration (`control_loop/policy.py` + `default_policy.json`).
- Added work mode enforcement (`routine` or `design`) in proposal checks.
- Added no-assumption enforcement requiring confirmation evidence for non-`NONE` assumptions.
- Made control and process guard behavior configurable via policy override path/env/project file.

## v0.1.0
- Initial release with control gate and process guard.
