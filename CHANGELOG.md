# Changelog

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
