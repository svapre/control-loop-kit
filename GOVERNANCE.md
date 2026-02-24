# Governance Rules

## Purpose
This file defines how decisions are made, validated, and approved by the human-AI team.

## Core Rule
No significant change is accepted unless both are true:
1. Code quality gates pass.
2. Process and design gates pass.

## Human-AI Operating Model
1. Human role:
   - Set objectives, constraints, and approval boundaries.
   - Approve or reject proposals and merges.

2. AI role:
   - Generate proposals, implement changes, run checks, and report evidence.
   - Explicitly call out design violations and tradeoffs.

3. Decision authority:
   - Acceptance is evidence-based (tests/CI/gates), not trust-based.
   - AI is execution-heavy, but not an approval authority.

## Two Work Modes
1. Design mode:
   - Used for brainstorming and solution selection.
   - Must include compliance against `DESIGN.md` parameters and an exception analysis.

2. Execution mode:
   - Used for coding, tests, CI fixes, and repository operations.
   - Must follow proposal-first rules and pass automated gates.

Mode selection and guard behavior are defined through `.control-loop/policy.json` so the process remains tool-agnostic and configurable.
Response behavior and approval requirements are defined through `.control-loop/ai_settings.json`.

## Proposal-First Workflow
Before changing implementation files (`core/`, `main.py`, `data_models/`, `utils/`):
1. Create or update a proposal in `docs/proposals/`.
2. Complete all mandatory template sections.
3. Include design-parameter compliance and explicit exceptions (if any).
4. Record selected work mode (`routine` or `design`) and assumptions/unknowns.

## Ambiguity Stop Rule
1. If implementation depends on unresolved assumptions, do not proceed directly to code.
2. Ask clarifying questions and capture user confirmation evidence in proposal.
3. Assumption-based implementation is allowed only after explicit confirmation.

## Design Compliance Rule
Every plan must be checked against `DESIGN.md`.
If a plan violates a parameter, proposal must include:
1. Violated parameter
2. Reason alternatives are worse
3. Risk, mitigation, and rollback

## Rule Severity Modes
Design/process checks can be configured per rule as:
1. `strict` - fails checks automatically.
2. `warn` - emits warning but does not fail.
3. `manual_review` - flags human review; if marked as special-case, approval evidence is required.

Projects can tune severity through `.control-loop/policy.json` without changing gate logic.

## Process-Change Rule
If process files change (`SPEC.md`, `SYSTEM.md`, `AGENTS.md`, gate scripts, CI workflow, governance/design docs):
1. Update `docs/PROCESS_CHANGELOG.md` in the same branch.
2. Explain what changed and why.

## Session Evidence Rule
If changed files match AI-settings enforcement scope (for example implementation code, gate scripts, workflow files, policy files):
1. Update a session log under `docs/sessions/`.
2. Record planned changes, user approval evidence, failures, and corrective actions.
3. Missing session evidence is a machine-check failure.

## Global Switch Rule
AI-settings include a global process switch:
1. `enabled=true, mode=strict`: process failures block merge.
2. `enabled=true, mode=advisory`: process failures become warnings.
3. `enabled=false`: process failures become warnings and require waiver metadata.
4. Default branch should run strict mode.

## Merge Rule
Default branch may only receive merges where all pass:
1. CI checks
2. `scripts/control_gate.py --mode ci`
3. `scripts/process_guard.py --mode ci`

## Communication Contract
1. Follow `docs/USER_CONTEXT.md`.
2. Define technical terms and acronyms on first use unless user asks for expert shorthand.
3. Describe any design-parameter violation in plain language with mitigation.

