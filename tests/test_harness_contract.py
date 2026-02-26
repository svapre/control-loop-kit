from __future__ import annotations

from pathlib import Path

from control_loop import harness


def write_session(path: Path, token_value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Session Log: test",
                "",
                "## Request",
                "- Session ID: test-session",
                "- Selected work mode: routine",
                "- Task summary: harness test",
                "",
                "## Planned Actions",
                "- Files planned to change: control_loop/harness.py",
                "- Why these changes: test",
                "- Workflow phase: implement",
                "- Change scope: project",
                f"- Implementation approval token: {token_value}",
                "",
                "## User Approval",
                "- User approval status: yes",
                "- User approval evidence: approved",
                "",
                "## AI Settings Applied",
                "- confirm_before_changes: true",
                "- assumption_policy: ask_first",
                "- process_enforcement_mode: strict",
                "",
                "## Execution Log",
                "- Failure observed: none",
                "- Corrective change made: n/a",
                "- Validation checks run:",
                "",
                "## Results and Feedback",
                "- Feedback received: none",
                "- Feedback applied: none",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_harness_implement_requires_approval_token(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = tmp_path / "docs" / "sessions" / "2026-02-26-token-missing.md"
    write_session(session, "")

    def fail_if_called(cmd: tuple[str, ...], repo_root: Path):
        raise AssertionError(f"command runner should not be called: {cmd} @ {repo_root}")

    monkeypatch.setattr(harness, "run_command_capture", fail_if_called)
    code = harness.main(["run", "--phase", "implement", "--session", str(session)])

    assert code == 1
    text = session.read_text(encoding="utf-8")
    assert "- FAIL | approval_token_check |" in text
    assert "APPROVE_IMPLEMENT" in text


def test_harness_implement_passes_with_matching_token(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = tmp_path / "docs" / "sessions" / "2026-02-26-token-present.md"
    write_session(session, "APPROVE_IMPLEMENT")

    def fake_runner(cmd: tuple[str, ...], repo_root: Path) -> tuple[int, str, str]:
        return 0, "", ""

    monkeypatch.setattr(harness, "run_command_capture", fake_runner)
    code = harness.main(["run", "--phase", "implement", "--session", str(session)])

    assert code == 0
    text = session.read_text(encoding="utf-8")
    assert "- PASS | approval_token_check" in text
    assert "- PASS | python -m pytest -q" in text
