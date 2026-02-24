# Control Loop Kit

Reusable process-control toolkit for AI-assisted software projects.

## What this repository provides
- `control_loop.control_gate`: readiness and CI gate checks.
- `control_loop.process_guard`: process-governance checks for proposal/design coupling.
- `control_loop.policy`: policy loading and override logic.

## Policy-driven behavior
Rules are loaded from JSON policy files instead of being hardcoded in scripts.

Policy resolution order:
1. `--policy <path>` CLI argument
2. `CONTROL_LOOP_POLICY_PATH` environment variable
3. Project-local `.control-loop/policy.json`
4. Toolkit fallback `control_loop/default_policy.json`

## Built-in process protections
- Proposal/design coupling checks.
- Ambiguity stop rule (assumptions require explicit user confirmation evidence).
- Work mode rule (`routine` vs `design`) to control reasoning depth and cost.

## Intended usage
1. Add this repository to a project as a submodule or package dependency.
2. Expose local wrapper scripts that call the toolkit modules.
3. Add project-specific `.control-loop/policy.json` for local constraints.
4. Run checks in CI and local development.

## Versioning
Use tagged releases and pin versions per project. Upgrade via explicit version bump PRs.

## Current release
- `v0.2.0`

