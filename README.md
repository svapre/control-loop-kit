# Control Loop Kit

Reusable process-control toolkit for AI-assisted software projects.

## What this repository provides
- `control_loop.control_gate`: readiness and CI gate checks.
- `control_loop.process_guard`: process-governance checks for proposal/design coupling.
- `control_loop.policy`: policy loading, validation, and override handling.
- `ai_settings` policy model: response style, approval behavior, and global enforcement switch.
- model-catalog contract and prompt generator for cross-agent model data collection.

## Read first
- AI single-file entrypoint: `AGENTS.md`
- Full onboarding (human + AI): `docs/CONTROL_TOOLKIT_GUIDE.md`
- Manual setup quickstart: `docs/QUICKSTART.md`
- Policy structure reference: `docs/POLICY_SCHEMA.md`
- Release process: `docs/RELEASE_CHECKLIST.md`

## Key capabilities
1. Policy-driven checks (avoid hardcoded project rules in gate logic).
2. Process vs project guideline separation.
3. Partial/full override support:
   - partial merge by default
   - full override with mandatory waiver metadata
4. Ambiguity stop enforcement:
   - assumptions require confirmation evidence
5. Work mode enforcement (`routine` / `design`).
6. Agent-agnostic AI settings support:
   - `.control-loop/ai_settings.json` merged through policy loader.
7. Session evidence enforcement:
   - code/process changes can require a session log update with approval and correction evidence.
8. Global process switch:
   - strict mode or advisory mode from AI settings.
9. Contract-driven model-catalog prompt generation:
   - contract file: `contracts/model_catalog.contract.json`
   - generated prompt: `contracts/MODEL_CATALOG_PROMPT.md`
   - sync check: `python scripts/generate_model_catalog_prompt.py --check`
10. Design robustness guardrails:
    - proposal evidence checks for generality/no-hardcoding claims,
    - per-rule severity (`strict`, `warn`, `manual_review`),
    - static scans for obvious hardcoding/overfitting signals in changed code.
11. Phase and scope execution checks:
    - session markers enforce `think` vs `implement` workflow boundaries,
    - implementation changes require explicit approval token evidence.
12. Control cockpit tracking:
    - setpoints file defines measurable targets,
    - backlog file tracks issues/suggestions/plans with machine-computed priority score,
    - roadmap and generated dashboard keep state visible for humans and agents.
13. Contract lifecycle execution gating:
    - optional active-contract checks for controlled implementation paths,
    - scope, approval, backlog-link, and stale-base validation from policy.
    - status-transition validation when `.control-loop/contracts.json` changes.

## Control cockpit files
- `.control-loop/setpoints.json`
- `.control-loop/backlog.json`
- `.control-loop/contracts.json`
- `docs/ROADMAP.md`
- `docs/CONTROL_DASHBOARD.md`

## Control cockpit commands
- Validate backlog/setpoint/roadmap coupling:
  - `python scripts/validate_backlog.py --check`
- Validate derived setpoint metrics sync:
  - `python scripts/sync_setpoints.py --check`
- Recompute/write derived setpoint metrics:
  - `python scripts/sync_setpoints.py --write`
- Validate dashboard sync:
  - `python scripts/render_dashboard.py --check`
- Regenerate dashboard:
  - `python scripts/render_dashboard.py --write`
- Validate onboarding doc contract:
  - `python scripts/validate_onboarding_docs.py --check`
- Validate release hygiene contract:
  - `python scripts/validate_release_hygiene.py --check --allow-unreleased-latest`

## Current release
- `v0.6.5` (SP-003 metric automation + CI setpoint sync check)

