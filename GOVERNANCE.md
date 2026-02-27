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

## Constitutional Law-Making Authority

The toolkit repo holds the exclusive right to amend national (default) law.
Consumer projects (state governments) can only create and enforce their own state laws.

### Why this is architecturally enforced

National governance files (`control_loop/default_policy.json`,
`control_loop/process_guard.py`, `control_loop/control_gate.py`, etc.)
exist only in the toolkit repo. Consumer projects never have copies of these
files in their own repos - they import the toolkit as a dependency. A consumer
project has no filesystem path to modify the national law, so the separation
is structural, not just policy.

### Constitutional Amendment Gate

Any change to a national governance file (as listed in
`governance_human_authority_rule.governance_files` in `.control-loop/policy.json`)
requires **mandatory human approval** before merging:

1. CI detects governance-file changes using the union of base and head policy
   governance lists (so a PR cannot remove protection by editing policy first).
2. CI pauses at job `governance-human-approval` in GitHub Environment
   `governance-amendment`.
3. The required human reviewer must approve in the GitHub UI.
4. `scripts/verify_governance_authority.py --check` verifies qualifying PR
   approval on the latest commit for configured approver(s).

Without approval, required checks cannot complete and merge remains blocked.
The AI may propose and draft governance changes, but cannot land them alone.

Token text in session logs is not treated as constitutional approval in this
repository. Approval is interactive and out-of-band in GitHub controls.

### Conflicting-Change Detection (deferred)

An amendment that weakens or removes an existing national rule (e.g., disabling
a mandatory check, removing a required file from the list) is more dangerous than
an additive amendment. Automatic detection of such regressions requires:
- Reading the base version of the governance file from git
- Comparing enforcement keys and their values
- Classifying weakening vs. additive changes

This is deferred to a future backlog item. Until then, the human reviewer is the
sole arbiter of whether a proposed amendment is regressive. The constitutional
amendment gate ensures a human always reviews before merge.
