## Summary
- What changed:
- Why:

## Proposal and Design
- Proposal file: `docs/proposals/<file>.md`
- Design guardrails satisfied:
- Design guardrails violated (if any) and justification:
- Session log file (if required by AI settings): `docs/sessions/<file>.md`

## Validation
- [ ] `ruff check .`
- [ ] `pytest -q`
- [ ] `python scripts/control_gate.py --mode ci`
- [ ] `python scripts/process_guard.py --mode ci --base-sha <base_sha>`

## Process Updates
- [ ] Updated `docs/PROCESS_CHANGELOG.md` for process/policy changes (if applicable)
- [ ] Updated `MASTER_PLAN.md` when control-step status changed
- [ ] Confirmed `.control-loop/ai_settings.json` was applied (or documented waiver/advisory mode)

## Governance Approval (only for governance-file changes)
- [ ] Confirmed this PR received required GitHub Environment approval (`governance-amendment`)

## Constitutional Amendment Artifact (required for governance-affecting PRs)
- Added exactly one file under `.control-loop/amendments/<slug>.json`
- `amendment_id` equals filename stem
- Minimal schema v1 fields are present and machine-parseable

## Constitutional Amendment Declaration (optional transitional overlap mirror)
- If present, declaration fields must match the amendment artifact key fields.
- Legal object changed:
- Affected layer:
- Candidate tier:
- Expected constitutional effect:
- Draft status:

