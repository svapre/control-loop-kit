# Policy Schema (Practical)

This document defines the expected shape of `.control-loop/policy.json`.

## Top-level object
```json
{
  "policy_override": {},
  "control_gate": {},
  "process_guard": {},
  "control_loop_integrity": {},
  "governance_amendment_rule": {},
  "governance_human_authority_rule": {},
  "ai_settings_loader": {},
  "ai_settings": {}
}
```

## `policy_override` keys
- `mode`: `"partial"` or `"full"`
- `waiver`: required if `mode` is `"full"`
  - `reason`: non-empty string
  - `approved_by`: non-empty string
  - `expires_on`: non-empty string

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
- `process_guideline_fields`: process markers (how work should be executed)
- `project_guideline_fields`: project quality markers (what output quality is required)
- `execution_phase_rules`: session-based phase/scope controls for `think` vs `implement` execution
- `contract_lifecycle_rules`: active-contract enforcement for controlled implementation scopes
  including status-transition and removal state-machine checks
- `default_branch`: string (for merge-base and diff baseline)
- session checks are controlled via `ai_settings.session_log`
- `design_principle_rules`: proposal field-value enforcement with per-rule severity (`strict` / `warn` / `manual_review`)
- `static_guard_rules`: regex-based scans for changed implementation files (for hardcoding/overfitting signals)

## `control_loop_integrity` keys
- `ci_workflow_path`: path to CI workflow to inspect (default `.github/workflows/ci.yml`)
- `required_gate_markers`: array of script markers expected in CI
- `stage0_check`: `"ignore"`, `"warn"`, or `"strict"` behavior for missing Stage0 marker
- `stage0_marker`: marker string expected in CI env (default `STAGE0_TAG`)

## `governance_amendment_rule` keys
- `enabled`: boolean
- `governance_files`: array of governance/constitutional file paths
- `required_token_field`: session marker used for amendment intent (legacy/manual flow)
- `required_token_value`: required token value (default `GOVERNANCE_CHANGE`)
- `review_evidence_field`: session marker used for human review evidence

## `governance_human_authority_rule` keys
- `enabled`: boolean
- `governance_files`: array of governance/constitutional file paths
- `required_approvers`: GitHub login list allowed to approve governance changes
- `minimum_approvals`: integer >= 1
- `require_approval_on_latest_commit`: boolean
- `allow_pr_authority_bypass`: boolean (optional; keep `false` for strict interactive approval flow)
- `authority_bypass_requires_pr_marker`: boolean (when `false`, bypass does not require PR-body marker text)
- `pr_authority_bypass_field`: PR body marker for authority self-signoff (used only when bypass enabled)
- `pr_authority_bypass_token`: required value for self-signoff marker (used only when bypass enabled)
- `require_human_reviewers`: boolean (ignore bot approvals when true)

Recommended for production governance:
- keep `governance_human_authority_rule.enabled=true`
- keep `allow_pr_authority_bypass=false` for multi-human teams
- enforce interactive human approval with GitHub Environment reviewers in CI

Sole-contributor profile (GitHub cannot approve own PR):
- set `allow_pr_authority_bypass=true`
- set `authority_bypass_requires_pr_marker=false`
- keep interactive Environment approval required in CI (`governance-amendment`)

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

### Execution phase rule profile
```json
"execution_phase_rules": {
  "enabled": true,
  "phase_field": "- Workflow phase:",
  "change_scope_field": "- Change scope:",
  "implementation_approval_token_field": "- Implementation approval token:",
  "required_implementation_approval_token": "APPROVE_IMPLEMENT",
  "allowed_phases": ["think", "implement"],
  "allowed_scopes": ["project", "toolkit", "both"],
  "toolkit_prefixes": ["tooling/control-loop-kit"]
}
```

### Contract lifecycle rule profile
```json
"contract_lifecycle_rules": {
  "enabled": true,
  "contract_path": ".control-loop/contracts.json",
  "id_pattern": "^CT-\\d{3}$",
  "allowed_statuses": ["draft", "approved", "active", "validated", "completed", "blocked", "stale", "cancelled"],
  "active_statuses": ["active"],
  "approval_flag_field": "approved",
  "approval_actor_field": "approved_by",
  "backlog_item_id_field": "backlog_item_id",
  "base_commit_field": "base_commit",
  "include_paths_field": "include_paths",
  "exclude_paths_field": "exclude_paths",
  "require_backlog_item_link": true,
  "require_approval": true,
  "require_base_commit_validation": true,
  "max_commits_since_base": 60,
  "enforce_transition_on_contract_change": true,
  "allowed_transitions": {
    "approved": ["active", "blocked", "stale", "cancelled"],
    "active": ["validated", "blocked", "stale", "cancelled"],
    "validated": ["completed", "active", "stale", "cancelled"]
  },
  "removal_allowed_statuses": ["completed", "cancelled"],
  "enforce_prefixes": ["core/", "scripts/", "control_loop/"],
  "enforce_files": ["main.py"],
  "ignore_prefixes": ["docs/"],
  "ignore_files": ["README.md", "CHANGELOG.md"]
}
```

### Design principle rule profile
```json
"design_principle_rules": {
  "null_tokens": ["", "none", "n/a", "na"],
  "manual_review_evidence_field": "- Manual review evidence:",
  "required_value_rules": [
    {"field": "- Generality scope:", "enforcement": "strict"},
    {"field": "- Single-case exception:", "enforcement": "manual_review"}
  ]
}
```

### Static guard rules
```json
"static_guard_rules": {
  "enabled": true,
  "scan_extensions": [".py"],
  "include_prefixes": ["core/", "utils/"],
  "include_files": ["main.py"],
  "rules": [
    {
      "name": "absolute_path_literals",
      "pattern": "(?:[A-Za-z]:\\\\\\\\|/Users/|/home/|/var/)",
      "enforcement": "strict",
      "message": "Detected absolute path literal in implementation code."
    }
  ]
}
```

## `ai_settings_loader` keys
- `default_path`: path to AI settings file (default `.control-loop/ai_settings.json`)
- `env_var`: environment variable name for AI settings path override

## `ai_settings` keys
### Global process switch
```json
"global_switch": {
  "enabled": true,
  "mode": "strict",
  "require_waiver_when_disabled": true,
  "waiver": {
    "reason": "N/A",
    "approved_by": "N/A",
    "expires_on": "N/A"
  }
}
```

### Response settings
```json
"response": {
  "detail_level": "normal",
  "language_style": "simple",
  "explanation_style": "action_reason",
  "progress_update_style": "frequent"
}
```

### Execution settings
```json
"execution": {
  "confirm_before_changes": true,
  "assumption_policy": "ask_first",
  "brainstorming_rule_strictness": "strict"
}
```

### Context management
```json
"context_management": {
  "context_index_path": "docs/CONTEXT_INDEX.md",
  "required_tiers": ["P0", "P1", "P2"]
}
```

### Session log settings
```json
"session_log": {
  "root": "docs/sessions/",
  "required_for_prefixes": ["core/", "scripts/"],
  "required_for_files": ["main.py"],
  "required_sections": ["## Request", "## Planned Actions"],
  "required_fields": ["- Session ID:", "- User approval status:"]
}
```

## Strict recommendation
Keep all project-specific process requirements in policy, not in gate code.
