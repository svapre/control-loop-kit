# Changelog

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
