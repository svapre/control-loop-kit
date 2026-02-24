# Control Dashboard

- Source snapshot: `backlog=2026-02-24, setpoints=2026-02-24`
- Open backlog items: `3`
- Active items: `1`
- Blocked items: `0`
- Blocker items: `2`

## Status Breakdown
- `active`: `1`
- `planned`: `1`
- `triaged`: `1`

## Setpoint Health
| ID | Name | Current | Target | Status |
|---|---|---:|---:|---|
| SP-001 | CI pass rate (30d) | 1.0 | >= 0.98 ratio | on_track |
| SP-002 | Process regression incidents per month | 0 | <= 1 count | on_track |
| SP-003 | Median issue-to-validated cycle time (days) | 0 | <= 7 days | unknown |

## Top Priority Queue
- `BL-001` (now, score=167): Control cockpit foundation for roadmap and dashboard tracking -> next: Implement backlog/setpoint validators, dashboard renderer, and CI checks.
- `BL-002` (next, score=60): Contract lifecycle state machine for execution gating -> next: Define contract schema and enforce active-contract scope in process guard.
- `BL-003` (later, score=18): AI capability levels and multi-agent coordination plan -> next: Design capability-level schema and lock strategy for concurrent agents.

## Roadmap Snapshot
### Now
- `BL-001` (active): Control cockpit foundation for roadmap and dashboard tracking
### Next
- `BL-002` (planned): Contract lifecycle state machine for execution gating
### Later
- `BL-003` (triaged): AI capability levels and multi-agent coordination plan

## Immediate Focus
- `BL-001`: Control cockpit foundation for roadmap and dashboard tracking
- `BL-002`: Contract lifecycle state machine for execution gating

## Data Sources
- `.control-loop/backlog.json`
- `.control-loop/setpoints.json`
- `docs/ROADMAP.md`
