# Policy Schema (Practical)

This document defines the expected shape of `.control-loop/policy.json`.

## Top-level object
```json
{
  "control_gate": {},
  "process_guard": {}
}
```

## `control_gate` keys
- `required_files`: array of file paths that must exist
- `require_tests_dir`: boolean
- `master_plan_tokens`: array of strings used to detect readiness tracking in `MASTER_PLAN.md`
- `readiness_tag`: string git tag name
- `ci_workflow_name`: string workflow name used in remote CI lookup
- `readiness_commands`: array of command arrays; `${PYTHON}` token is supported

## `process_guard` keys
- `required_process_files`: array of file paths
- `implementation_prefixes`: array of path prefixes treated as implementation code
- `implementation_files`: array of exact paths treated as implementation code
- `process_controlled_files`: array of file paths requiring changelog update when changed
- `proposal_ignored_files`: array of proposal paths excluded from proposal checks
- `proposal_root`: string path prefix (default `docs/proposals/`)
- `process_changelog_path`: string path for process changelog
- `design_update_paths`: array of exact files/prefixes accepted as design update evidence
- `required_proposal_sections`: array of heading strings
- `required_proposal_fields`: array of marker strings
- `default_branch`: string (for merge-base and diff baseline)

### Work mode rule
```json
"mode_rule": {
  "enabled": true,
  "selected_mode_field": "- Selected work mode:",
  "allowed_modes": ["routine", "design"]
}
```

### No-assumption rule
```json
"no_assumption_rule": {
  "enabled": true,
  "assumptions_field": "- Assumptions made:",
  "confirmation_required_field": "- User confirmation required before implementation:",
  "confirmation_evidence_field": "- User confirmation evidence:"
}
```

## Strict recommendation
Keep all project-specific process requirements in policy, not in gate code.

