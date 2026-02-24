# Proposals

Use this folder for proposal-first planning before implementation changes in `core/`, `data_models/`, `utils/`, or `main.py`.

## Naming
Use: `YYYY-MM-DD-short-topic.md`

Example:
- `2026-02-23-link-resolution-boundary-fix.md`

## Minimum Content
Each proposal must be created from `docs/proposals/TEMPLATE.md` and include all required sections.
At minimum this includes:
- explicit work mode selection (`routine` or `design`)
- design-parameter compliance matrix
- robustness evidence for generality and no-hardcoding claims
- exception register with rollback plan
- decision scorecard
- assumptions and unknowns section
- approval checkpoint with confirmation evidence marker
- validation plan

## Rule
Implementation changes without a proposal update fail `scripts/process_guard.py --mode ci`.

