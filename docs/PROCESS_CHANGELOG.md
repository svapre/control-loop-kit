# Process Changelog

This log tracks changes to control-system process, policy, and governance artifacts.

## 2026-03-01 - Structured amendment artifact channel (overlap stage)
- Replaced PR-body declaration as primary machine-readable source with repository-tracked amendment artifacts:
  - `.control-loop/amendments/<slug>.json`.
- Governance-affecting PRs now require exactly one changed amendment artifact file.
- Added amendment artifact schema v1 validation:
  - required fields present,
  - `schema_version` must be `"1"`,
  - `amendment_id` must equal filename stem,
  - `candidate_tier` must be `C0`, `C1`, or `C2`,
  - `draft_status` must be `draft`,
  - optional fields allowed: `rationale`, `references`, `notes`.
- Overlap behavior:
  - PR-body declaration is optional.
  - if PR-body declaration is present, key fields must match artifact values.
- Existing tier doctrine, admissibility logic, and survival-floor checks remain unchanged aside from declaration source handling.

## 2026-03-01 - Slice 2B Stage0 minimum-floor activation (promotion)
- Published release tag `v0.8.0` from commit `17728d3` (Slice 2A baseline).
- Updated CI Stage0 controller pin:
  - `.github/workflows/ci.yml` now sets `STAGE0_TAG: v0.8.0` (was `v0.7.0`).
- Constitutional effect:
  - activates Stage0 minimum C0 survival-floor adjudication in the pinned external judge path.
  - local checker remains broader/redundant self-governance visibility; no new governance logic introduced in this promotion PR.

## 2026-03-01 - Slice 2A Stage0-capable minimum survival floor (implementation only)
- Added Stage0-capable governance survival profile:
  - `scripts/verify_governance_survival.py` now supports `--profile stage0_min_floor` alongside default local/full behavior.
- Stage0 minimum-floor profile behavior:
  - declaration enforcement applies only for Stage0 overlap scope,
  - checks only minimum C0 survival posture,
  - keeps richer local/full semantics outside Stage0 minimum-floor mode.
- Updated Stage0 gate suite definition:
  - `scripts/run_gate_suite.py --suite stage0` now includes
    `python scripts/verify_governance_survival.py --check --profile stage0_min_floor`.
- Added/updated governance survival contract tests for:
  - Stage0 declaration overlap scoping,
  - C0 weakening rejection in overlap scope,
  - minimum-posture-only Stage0 behavior,
  - preservation of existing local/full Slice 1 behavior.
- Updated gate-suite documentation to describe Stage0 minimum-floor semantics.
- This is implementation-only for Slice 2A:
  - no `.github/workflows/ci.yml` change,
  - no `STAGE0_TAG` promotion/bump (Slice 2B).

## 2026-02-27 - Stage0 v0.7.0 activation in CI
- Published release tag `v0.7.0` from `master`.
- Updated CI Stage0 controller pin:
  - `.github/workflows/ci.yml` now sets `STAGE0_TAG: v0.7.0`.
- Switched Stage0 execution to suite-runner mode:
  - replaced per-command Stage0 checks with
    `python /tmp/stage0/scripts/run_gate_suite.py --suite stage0 --target-root "$GITHUB_WORKSPACE"`.
- Result: merge-blocking Stage0 governance now runs the trusted frozen suite from the v0.7.0 controller.

## 2026-02-27 - Machine-verifiable governance authority gate
- Added `scripts/verify_governance_authority.py`:
  - checks pull request metadata via GitHub API,
  - enforces that governance-file changes have qualifying approval authority,
  - evaluates against effective base+head policy config so a PR cannot disable authority checks and bypass review.
- Added `governance_human_authority_rule` policy block:
  - schema validation in `control_loop/policy.py`,
  - default shape in `control_loop/default_policy.json`,
  - enabled project override in `.control-loop/policy.json`.
- Wired CI enforcement in `verify` job:
  - new step `Governance Human Authority Check` with `GITHUB_TOKEN`.
- Added interactive approval gate in CI:
  - `detect-governance-changes` computes governance-file changes from base+head policy union.
  - `governance-human-approval` pauses in GitHub Environment `governance-amendment` for human approval.
  - `stage0-governance` and `verify` proceed only after approval or when the gate is not applicable.
  - merge-blocking jobs are restricted to `pull_request` events so push-run statuses cannot satisfy required checks prematurely.
- Disabled this repository's legacy token-based governance-amendment gate (`governance_amendment_rule.enabled=false`).
- Added sole-contributor authority profile support:
  - policy key `authority_bypass_requires_pr_marker`,
  - verifier accepts configured self-bypass without marker text when enabled,
  - used with mandatory interactive environment approval to avoid self-review deadlock.
- Added contract tests:
  - `tests/test_governance_authority_contract.py`,
  - policy validation tests in `tests/test_policy_contract.py`.
- Added `.github/CODEOWNERS` mapping for governance/constitutional files (effective when code-owner review is enabled in branch protection).
- Updated policy and gate-suite docs for the new rule and check.

## 2026-02-24 - Toolkit location decoupled from project repository
- Removed toolkit submodule from this repository (`tooling/control-loop-kit`).
- Updated wrappers to resolve toolkit in this order:
  - `CONTROL_LOOP_KIT_PATH`
  - sibling path `../control-loop-kit`
  - legacy in-repo path `tooling/control-loop-kit`
- This keeps project code and toolkit code in separate repositories by default.

## 2026-02-23 - Process governance hardening
- Added `scripts/process_guard.py` to enforce process-change and design-coupling rules.
- Added proposal-structure enforcement so proposal files must contain required decision sections.
- Added `DESIGN.md` with design guardrails and brainstorming protocol.
- Added `GOVERNANCE.md` with proposal-first and process-change rules.
- Added `.github/pull_request_template.md` with required governance checklist.
- Updated `SPEC.md`, `SYSTEM.md`, `AGENTS.md`, `MASTER_PLAN.md`, and CI workflow to include process guard checks.

## 2026-02-23 - Communication profile codification
- Added `docs/USER_CONTEXT.md` to persist user background and plain-language communication preferences.
- Updated `AGENTS.md` read order and update rules to require plain-language, acronym expansion, and terminology definitions.
- Updated `GOVERNANCE.md` with a communication contract tied to process quality.
- Updated `SPEC.md` to include user-context communication expectations.
- Updated `scripts/control_gate.py` and `scripts/process_guard.py` to require `docs/USER_CONTEXT.md`.
- Updated `docs/README.md` index for discoverability.

## 2026-02-23 - Design-parameter and operating-model hardening
- Expanded `DESIGN.md` into explicit project design parameters and added formal exception rule.
- Updated `GOVERNANCE.md` with human-AI operating model, two work modes, and evidence-based acceptance rule.
- Upgraded `docs/proposals/TEMPLATE.md` to require:
  - design-parameter compliance section
  - exception register
  - decision scorecard
  - validation plan
- Updated `scripts/process_guard.py` to enforce new proposal sections and field markers.
- Extended process-controlled file list in `scripts/process_guard.py` to include proposal/process templates.
- Updated `tests/test_process_guard_contract.py` for new proposal contract and process-change coverage.
- Updated `SPEC.md` and `AGENTS.md` to reflect new acceptance and brainstorming constraints.

## 2026-02-24 - Process extraction and policy-driven upgrade test
- Created separate reusable process repository: `svapre/control-loop-kit`.
- Integrated toolkit in this project as a pinned submodule: `tooling/control-loop-kit`.
- Replaced local gate implementations with compatibility wrappers:
  - `scripts/control_gate.py`
  - `scripts/process_guard.py`
- Updated CI checkout to initialize submodules.
- Published toolkit `v0.2.0` with:
  - policy-driven rules (`default_policy.json` + override support),
  - work-mode enforcement (`routine`/`design`),
  - ambiguity/no-assumption stop rule requiring confirmation evidence.
- Added project policy override at `.control-loop/policy.json`.
- Updated proposal template and governance/spec rules to include:
  - work mode declaration,
  - assumptions/unknowns,
  - approval checkpoint and confirmation evidence.
- Updated process-guard contract tests for new rule set.

## 2026-02-24 - Toolkit documentation release adoption
- Upgraded toolkit submodule from `v0.2.0` to `v0.2.1`.
- Adopted toolkit docs release containing:
  - `docs/CONTROL_TOOLKIT_GUIDE.md` (single-file human + AI onboarding),
  - `docs/QUICKSTART.md` (manual integration steps),
  - `docs/POLICY_SCHEMA.md` (policy structure reference).

## 2026-02-24 - Toolkit policy governance upgrade adoption
- Upgraded toolkit submodule from `v0.2.1` to `v0.3.0`.
- Adopted toolkit runtime policy validation and controlled override modes:
  - partial override merge mode,
  - full override mode with mandatory waiver metadata.
- Added explicit project override directive in `.control-loop/policy.json`:
  - `"policy_override": { "mode": "partial" }`
- Adopted toolkit self-CI and toolkit-level tests for policy/process enforcement.

## 2026-02-24 - AI settings and session evidence enforcement
- Added project AI settings file at `.control-loop/ai_settings.json`.
- Added context-priority index at `docs/CONTEXT_INDEX.md`.
- Added session evidence workflow:
  - `docs/sessions/README.md`
  - `docs/sessions/TEMPLATE.md`
  - session log for this change
- Updated policy required artifact lists to include AI settings, context index, and session docs.
- Extended shared toolkit (submodule working tree) with:
  - AI settings loader and schema validation,
  - global strict/advisory process switch,
  - session evidence checks in `process_guard`,
  - reusable templates for AI settings/context/session files.

## 2026-02-24 - Model-catalog contract and prompt sync foundation
- Updated toolkit submodule with contract-driven model-catalog artifacts:
  - `contracts/model_catalog.contract.json` (source-of-truth format),
  - `contracts/MODEL_CATALOG_PROMPT.md` (generated prompt for any AI),
  - `scripts/generate_model_catalog_prompt.py` (generator + sync checker).
- Added toolkit CI enforcement:
  - `python scripts/generate_model_catalog_prompt.py --check`.
- Added toolkit tests:
  - `tests/test_model_catalog_contract.py` for route-candidate shape and prompt-sync assertions.
- This is step 1 for model-switching refinement: lock format + prevent prompt drift before router runtime changes.

## 2026-02-24 - Design robustness severity enforcement
- Extended toolkit process guard with policy-driven rule severities:
  - `strict` (hard fail),
  - `warn` (warning),
  - `manual_review` (explicit human review signal with evidence requirement when special-cases are declared).
- Added policy-driven static guard checks for changed implementation code:
  - strict failure on absolute path literals,
  - manual-review signal on hardcoded PDF filename literals.
- Added policy schema/validation support for:
  - `process_guard.design_principle_rules`,
  - `process_guard.static_guard_rules`.
- Updated project design/process docs and proposal templates to include mechanical evidence for:
  - generality scope,
  - corpus and holdout validation,
  - config externalization,
  - determinism and idempotency.
- Updated project and toolkit process-guard contract tests for the new field/rule set.

## 2026-02-24 - Toolkit generic-boundary recovery and phase/scope gating
- Corrected toolkit defaults to remain project-agnostic:
  - changed generic markers to `- Validation coverage evidence:` and `- Single-case exception:`,
  - removed PDF-project-specific default markers from toolkit policy.
- Added execution-phase governance in toolkit process guard:
  - enforced session markers for `- Workflow phase:`, `- Change scope:`, and `- Implementation approval token:`,
  - enforced think-vs-implement boundaries with `scripts/process_guard.py --mode think|ci`.
- Kept project-specific strict design/static rules only in this repository override:
  - `.control-loop/policy.json` continues to define PDF-project-specific markers and strict/manual-review tuning.
- Updated toolkit docs/tests to prevent regression:
  - policy schema docs updated for phase rules and generic marker examples,
  - added toolkit policy contract test asserting defaults stay project-agnostic.
- Updated session template fields and aligned project/toolkit contract tests with new phase markers.
