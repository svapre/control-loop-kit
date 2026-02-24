# Master Plan

## Objective
Build and stabilize a closed-loop engineering control system for this repository before any feature work.

## Task Board
| Step | Title | Status | Success Criteria | Evidence | Next Action |
|---|---|---|---|---|---|
| 1 | Initialize Git + project skeleton | done | Git initialized, docs scaffolding created, initial commit made | Commit `58245dd` | Step 2 |
| 2 | Define control-system architecture | done | `SYSTEM.md` and `SPEC.md` define measurable control targets | Commit `46d11a0` | Step 3 |
| 3 | Build measurement and feedback tools | done | CI, tests, and lint configured and executable | Commit `65a0487` with workflow, config, and test scaffold | Step 4 |
| 4 | Execute feedback loop to green | done | Local checks pass and remote CI success exists for current `HEAD` | Remote configured, CI green for hardened gate flow, local control gates passing | Step 5 |
| 5 | Tag readiness | in_progress | `control-system-ready` tag points to `HEAD` and readiness gate passes | Reopened: new commits require fresh CI run and tag refresh for current `HEAD` | Push latest commits, verify CI success, then refresh readiness tag |
| 6 | Harden process governance loop | done | Process guard enforces proposal/design/process coupling and is required in CI | Added `scripts/process_guard.py`, governance docs/templates, CI integration; local gates pass | Start feature planning under new guardrails |
| 7 | Enforce AI settings + session evidence loop | done | AI settings are file-driven and process/session checks are machine-enforced | Commits `c556df0` (toolkit) and `4cb016a`/`319adf1` (project); all local checks green | Complete Step 5 readiness refresh after CI |
| 8 | Add model-catalog contract sync loop | done | Contract-driven model catalog format and generated prompt stay synchronized by machine check | Toolkit commit `fd7992b`; local sync/lint/tests passed | Start model-routing runtime implementation |
| 9 | Add design robustness severity checks | done | No-hardcoding and generality evidence are mechanically checked with severity levels | Toolkit pending commit on top of `fd7992b`; project tests/gates green | Continue with external-AI intake controls |
| 10 | Recover toolkit generic boundary + phase/scope enforcement | in_progress | Toolkit defaults remain project-agnostic, project-specific strictness stays in project override, and think-vs-implement rules are machine-enforced | Local toolkit and project checks both pass after recovery edits (`ruff`, `pytest`, `process_guard`, `control_gate`) | Commit toolkit and project recovery changes, push, and verify CI |

## Progress Log
- Step 1 completed: initialized Git, added control-document scaffolding, and committed baseline (`58245dd`).
- Step 2 completed: formalized control-loop architecture in `SYSTEM.md` and measurable pass/fail gates in `SPEC.md` (`46d11a0`).
- Step 3 completed: added CI workflow, lint config, dev dependencies, and minimum baseline tests (`65a0487`).
- Step 4 measurement cycle 1: failures detected.
  - `ruff check .` failed on undefined `json` in `core/profiler.py`.
  - `pytest -q` failed due invalid `pyproject.toml` encoding/parsing.
- Step 4 corrective actions:
  - Added module-level `import json` and removed function-local conflicting import in `core/profiler.py`.
  - Rewrote `pyproject.toml` in ASCII to remove BOM parsing issue.
- Step 4 measurement cycle 2: local checks passed.
  - `python -m pip install -r requirements.txt -r requirements-dev.txt` passed.
  - `ruff check .` passed.
  - `pytest -q` passed.
- Postmortem: readiness was previously marked done using local fallback despite no remote CI proof for current `HEAD`.
- Hardening cycle applied:
  - Added automated control gate at `scripts/control_gate.py`.
  - Tightened `SPEC.md`, `SYSTEM.md`, and `AGENTS.md` to require remote CI proof and tag freshness.
  - Added CI step `python scripts/control_gate.py --mode ci`.
- Current state after hardening:
  - Local checks are passing.
  - Readiness is intentionally reopened until remote CI for current `HEAD` is available and tag is updated.
- Hardening verification run:
  - `python scripts/control_gate.py --mode ci` passed.
  - `python scripts/control_gate.py --mode readiness` failed as expected with actionable blockers:
    - no `origin` remote configured,
    - stale `control-system-ready` tag,
    - dirty worktree during in-progress edits.
- Remote integration and stabilization cycle:
  - Configured GitHub remote by creating `svapre/pdf-accessibility-linker` and pushing `master`.
  - CI run on hardening commit initially failed (Linux import path issue), then fixed via `tests/conftest.py`.
  - Subsequent CI run completed successfully for latest pushed code.
  - Finalized readiness by enforcing strict gate criteria and refreshing readiness tag to latest `HEAD`.
- Process governance hardening cycle:
  - Added process gate script at `scripts/process_guard.py`.
  - Added governance and design baselines (`GOVERNANCE.md`, `DESIGN.md`).
  - Added required process artifacts:
    - `docs/PROCESS_CHANGELOG.md`
    - `docs/proposals/README.md`
    - `docs/proposals/TEMPLATE.md`
    - `.github/pull_request_template.md`
  - Extended CI workflow to run process guard using base SHA.
  - Extended control gate required artifacts to include governance/process files.
  - Updated control docs (`AGENTS.md`, `SPEC.md`, `SYSTEM.md`) to enforce brainstorming and design-compliance expectations.
  - Verification evidence (local):
    - `.\\venv\\Scripts\\python.exe -m ruff check .` passed.
    - `.\\venv\\Scripts\\python.exe -m pytest -q` passed.
    - `.\\venv\\Scripts\\python.exe scripts/process_guard.py --mode ci` passed.
    - `.\\venv\\Scripts\\python.exe scripts/control_gate.py --mode ci` passed.
- Communication-context hardening:
  - Added `docs/USER_CONTEXT.md` to persist user background and response-style requirements.
  - Updated `AGENTS.md`, `GOVERNANCE.md`, and `SPEC.md` to require plain-language explanations and acronym/term definitions.
  - Updated `docs/PROCESS_CHANGELOG.md` and `docs/README.md` to track/discover communication policy artifacts.
- Design-parameter hardening cycle:
  - Expanded `DESIGN.md` with explicit project design parameters and exception rule.
  - Updated `GOVERNANCE.md` with human-AI operating model and dual-mode workflow.
  - Updated proposal contract (`docs/proposals/TEMPLATE.md`) with compliance matrix, exception register, decision scorecard, and validation plan.
  - Strengthened `scripts/process_guard.py` and `tests/test_process_guard_contract.py` to enforce the upgraded proposal structure.
  - Updated `SPEC.md`, `AGENTS.md`, and `docs/PROCESS_CHANGELOG.md` to align policy and enforcement.
- Process extraction and upgrade-test cycle:
  - Split reusable control-loop logic into dedicated repo `svapre/control-loop-kit`.
  - Added toolkit as submodule at `tooling/control-loop-kit` and pinned version.
  - Converted local gate scripts to compatibility wrappers that import toolkit modules.
  - Upgraded toolkit to `v0.2.0` and updated this project to consume it.
  - Adopted policy-driven configuration with `.control-loop/policy.json`.
  - Added ambiguity stop and work-mode constraints in proposal template, governance, and spec.
- Toolkit documentation adoption cycle:
  - Released `control-loop-kit v0.2.1` with single-file human+AI onboarding and policy documentation.
  - Upgraded project submodule to `v0.2.1`.
  - Recorded adoption in `docs/PROCESS_CHANGELOG.md`.
- Toolkit policy-governance adoption cycle:
  - Released and adopted `control-loop-kit v0.3.0`.
  - Adopted policy validation, partial/full override governance, and toolkit self-CI.
  - Added explicit partial override directive to project `.control-loop/policy.json`.
  - Recorded adoption in `docs/PROCESS_CHANGELOG.md`.
- AI-settings and session-evidence hardening cycle completed:
  - Extended toolkit policy and process guard to load `.control-loop/ai_settings.json`.
  - Added global strict/advisory switch, context index model, and session evidence enforcement.
  - Added project-level AI settings file, context index, session templates, and session log.
  - Validation evidence:
    - `.\\venv\\Scripts\\python.exe -m ruff check .` passed.
    - `.\\venv\\Scripts\\python.exe -m pytest -q` passed.
    - `.\\venv\\Scripts\\python.exe scripts/process_guard.py --mode ci` passed.
    - `.\\venv\\Scripts\\python.exe scripts/control_gate.py --mode ci` passed.
- Readiness gate check after these commits:
  - `.\\venv\\Scripts\\python.exe scripts/control_gate.py --mode readiness` failed as expected because:
    - CI has not run yet for current `HEAD`.
    - `control-system-ready` tag is stale and must be moved after CI passes.
- Model-catalog contract sync loop completed:
  - Added contract source of truth:
    - `tooling/control-loop-kit/contracts/model_catalog.contract.json`
  - Added generated prompt artifact and sync checker:
    - `tooling/control-loop-kit/contracts/MODEL_CATALOG_PROMPT.md`
    - `tooling/control-loop-kit/scripts/generate_model_catalog_prompt.py`
  - Added toolkit CI check:
    - `python scripts/generate_model_catalog_prompt.py --check`
  - Added toolkit contract tests:
    - `tooling/control-loop-kit/tests/test_model_catalog_contract.py`
  - Validation evidence:
    - `python scripts/generate_model_catalog_prompt.py --check` passed (toolkit root).
    - `python -m ruff check .` passed (toolkit root).
    - `python -m pytest -q` passed (toolkit root).
- Design robustness severity checks completed:
  - Added policy-driven proposal evidence checks for generality/no-hardcoding claims with per-rule severity:
    - `strict`, `warn`, `manual_review`.
  - Added policy-driven static guard scan for changed implementation files:
    - strict check for absolute path literals,
    - manual-review signal for hardcoded PDF filename literals.
  - Expanded proposal template and tests with:
    - config externalization evidence,
    - generality scope,
    - corpus coverage evidence,
    - holdout validation evidence,
    - determinism and idempotency evidence,
    - single-document special-case declaration and manual review evidence.
  - Validation evidence:
    - project `ruff`, `pytest`, `process_guard --mode ci`, and `control_gate --mode ci` all passed.
    - toolkit `ruff` and `pytest` passed after the new rule set.
- Recovery cycle for toolkit/project boundary correctness (current):
  - Rebased toolkit default policy to generic markers (`Validation coverage evidence`, `Single-case exception`) and removed PDF-specific defaults.
  - Added execution phase/scope/token enforcement in toolkit process guard (`think`/`implement`, project/toolkit scope).
  - Kept PDF-project-specific strict rules in project override policy (`.control-loop/policy.json`) only.
  - Updated toolkit and project contract tests to match generic defaults and explicit rule enabling in tests.
  - Validation evidence:
    - toolkit: `python -m ruff check .`, `python -m pytest -q` passed.
    - project: `python -m ruff check .`, `python -m pytest -q`, `python scripts/process_guard.py --mode ci`, `python scripts/control_gate.py --mode ci` passed.
