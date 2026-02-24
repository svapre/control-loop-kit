# Control Loop Kit

Reusable process-control toolkit for AI-assisted software projects.

## What this repository provides
- `control_loop.control_gate`: readiness and CI gate checks.
- `control_loop.process_guard`: process-governance checks for proposal/design coupling.
- `control_loop.policy`: policy loading, validation, and override handling.

## Read first
- Full onboarding (human + AI): `docs/CONTROL_TOOLKIT_GUIDE.md`
- Manual setup quickstart: `docs/QUICKSTART.md`
- Policy structure reference: `docs/POLICY_SCHEMA.md`

## Key capabilities
1. Policy-driven checks (avoid hardcoded project rules in gate logic).
2. Process vs project guideline separation.
3. Partial/full override support:
   - partial merge by default
   - full override with mandatory waiver metadata
4. Ambiguity stop enforcement:
   - assumptions require confirmation evidence
5. Work mode enforcement (`routine` / `design`).

## Current release
- `v0.3.0` (policy validation + override control + toolkit self-CI)

