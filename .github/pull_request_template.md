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

