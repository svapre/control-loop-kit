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
                "- Config externalization evidence: values loaded from config files",
                "- Generality scope: chaptered textbooks and policy documents",
                "- Validation coverage evidence: validated on three representative documents",
                "- Holdout validation evidence: one unseen PDF validated without failures",
                "- Single-case exception: NONE",
                "- Manual review evidence: N/A",
                "- Determinism evidence: repeated run produced same output hash",
                "- Idempotent processing:",
                "- Idempotency evidence: second run produced no additional bookmarks/links",
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
                "- Workflow phase: implement",
                "- Change scope: project",
                "- Implementation approval token: APPROVE_IMPLEMENT",
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


def test_static_guard_detects_absolute_path_literal_as_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    policy = load_policy(repo_root=tmp_path)
    static_cfg = policy.setdefault("process_guard", {}).setdefault("static_guard_rules", {})
    static_cfg.update(
        {
            "enabled": True,
            "scan_extensions": [".py"],
            "include_prefixes": ["core/"],
            "include_files": ["main.py"],
            "rules": [
                {
                    "name": "absolute-path-literal",
                    "pattern": r"[A-Za-z]:\\\\",
                    "message": "absolute path literal detected; use config inputs instead",
                    "enforcement": "strict",
                }
            ],
        }
    )

    core_file = Path("core/profiler.py")
    core_file.parent.mkdir(parents=True, exist_ok=True)
    core_file.write_text("BASE = 'C:\\\\temp\\\\pdfs'\n", encoding="utf-8")

    failures = evaluate_change_coupling({core_file.as_posix()}, policy)

    assert any("absolute path literal" in item.lower() for item in failures)


def test_special_case_requires_manual_review_evidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    policy = load_policy(repo_root=tmp_path)
    design_cfg = policy.setdefault("process_guard", {}).setdefault("design_principle_rules", {})
    design_cfg.update(
        {
            "null_tokens": ["", "none", "n/a", "na", "tbd", "todo"],
            "manual_review_evidence_field": "- Manual review evidence:",
            "required_value_rules": [
                {
                    "field": "- Single-case exception:",
                    "enforcement": "manual_review",
                }
            ],
        }
    )

    proposal = Path("docs/proposals/2026-02-24-special-case.md")
    proposal.parent.mkdir(parents=True, exist_ok=True)
    proposal.write_text(
        "\n".join(
            [
                "# Proposal",
                "## Problem",
                "## Options Considered",
                "## Work Mode",
                "- Selected work mode: design",
                "- Why this mode: needs tradeoff analysis",
                "## Design Parameter Compliance",
                "- Structural correctness: preserved",
                "- Deterministic behavior: deterministic mapping",
                "- Traceable decisions: logged",
                "- No silent guessing: manual review on ambiguity",
                "- Configuration over hardcoding: config-based thresholds",
                "- Config externalization evidence: rules loaded from config",
                "- Generality scope: intended for chaptered PDFs",
                "- Validation coverage evidence: validated on three samples",
                "- Holdout validation evidence: one unseen sample passes",
                "- Single-case exception: hardcoded vendor header fallback",
                "- Manual review evidence: N/A",
                "- Determinism evidence: output hash stable",
                "- Idempotent processing: re-run safe",
                "- Idempotency evidence: no duplicates on second run",
                "- Fail loudly on invalid state: explicit warnings",
                "- Performance budget awareness: unchanged",
                "- Extensible module boundaries: separated stages",
                "- Evidence-backed claims: tests attached",
                "## Exception Register",
                "- Violated parameter(s): NONE",
                "- Why alternatives are worse: N/A",
                "- Risk: medium",
                "- Mitigation: rollback and review",
                "- Rollback plan: revert commit",
                "## Decision Scorecard",
                "- Correctness impact: high",
                "- Reliability impact: medium",
                "- Complexity impact: medium",
                "- Delivery speed impact: medium",
                "- Operational risk: medium",
                "- Why this is best overall now: temporary compatibility",
                "## Assumptions and Unknowns",
                "- Assumptions made: NONE",
                "- Unknowns: NONE",
                "- Clarifying questions for user: NONE",
                "## Approval Checkpoint",
                "- User confirmation required before implementation: no",
                "- User confirmation evidence: N/A",
                "## Decision",
                "## Risks and Mitigations",
                "## Validation Plan",
            ]
        ),
        encoding="utf-8",
    )

    session_log = Path("docs/sessions/2026-02-24-special-case.md")
    session_log.parent.mkdir(parents=True, exist_ok=True)
    session_log.write_text(
        "\n".join(
            [
                "# Session Log",
                "## Request",
                "- Session ID: session-special-case",
                "- Selected work mode: design",
                "- Task summary: special case trial",
                "## Planned Actions",
                "- Files planned to change: core/profiler.py",
                "- Why these changes: compatibility fallback",
                "- Workflow phase: implement",
                "- Change scope: project",
                "- Implementation approval token: APPROVE_IMPLEMENT",
                "## User Approval",
                "- User approval status: yes",
                "- User approval evidence: approved for experiment",
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
        proposal.as_posix(),
        "docs/adr/2026-02-24-special-case.md",
        session_log.as_posix(),
    }
    failures = evaluate_change_coupling(changed, policy)

    assert any("manual review evidence" in item.lower() for item in failures)


def test_contract_lifecycle_requires_file_for_controlled_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    policy = load_policy(repo_root=tmp_path)
    contract_cfg = policy.setdefault("process_guard", {}).setdefault("contract_lifecycle_rules", {})
    contract_cfg.update(
        {
            "enabled": True,
            "contract_path": ".control-loop/contracts.json",
            "enforce_prefixes": ["control_loop/"],
            "enforce_files": [],
            "ignore_prefixes": [],
            "ignore_files": [],
            "require_base_commit_validation": False,
        }
    )

    failures = evaluate_change_coupling({"control_loop/process_guard.py"}, policy)

    assert any("contract lifecycle file" in item.lower() for item in failures)


def test_contract_lifecycle_passes_with_valid_active_contract(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    policy = load_policy(repo_root=tmp_path)
    contract_cfg = policy.setdefault("process_guard", {}).setdefault("contract_lifecycle_rules", {})
    contract_cfg.update(
        {
            "enabled": True,
            "contract_path": ".control-loop/contracts.json",
            "enforce_prefixes": ["control_loop/"],
            "enforce_files": [],
            "ignore_prefixes": [],
            "ignore_files": [],
            "require_base_commit_validation": False,
        }
    )

    contract_file = Path(".control-loop/contracts.json")
    contract_file.parent.mkdir(parents=True, exist_ok=True)
    contract_file.write_text(
        "\n".join(
            [
                "{",
                '  "meta": {"schema_version": "1"},',
                '  "contracts": [',
                "    {",
                '      "id": "CT-001",',
                '      "title": "test",',
                '      "status": "active",',
                '      "approved": true,',
                '      "approved_by": "user",',
                '      "backlog_item_id": "BL-002",',
                '      "base_commit": "HEAD",',
                '      "include_paths": ["control_loop/"],',
                '      "exclude_paths": []',
                "    }",
                "  ]",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    failures = evaluate_change_coupling({"control_loop/process_guard.py"}, policy)

    assert not failures


def test_contract_lifecycle_fails_when_changed_path_is_outside_scope(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    policy = load_policy(repo_root=tmp_path)
    contract_cfg = policy.setdefault("process_guard", {}).setdefault("contract_lifecycle_rules", {})
    contract_cfg.update(
        {
            "enabled": True,
            "contract_path": ".control-loop/contracts.json",
            "enforce_prefixes": ["control_loop/"],
            "enforce_files": [],
            "ignore_prefixes": [],
            "ignore_files": [],
            "require_base_commit_validation": False,
        }
    )

    contract_file = Path(".control-loop/contracts.json")
    contract_file.parent.mkdir(parents=True, exist_ok=True)
    contract_file.write_text(
        "\n".join(
            [
                "{",
                '  "meta": {"schema_version": "1"},',
                '  "contracts": [',
                "    {",
                '      "id": "CT-001",',
                '      "title": "test",',
                '      "status": "active",',
                '      "approved": true,',
                '      "approved_by": "user",',
                '      "backlog_item_id": "BL-002",',
                '      "base_commit": "HEAD",',
                '      "include_paths": ["control_loop/policy.py"],',
                '      "exclude_paths": []',
                "    }",
                "  ]",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    failures = evaluate_change_coupling({"control_loop/process_guard.py"}, policy)

    assert any("outside active contract" in item.lower() for item in failures)

