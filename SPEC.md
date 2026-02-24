# Engineering Spec

## Scope
This specification defines measurable acceptance criteria for the repository control system setup and governance hardening phase.

## Required Artifacts
The following files must exist and be maintained:
1. `MASTER_PLAN.md`
2. `AGENTS.md`
3. `SYSTEM.md`
4. `SPEC.md`
5. `DESIGN.md`
6. `GOVERNANCE.md`
7. `docs/PROCESS_CHANGELOG.md`
8. `docs/proposals/README.md`
9. `docs/proposals/TEMPLATE.md`
10. CI workflow at `.github/workflows/ci.yml`
11. PR template at `.github/pull_request_template.md`
12. Lint and test configuration (`pyproject.toml` or equivalent)
13. Test scaffolding under `tests/`
14. Control gate validator at `scripts/control_gate.py`
15. Process gate validator at `scripts/process_guard.py`
16. User context profile at `docs/USER_CONTEXT.md`
17. Process policy file at `.control-loop/policy.json`
18. AI settings file at `.control-loop/ai_settings.json`
19. Context index file at `docs/CONTEXT_INDEX.md`
20. Session docs at `docs/sessions/README.md` and `docs/sessions/TEMPLATE.md`

## Required Commands (Local)
All commands are run from repository root.

1. Dependency install
- Command: `python -m pip install -r requirements.txt -r requirements-dev.txt`
- Pass criteria: exit code `0`

2. Lint
- Command: `ruff check .`
- Pass criteria: exit code `0`, no lint violations under configured rules

3. Tests
- Command: `pytest -q`
- Pass criteria: exit code `0`, no test failures or errors

4. Process guard
- Command: `python scripts/process_guard.py --mode ci`
- Pass criteria: exit code `0`

5. Control gate (readiness)
- Command: `python scripts/control_gate.py --mode readiness`
- Pass criteria: exit code `0`

## CI Gate Criteria
Primary gate:
1. GitHub Actions workflow `.github/workflows/ci.yml` executes dependency install, lint, tests, `python scripts/process_guard.py --mode ci --base-sha <base>`, and `python scripts/control_gate.py --mode ci` successfully.

No local fallback gate is allowed for declaring readiness.

Any failed required gate is a hard fail.

## Green State Definition
Green state is achieved when:
1. All local required commands pass.
2. CI workflow has a successful run for current `HEAD` commit.
3. `MASTER_PLAN.md` records completion status for current step with evidence.

## Zero-Error Control State
Zero-error state for this phase means:
1. No failing required checks.
2. No unresolved TODOs in the master plan for Steps 1-5.
3. Readiness tag `control-system-ready` exists and points to `HEAD`.

## Enforcement Rules
1. Do not add new application feature logic before `control-system-ready` is reached.
2. Any change that causes required checks to fail must be corrected before continuing.
3. `MASTER_PLAN.md` must be updated after each completed step with evidence.
4. If readiness preconditions are missing (for example no remote origin or no successful CI run for `HEAD`), readiness cannot be marked complete.
5. Implementation changes in `core/`, `data_models/`, `utils/`, or `main.py` must include:
   - proposal update under `docs/proposals/`
   - design-impact update in `DESIGN.md` or `docs/adr/`
6. Process/control changes must include `docs/PROCESS_CHANGELOG.md` update in the same change set.
7. Proposal files under `docs/proposals/` must include required sections defined by `scripts/process_guard.py`.
8. Proposal files must include:
   - design-parameter compliance matrix
   - exception register (with rollback)
   - decision scorecard
   - work mode declaration
   - assumptions and unknowns section
   - approval checkpoint with confirmation evidence marker
   - validation plan
9. During brainstorming, any suggested approach that violates `DESIGN.md` must be explicitly marked as a design violation with mitigation.
10. Communication responses must follow `docs/USER_CONTEXT.md`:
   - define terms on first mention
   - expand acronyms on first use
   - prefer plain language unless user requests technical depth
11. If assumptions are non-`NONE`, proposal must require user confirmation before implementation.
12. AI behavior must follow `.control-loop/ai_settings.json`.
13. If changed files match session triggers from AI settings, a session log update under `docs/sessions/` is required.
14. Global process switch behavior from AI settings must be honored:
   - strict mode fails checks
   - advisory/disabled mode warns with waiver metadata rules
15. Design principle rules in policy must support per-rule severity:
   - `strict`, `warn`, `manual_review`
16. Static guard rules must scan changed implementation files for hardcoding/overfitting signals defined in policy.
17. Proposal design-evidence fields for generality and robustness must be non-empty for `strict` rules.

## Minimum Test Baseline
Before readiness tag, test suite must include at least:
1. One schema contract test.
2. One utility contract test.
3. One pipeline import/smoke test.
4. One control-gate contract test.
5. One process-gate contract test.

## Readiness Tag Criteria
Tag `control-system-ready` may be created or moved only when:
1. Steps 1-4 are complete and validated.
2. `python scripts/control_gate.py --mode readiness` passes.
3. Step 5 is marked complete in `MASTER_PLAN.md`.

