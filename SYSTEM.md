# System Control Model

## Purpose
Define the closed-loop engineering control system for this repository. The loop governs how changes are proposed, measured, corrected, and accepted.

## Control Framing
- Controller: autonomous development agent (Codex), with human review.
- Plant: repository code, tests, lint config, CI workflow, dependency setup, and process docs.
- Reference signal: pass targets defined in `SPEC.md` and guardrails in `DESIGN.md`.
- Feedback signals: local command exit codes, process-gate output, control-gate output, and GitHub Actions results for current `HEAD`.
- Error vector: the set of failing checks versus target pass state.

## Loop Components
### Sensors (Measurements)
1. Lint sensor: `ruff check .`
2. Test sensor: `pytest -q`
3. CI sensor: successful `ci` workflow run for current `HEAD`.
4. Control-gate sensor: `python scripts/control_gate.py --mode readiness`.
5. Process-gate sensor: `python scripts/process_guard.py --mode ci`.
6. Repository state sensor: `git status --short` for dirty-state visibility.
7. Policy sensor: `.control-loop/policy.json` loaded by gate scripts.
8. AI settings sensor: `.control-loop/ai_settings.json` loaded through policy loader.
9. Session evidence sensor: session logs under `docs/sessions/` when trigger paths change.
10. Context-priority sensor: `docs/CONTEXT_INDEX.md`.

### Actuators (Corrections)
1. Edit source/config/test files.
2. Add or adjust tooling config (`pyproject.toml`, workflow files, test scaffolds).
3. Add or pin developer dependencies needed for measurement.
4. Update documentation (`MASTER_PLAN.md`, `SPEC.md`, process logs, proposals) to keep control intent explicit.
5. Configure repository integration prerequisites (remote origin, GitHub auth, CI connectivity).

### Controller Logic
1. Measure sensors.
2. Compare measured state to `SPEC.md` pass targets.
3. Identify smallest corrective change set needed to reduce error.
4. Apply corrections.
5. Re-run sensors.
6. Commit when stable improvement is achieved.
7. Repeat until all required sensors report pass.

## Dual Closed Loops
This project runs two linked loops:
1. Code-quality loop:
   - Focus: syntax, tests, CI pass state.
   - Tools: lint, tests, control gate.
2. Process-governance loop:
   - Focus: whether implementation changes are backed by proposal/design updates and whether process changes are logged.
   - Tools: process guard, PR template, process changelog.

A change is accepted only when both loops are green.

The gate implementation is consumed from shared repository `tooling/control-loop-kit` so the same process can be reused across projects.

An additional communication-control loop is enforced through AI settings:
1. user feedback updates response settings,
2. session evidence proves approval and correction flow,
3. process guard enforces compliance.

## Operating Modes
1. Work mode `routine`: low-risk implementation and maintenance tasks.
2. Work mode `design`: architecture/tradeoff and unclear requirement analysis.
3. If requirements are ambiguous, proposal must use `design` and record clarifying questions.
4. Bootstrap mode: establish tooling and measurements (Steps 1-3 in `MASTER_PLAN.md`).
5. Stabilization mode: iterate until full green state (Step 4).
6. Readiness mode: verify CI success for `HEAD`, clean worktree, and fresh readiness tag (Step 5).
7. Maintenance mode: future work must keep both loops green; regressions trigger return to stabilization mode.

## Termination Criteria
Control loop is considered closed and stable when:
1. Local lint and tests pass with zero failures.
2. Process guard passes.
3. CI workflow has a successful run for current `HEAD`.
4. `python scripts/control_gate.py --mode readiness` passes.
5. `MASTER_PLAN.md` marks Steps 1-5 complete with valid evidence.
6. Readiness tag `control-system-ready` points to `HEAD`.

## Disturbances and Failure Handling
Common disturbances:
1. Dependency drift or missing tooling.
2. Syntax/runtime import failures.
3. Configuration mismatch between local and CI.
4. Missing GitHub remote or missing authentication.
5. Stale readiness tag after additional commits.
6. Context drift in brainstorming that skips design rules.

Failure handling policy:
1. Any failing sensor is treated as non-zero control error.
2. Do not advance steps while unresolved failures exist for the current step goal.
3. Record failures and corrections in `MASTER_PLAN.md` and `docs/PROCESS_CHANGELOG.md` when process files change.
4. If readiness was previously marked complete and a new failure appears, reopen Step 4/5.
5. If evidence is missing, mark status as `UNKNOWN` instead of claiming completion.

## Guardrails
1. No feature development before control-system readiness is tagged and verified.
2. Each meaningful artifact is committed with explicit commit message.
3. Plans and specs are source-controlled and updated alongside implementation changes.
4. Readiness claims must be reproducible via automated control-gate command.
5. Proposal-first and design-compliance checks are enforced via `scripts/process_guard.py`.

