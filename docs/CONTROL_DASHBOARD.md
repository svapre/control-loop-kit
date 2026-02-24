# Control Dashboard

- Source snapshot: `backlog=2026-02-24, setpoints=2026-02-24`
- Open backlog items: `3`
- Active items: `1`
- Blocked items: `0`
- Blocker items: `0`

## Status Breakdown
- `active`: `1`
- `closed`: `5`
- `planned`: `1`
- `triaged`: `1`

## Setpoint Health
| ID | Name | Current | Target | Status |
|---|---|---:|---:|---|
| SP-001 | CI pass rate (30d) | 1.0 | >= 0.98 ratio | on_track |
| SP-002 | Process regression incidents per month | 0 | <= 1 count | on_track |
| SP-003 | Median issue-to-validated cycle time (days) | 0 | <= 7 days | unknown |

## Top Priority Queue
- `BL-005` (now, score=50): Release hygiene: align tags with versioned releases and checklist -> next: Create release checklist and publish version tags for post-v0.3.0 releases.
- `BL-006` (next, score=30): Automate SP-003 metric collection for issue-to-validated cycle time -> next: Add metric collector script and keep setpoint current_value synchronized from evidence.
- `BL-003` (later, score=18): AI capability levels and multi-agent coordination plan -> next: Design capability-level schema and lock strategy for concurrent agents.

## Roadmap Snapshot
### Now
- `BL-005` (active): Release hygiene: align tags with versioned releases and checklist
### Next
- `BL-006` (planned): Automate SP-003 metric collection for issue-to-validated cycle time
### Later
- `BL-003` (triaged): AI capability levels and multi-agent coordination plan

## Immediate Focus
- No blocker items currently open.

## Data Sources
- `.control-loop/backlog.json`
- `.control-loop/setpoints.json`
- `docs/ROADMAP.md`
