# Control Toolkit Guide

## 1) Purpose
Control Loop Kit is a reusable engineering process toolkit for AI-assisted software projects.

It is built for teams where:
- humans set goals, constraints, and approvals
- AI executes most code and process work
- automated gates enforce quality and process discipline

The core model is a closed loop:
1. Measure
2. Compare to target
3. Correct
4. Re-measure

## 2) What the toolkit does
The toolkit provides two executable gates:

1. `control_gate`
- validates required process artifacts
- validates readiness requirements (clean worktree, local checks, CI success for current commit, readiness tag freshness)

2. `process_guard`
- enforces process-governance coupling rules
- enforces proposal structure
- enforces work-mode declaration (`routine` or `design`)
- enforces ambiguity stop rule (assumptions need confirmation evidence)
- enforces process-vs-project guideline markers from policy

## 3) Guarantees and non-guarantees
### Guarantees
- process checks are executable and repeatable
- implementation/process coupling is enforceable
- no-assumption and mode rules are machine-checked when configured

### Non-guarantees
- does not guarantee business logic is correct
- does not replace human architectural judgment
- does not eliminate all defects

## 4) Single-file AI onboarding contract
If an AI reads only one file, it should read this file before changes.

Required AI behavior:
1. Read project control docs in this order:
   - `MASTER_PLAN.md`
   - `SPEC.md`
   - `SYSTEM.md`
   - `DESIGN.md`
   - `GOVERNANCE.md`
   - `docs/USER_CONTEXT.md`
2. Declare work mode before major actions:
   - `routine` for low-risk implementation and maintenance
   - `design` for architecture, tradeoffs, or unclear requirements
3. Apply ambiguity stop rule:
   - if assumptions are needed, ask user first
   - do not implement assumption-based changes without confirmation evidence
4. Use policy config instead of hardcoding process rules.
5. Claim completion only with passing gate evidence.

## 5) Human manual setup instructions (any project)
Follow these steps in target repository.

### Step 1: Add toolkit dependency
```powershell
git submodule add https://github.com/svapre/control-loop-kit.git tooling/control-loop-kit
git -C tooling/control-loop-kit fetch --tags
git -C tooling/control-loop-kit checkout v0.3.0
```

### Step 2: Add local wrappers
Create `scripts/control_gate.py` and `scripts/process_guard.py` wrappers that import toolkit modules from:
- `CONTROL_LOOP_KIT_PATH` environment variable, or
- `tooling/control-loop-kit` submodule path

### Step 3: Add policy file
Create `.control-loop/policy.json` in the project root.

Recommended policy strategy:
1. Use partial override by default (`policy_override.mode = "partial"`).
2. Use full override only when needed and require waiver metadata:
   - `reason`
   - `approved_by`
   - `expires_on`

Policy resolution order:
1. `--policy <path>` CLI argument
2. `CONTROL_LOOP_POLICY_PATH` environment variable
3. project `.control-loop/policy.json`
4. toolkit `control_loop/default_policy.json`

Override behavior:
1. `partial`: deep-merge project override into toolkit base policy.
2. `full`: replace toolkit base policy with project policy, but only with waiver metadata.

### Step 4: Add CI integration
In CI, include:
1. checkout with submodules enabled
2. dependency install
3. lint
4. tests
5. process guard
6. control gate

### Step 5: Run local verification
```powershell
python -m ruff check .
python -m pytest -q
python scripts/process_guard.py --mode ci
python scripts/control_gate.py --mode ci
```

### Step 6: Enable branch protection (recommended)
Require:
- pull request merge flow
- required CI status check
- no force push
- no branch deletion

## 6) Minimum project files expected by default policy
- `MASTER_PLAN.md`
- `SPEC.md`
- `SYSTEM.md`
- `AGENTS.md`
- `DESIGN.md`
- `GOVERNANCE.md`
- `docs/USER_CONTEXT.md`
- `docs/PROCESS_CHANGELOG.md`
- `docs/proposals/README.md`
- `docs/proposals/TEMPLATE.md`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`

## 7) Proposal contract (enforced by process guard when configured)
Proposals must include:
- work mode
- design parameter compliance matrix
- exception register
- decision scorecard
- assumptions and unknowns
- approval checkpoint with confirmation evidence
- validation plan

## 8) Reference roadmap (human + AI)
### Phase A: Bootstrap
1. Add toolkit
2. Add wrappers
3. Add policy file
4. Add baseline control docs and CI wiring

### Phase B: Stabilization
1. Run gates
2. Fix failures
3. Re-run until green

### Phase C: Feature Delivery
1. Proposal update
2. Implementation
3. Tests + gates
4. PR + merge

### Phase D: Toolkit Upgrade
1. Bump toolkit version/tag
2. Run full validation
3. Merge if green
4. Refresh readiness marker if project uses one

## 9) Why this is AI-agnostic
The process is not tied to one model.

It is portable because:
- rules are configuration-driven (`policy.json`)
- pass/fail logic is executable
- documentation defines mandatory behavior independent of model vendor
- human approval remains explicit and external

## 10) Process vs project guidelines
The toolkit separates two guideline classes in policy:

1. Process guidelines:
- how work is done
- examples: work mode declaration, assumptions/unknowns, approval checkpoint

2. Project guidelines:
- what quality principles the project output must satisfy
- examples: deterministic behavior, no hardcoding, fail loudly, traceability

Projects can override either set partially or fully through policy, with guardrails.
