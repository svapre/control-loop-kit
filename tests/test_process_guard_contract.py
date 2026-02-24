from pathlib import Path

from control_loop.policy import load_policy
from control_loop.process_guard import evaluate_change_coupling


def test_process_vs_project_fields_loaded_from_policy():
    policy = load_policy()
    process_fields = policy["process_guard"]["process_guideline_fields"]
    project_fields = policy["process_guard"]["project_guideline_fields"]

    assert "- Selected work mode:" in process_fields
    assert "- Structural correctness:" in project_fields


def test_process_change_requires_changelog_update():
    policy = load_policy()
    failures = evaluate_change_coupling({"SPEC.md"}, policy)

    assert any("PROCESS_CHANGELOG" in item for item in failures)


def test_implementation_change_requires_session_log_update():
    policy = load_policy()
    failures = evaluate_change_coupling({"core/profiler.py"}, policy)

    assert any("session log update" in item.lower() for item in failures)


def test_implementation_change_passes_with_proposal_design_and_session(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    policy = load_policy(repo_root=tmp_path)

    proposal = Path("docs/proposals/2026-02-24-test.md")
    proposal.parent.mkdir(parents=True, exist_ok=True)
    proposal.write_text(
        "\n".join(
            [
                "# Proposal",
                "## Problem",
                "## Options Considered",
                "## Work Mode",
                "- Selected work mode: routine",
                "- Why this mode: routine implementation and validation tasks",
                "## Design Parameter Compliance",
                "- Structural correctness:",
                "- Deterministic behavior:",
                "- Traceable decisions:",
                "- No silent guessing:",
                "- Configuration over hardcoding:",
                "- Idempotent processing:",
                "- Fail loudly on invalid state:",
                "- Performance budget awareness:",
                "- Extensible module boundaries:",
                "- Evidence-backed claims:",
                "## Exception Register",
                "- Violated parameter(s): NONE",
                "- Why alternatives are worse: N/A",
                "- Risk: LOW",
                "- Mitigation: tests",
                "- Rollback plan: revert commit",
                "## Decision Scorecard",
                "- Correctness impact: high",
                "- Reliability impact: high",
                "- Complexity impact: low",
                "- Delivery speed impact: medium",
                "- Operational risk: low",
                "- Why this is best overall now: balanced tradeoff",
                "## Assumptions and Unknowns",
                "- Assumptions made: NONE",
                "- Unknowns: NONE",
                "- Clarifying questions for user: NONE",
                "## Approval Checkpoint",
                "- User confirmation required before implementation: no",
                "- User confirmation evidence: N/A",
                "## Decision",
                "Selected option.",
                "## Risks and Mitigations",
                "Low risk.",
                "## Validation Plan",
                "Run tests.",
            ]
        ),
        encoding="utf-8",
    )

    session_log = Path("docs/sessions/2026-02-24-test.md")
    session_log.parent.mkdir(parents=True, exist_ok=True)
    session_log.write_text(
        "\n".join(
            [
                "# Session Log",
                "## Request",
                "- Session ID: session-1",
                "- Selected work mode: routine",
                "- Task summary: test setup",
                "## Planned Actions",
                "- Files planned to change: core/profiler.py",
                "- Why these changes: improve enforcement",
                "## User Approval",
                "- User approval status: yes",
                "- User approval evidence: user said go ahead",
                "## AI Settings Applied",
                "- confirm_before_changes: true",
                "- assumption_policy: ask_first",
                "- process_enforcement_mode: strict",
                "## Execution Log",
                "- Failure observed: none",
                "- Corrective change made: n/a",
                "- Validation checks run: tests",
                "## Results and Feedback",
                "- Feedback received: none",
                "- Feedback applied: none",
            ]
        ),
        encoding="utf-8",
    )

    changed = {
        "core/profiler.py",
        "docs/proposals/2026-02-24-test.md",
        "docs/adr/2026-02-24-test.md",
        "docs/sessions/2026-02-24-test.md",
    }
    failures = evaluate_change_coupling(changed, policy)

    assert not failures

