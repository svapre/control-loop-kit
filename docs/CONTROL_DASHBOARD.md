# Control Dashboard

- Source snapshot: `backlog=2026-02-24, setpoints=2026-02-25`
- Open backlog items: `1`
- Active items: `1`
- Blocked items: `0`
- Blocker items: `0`

## Status Breakdown
- `active`: `1`
- `closed`: `7`

## Setpoint Health
| ID | Name | Current | Target | Status |
|---|---|---:|---:|---|
| SP-001 | CI pass rate (30d) | 1.0 | >= 0.98 ratio | on_track |
| SP-002 | Process regression incidents per month | 0 | <= 1 count | on_track |
| SP-003 | Median issue-to-validated cycle time (days) | 0 | <= 7 days | on_track |

## Top Priority Queue
- `BL-003` (later, score=18): AI capability levels and multi-agent coordination plan -> next: Design capability-level schema and lock strategy for concurrent agents.

## Roadmap Snapshot
### Now
- `BL-005` (closed): Release hygiene: align tags with versioned releases and checklist
### Next
- `BL-006` (closed): Automate SP-003 metric collection for issue-to-validated cycle time
### Later
- `BL-003` (active): AI capability levels and multi-agent coordination plan

## Immediate Focus
- No blocker items currently open.

## Data Sources
- `.control-loop/backlog.json`
- `.control-loop/setpoints.json`
- `docs/ROADMAP.md`
