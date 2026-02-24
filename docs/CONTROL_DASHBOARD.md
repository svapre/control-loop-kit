# Control Dashboard

- Source snapshot: `backlog=2026-02-24, setpoints=2026-02-24`
- Open backlog items: `5`
- Active items: `1`
- Blocked items: `0`
- Blocker items: `2`

## Status Breakdown
- `active`: `1`
- `closed`: `1`
- `planned`: `3`
- `triaged`: `1`

## Setpoint Health
| ID | Name | Current | Target | Status |
|---|---|---:|---:|---|
| SP-001 | CI pass rate (30d) | 1.0 | >= 0.98 ratio | on_track |
| SP-002 | Process regression incidents per month | 0 | <= 1 count | on_track |
| SP-003 | Median issue-to-validated cycle time (days) | 0 | <= 7 days | unknown |

## Top Priority Queue
- `BL-004` (now, score=167): Protect toolkit master branch with required CI and pull request flow -> next: Enable branch protection policy for master with required verify check and PR-only merges.
- `BL-002` (now, score=60): Contract lifecycle state machine for execution gating -> next: Define contract schema and enforce active-contract scope in process guard.
- `BL-005` (next, score=50): Release hygiene: align tags with versioned releases and checklist -> next: Create release checklist and publish version tags for post-v0.3.0 releases.
- `BL-006` (next, score=30): Automate SP-003 metric collection for issue-to-validated cycle time -> next: Add metric collector script and keep setpoint current_value synchronized from evidence.
- `BL-003` (later, score=18): AI capability levels and multi-agent coordination plan -> next: Design capability-level schema and lock strategy for concurrent agents.

## Roadmap Snapshot
### Now
- `BL-002` (active): Contract lifecycle state machine for execution gating
- `BL-004` (planned): Protect toolkit master branch with required CI and pull request flow
### Next
- `BL-005` (planned): Release hygiene: align tags with versioned releases and checklist
- `BL-006` (planned): Automate SP-003 metric collection for issue-to-validated cycle time
### Later
- `BL-003` (triaged): AI capability levels and multi-agent coordination plan

## Immediate Focus
- `BL-004`: Protect toolkit master branch with required CI and pull request flow
- `BL-002`: Contract lifecycle state machine for execution gating

## Data Sources
- `.control-loop/backlog.json`
- `.control-loop/setpoints.json`
- `docs/ROADMAP.md`
