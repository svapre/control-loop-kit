# Control Dashboard

- Source snapshot: `backlog=2026-02-24, setpoints=2026-02-24`
- Open backlog items: `7`
- Active items: `1`
- Blocked items: `0`
- Blocker items: `2`

## Status Breakdown
- `active`: `1`
- `closed`: `1`
- `planned`: `5`
- `triaged`: `1`

## Setpoint Health
| ID | Name | Current | Target | Status |
|---|---|---:|---:|---|
| SP-001 | CI pass rate (30d) | 1.0 | >= 0.98 ratio | on_track |
| SP-002 | Process regression incidents per month | 0 | <= 1 count | on_track |
| SP-003 | Median issue-to-validated cycle time (days) | 0 | <= 7 days | unknown |

## Top Priority Queue
- `BL-004` (now, score=167): Protect toolkit master branch with required CI and pull request flow -> next: Enable branch protection policy for master with required verify check and PR-only merges.
- `BL-007` (next, score=83): Single-file AI entrypoint contract via toolkit AGENTS.md and required read order -> next: Add toolkit-level AGENTS.md with canonical document order for any AI session.
- `BL-002` (now, score=60): Contract lifecycle state machine for execution gating -> next: Define contract schema and enforce active-contract scope in process guard.
- `BL-005` (next, score=50): Release hygiene: align tags with versioned releases and checklist -> next: Create release checklist and publish version tags for post-v0.3.0 releases.
- `BL-008` (next, score=50): CI guard for onboarding docs completeness and consistency -> next: Add machine check that AGENTS.md, guide docs, and roadmap references stay in sync.

## Roadmap Snapshot
### Now
- `BL-002` (active): Contract lifecycle state machine for execution gating
- `BL-004` (planned): Protect toolkit master branch with required CI and pull request flow
### Next
- `BL-005` (planned): Release hygiene: align tags with versioned releases and checklist
- `BL-006` (planned): Automate SP-003 metric collection for issue-to-validated cycle time
- `BL-007` (planned): Single-file AI entrypoint contract via toolkit AGENTS.md and required read order
- `BL-008` (planned): CI guard for onboarding docs completeness and consistency
### Later
- `BL-003` (triaged): AI capability levels and multi-agent coordination plan

## Immediate Focus
- `BL-004`: Protect toolkit master branch with required CI and pull request flow
- `BL-002`: Contract lifecycle state machine for execution gating

## Data Sources
- `.control-loop/backlog.json`
- `.control-loop/setpoints.json`
- `docs/ROADMAP.md`
