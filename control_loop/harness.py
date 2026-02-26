"""Local execution harness for phase-aware governance workflows."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from control_loop.policy import load_policy


DEFAULT_SCOPE = "project"
SESSION_TEMPLATE_PATH = Path("docs/SESSION_TEMPLATE.md")
DEFAULT_SESSION_IGNORED = {"README.md", "TEMPLATE.md"}
NO_VALID_SESSION_MESSAGE = "No valid session found. Run: python -m control_loop.harness start first."


@dataclass(frozen=True)
class CommandSpec:
    display: str
    args: tuple[str, ...]


THINK_SUITE: tuple[CommandSpec, ...] = (
    CommandSpec(
        "python scripts/generate_model_catalog_prompt.py --check",
        (sys.executable, "scripts/generate_model_catalog_prompt.py", "--check"),
    ),
    CommandSpec(
        "python scripts/validate_backlog.py --check",
        (sys.executable, "scripts/validate_backlog.py", "--check"),
    ),
    CommandSpec(
        "python scripts/sync_setpoints.py --check",
        (sys.executable, "scripts/sync_setpoints.py", "--check"),
    ),
    CommandSpec(
        "python scripts/render_dashboard.py --check",
        (sys.executable, "scripts/render_dashboard.py", "--check"),
    ),
    CommandSpec(
        "python scripts/validate_onboarding_docs.py --check",
        (sys.executable, "scripts/validate_onboarding_docs.py", "--check"),
    ),
    CommandSpec(
        "python scripts/validate_release_hygiene.py --check --allow-unreleased-latest",
        (
            sys.executable,
            "scripts/validate_release_hygiene.py",
            "--check",
            "--allow-unreleased-latest",
        ),
    ),
)

IMPLEMENT_SUITE: tuple[CommandSpec, ...] = THINK_SUITE + (
    CommandSpec("python -m ruff check .", (sys.executable, "-m", "ruff", "check", ".")),
    CommandSpec("python -m pytest -q", (sys.executable, "-m", "pytest", "-q")),
)


def discover_repo_root(start: Path | None = None) -> Path:
    origin = start or Path.cwd()
    for candidate in [origin, *origin.parents]:
        if (candidate / ".control-loop" / "policy.json").exists():
            return candidate
    return Path(__file__).resolve().parents[1]


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    if not slug:
        slug = "session"
    return slug[:60].strip("-")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def marker_index(lines: list[str], marker: str) -> int:
    target = marker.lower()
    for idx, line in enumerate(lines):
        if line.strip().lower().startswith(target):
            return idx
    return -1


def set_marker_value(lines: list[str], marker: str, value: str) -> bool:
    idx = marker_index(lines, marker)
    if idx < 0:
        return False
    prefix = marker.rstrip()
    tail = f" {value.strip()}" if value.strip() else ""
    lines[idx] = f"{prefix}{tail}"
    return True


def get_marker_value(lines: list[str], marker: str) -> str:
    idx = marker_index(lines, marker)
    if idx < 0:
        return ""
    line = lines[idx].strip()
    if ":" not in line:
        return ""
    return line.split(":", 1)[1].strip()


def set_marker_block(lines: list[str], marker: str, entries: list[str]) -> bool:
    idx = marker_index(lines, marker)
    if idx < 0:
        return False

    end = idx + 1
    while end < len(lines) and lines[end].startswith("  - "):
        end += 1

    block = [f"  {entry}" for entry in entries]
    lines[idx + 1 : end] = block
    return True


def run_command_capture(cmd: tuple[str, ...], repo_root: Path) -> tuple[int, str, str]:
    proc = subprocess.run(list(cmd), cwd=str(repo_root), capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def short_reason(stderr: str, stdout: str, rc: int) -> str:
    text = stderr or stdout
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned.replace("|", "/")[:240]
    return f"exit={rc}"


def session_root_from_policy(policy: dict[str, Any], repo_root: Path) -> Path:
    ai_cfg = policy.get("ai_settings", {})
    session_cfg = ai_cfg.get("session_log", {}) if isinstance(ai_cfg, dict) else {}
    root = session_cfg.get("root", "docs/sessions/")
    if not isinstance(root, str) or not root.strip():
        root = "docs/sessions/"
    path = Path(root)
    if not path.is_absolute():
        path = repo_root / path
    return path


def normalize_path_string(path: Path) -> str:
    return str(path).replace("\\", "/").lower()


def session_ignored_files(policy: dict[str, Any], repo_root: Path) -> tuple[set[str], set[str]]:
    ai_cfg = policy.get("ai_settings", {})
    session_cfg = ai_cfg.get("session_log", {}) if isinstance(ai_cfg, dict) else {}
    raw_ignored = session_cfg.get("ignored_files", [])
    if not isinstance(raw_ignored, list):
        raw_ignored = []

    ignored_paths: set[str] = set()
    ignored_rel_paths: set[str] = set()
    for name in DEFAULT_SESSION_IGNORED:
        default_path = repo_root / "docs" / "sessions" / name
        ignored_paths.add(normalize_path_string(default_path.resolve()))
        ignored_rel_paths.add(f"docs/sessions/{name}".lower())

    for entry in raw_ignored:
        if not isinstance(entry, str) or not entry.strip():
            continue
        path = Path(entry)
        ignored_rel_paths.add(path.as_posix().lower())
        if not path.is_absolute():
            path = repo_root / path
        ignored_paths.add(normalize_path_string(path.resolve()))
    return ignored_paths, ignored_rel_paths


def is_ignored_session_file(path: Path, repo_root: Path, ignored_paths: set[str], ignored_rel_paths: set[str]) -> bool:
    path_abs = normalize_path_string(path.resolve())
    if path_abs in ignored_paths:
        return True
    try:
        relative = path.relative_to(repo_root).as_posix().lower()
    except ValueError:
        relative = ""
    return bool(relative and relative in ignored_rel_paths)


def resolve_session_path(
    repo_root: Path,
    policy: dict[str, Any],
    explicit: str | None,
    latest: bool,
) -> Path:
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        return candidate

    session_root = session_root_from_policy(policy, repo_root)
    ignored_paths, ignored_rel_paths = session_ignored_files(policy, repo_root)
    files = [
        path
        for path in session_root.glob("*.md")
        if not is_ignored_session_file(path, repo_root, ignored_paths, ignored_rel_paths)
    ]
    files = sorted(files, key=lambda path: (path.stat().st_mtime, path.name))
    if not files:
        raise ValueError(NO_VALID_SESSION_MESSAGE)
    if latest or not explicit:
        return files[-1]
    return files[-1]


def required_token_config(policy: dict[str, Any]) -> tuple[str, str]:
    process_cfg = policy.get("process_guard", {})
    if not isinstance(process_cfg, dict):
        process_cfg = {}
    phase_cfg = process_cfg.get("execution_phase_rules", {})
    if not isinstance(phase_cfg, dict):
        phase_cfg = {}
    token_field = str(
        phase_cfg.get("implementation_approval_token_field", "- Implementation approval token:")
    )
    required_token = str(phase_cfg.get("required_implementation_approval_token", "APPROVE_IMPLEMENT"))
    return token_field, required_token


def session_null_tokens(policy: dict[str, Any]) -> set[str]:
    ai_cfg = policy.get("ai_settings", {})
    session_cfg = ai_cfg.get("session_log", {}) if isinstance(ai_cfg, dict) else {}
    raw = session_cfg.get("null_tokens", ["none", "n/a", "na", ""])
    if not isinstance(raw, list):
        raw = ["none", "n/a", "na", ""]
    tokens = {str(item).strip().lower() for item in raw if isinstance(item, str)}
    tokens.add("")
    return tokens


def ensure_markers(lines: list[str], markers: list[str]) -> list[str]:
    missing = [marker for marker in markers if marker_index(lines, marker) < 0]
    return missing


def suite_for_phase(phase: str) -> tuple[CommandSpec, ...]:
    return THINK_SUITE if phase == "think" else IMPLEMENT_SUITE


def command_start(args: argparse.Namespace) -> int:
    repo_root = discover_repo_root(Path(args.root).resolve() if args.root else None)
    policy = load_policy(repo_root=repo_root)
    template_path = repo_root / SESSION_TEMPLATE_PATH
    if not template_path.exists():
        print(f"FAIL: missing session template: {template_path.as_posix()}")
        return 1

    session_root = session_root_from_policy(policy, repo_root)
    session_root.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    slug = slugify(args.task)
    session_path = session_root / f"{today}-{slug}.md"
    if session_path.exists():
        print(f"FAIL: session already exists: {session_path.as_posix()}")
        return 1

    lines = read_lines(template_path)
    required_markers = [
        "- Session ID:",
        "- Selected work mode:",
        "- Task summary:",
        "- Files planned to change:",
        "- Why these changes:",
        "- Workflow phase:",
        "- Change scope:",
        "- Implementation approval token:",
        "- User approval status:",
        "- User approval evidence:",
        "- confirm_before_changes:",
        "- assumption_policy:",
        "- process_enforcement_mode:",
        "- Failure observed:",
        "- Corrective change made:",
        "- Validation checks run:",
        "- Feedback received:",
        "- Feedback applied:",
    ]
    missing = ensure_markers(lines, required_markers)
    if missing:
        print("FAIL: session template missing required markers")
        for marker in missing:
            print(f"- {marker}")
        return 1

    ai_cfg = policy.get("ai_settings", {})
    execution_cfg = ai_cfg.get("execution", {}) if isinstance(ai_cfg, dict) else {}
    switch_cfg = ai_cfg.get("global_switch", {}) if isinstance(ai_cfg, dict) else {}

    selected_mode = "design" if args.phase == "think" else "routine"
    set_marker_value(lines, "- Session ID:", session_path.stem)
    set_marker_value(lines, "- Selected work mode:", selected_mode)
    set_marker_value(lines, "- Task summary:", args.task)
    set_marker_value(lines, "- Files planned to change:", "TBD")
    set_marker_value(lines, "- Why these changes:", args.task)
    set_marker_value(lines, "- Workflow phase:", args.phase)
    set_marker_value(lines, "- Change scope:", args.scope)
    set_marker_value(lines, "- Implementation approval token:", "")
    set_marker_value(lines, "- User approval status:", "no")
    set_marker_value(lines, "- User approval evidence:", "pending")
    set_marker_value(lines, "- confirm_before_changes:", str(bool(execution_cfg.get("confirm_before_changes", True))).lower())
    set_marker_value(lines, "- assumption_policy:", str(execution_cfg.get("assumption_policy", "ask_first")))
    set_marker_value(lines, "- process_enforcement_mode:", str(switch_cfg.get("mode", "strict")))
    set_marker_value(lines, "- Failure observed:", "none")
    set_marker_value(lines, "- Corrective change made:", "n/a")
    set_marker_value(lines, "- Validation checks run:", "")
    set_marker_block(lines, "- Validation checks run:", ["- PENDING | no checks run yet"])
    set_marker_value(lines, "- Feedback received:", "pending")
    set_marker_value(lines, "- Feedback applied:", "pending")

    write_lines(session_path, lines)
    print(f"PASS: created session {session_path.as_posix()}")
    return 0


def command_run(args: argparse.Namespace) -> int:
    repo_root = discover_repo_root(Path(args.root).resolve() if args.root else None)
    policy = load_policy(repo_root=repo_root)
    try:
        session_path = resolve_session_path(repo_root, policy, args.session, args.latest)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    if not session_path.exists():
        print(f"FAIL: session file not found: {session_path.as_posix()}")
        return 1

    lines = read_lines(session_path)
    missing = ensure_markers(lines, ["- Workflow phase:", "- Validation checks run:"])
    if missing:
        print(f"FAIL: session missing required markers in {session_path.as_posix()}")
        for marker in missing:
            print(f"- {marker}")
        return 1

    set_marker_value(lines, "- Workflow phase:", args.phase)

    results: list[str] = []
    if args.phase == "implement":
        token_field, required_token = required_token_config(policy)
        required_token = required_token.strip()
        token_value = get_marker_value(lines, token_field).strip()
        null_tokens = session_null_tokens(policy)
        if not required_token:
            reason = (
                "policy required implementation token is blank; "
                "set process_guard.execution_phase_rules.required_implementation_approval_token"
            )
            results.append(f"- FAIL | approval_token_check | {reason}")
            set_marker_block(lines, "- Validation checks run:", results)
            write_lines(session_path, lines)
            print(f"FAIL: implementation approval token check failed for {session_path.as_posix()}")
            print(f"- {reason}")
            return 1
        if not token_value or token_value.lower() in null_tokens:
            reason = (
                f"marker '{token_field}' is missing or blank; "
                f"expected exact token '{required_token}'"
            )
            results.append(f"- FAIL | approval_token_check | {reason}")
            set_marker_block(lines, "- Validation checks run:", results)
            write_lines(session_path, lines)
            print(f"FAIL: implementation approval token check failed for {session_path.as_posix()}")
            print(f"- {reason}")
            return 1
        if token_value != required_token:
            reason = (
                f"expected token '{required_token}' in marker '{token_field}', "
                f"found '{token_value or '<empty>'}'"
            )
            results.append(f"- FAIL | approval_token_check | {reason}")
            set_marker_block(lines, "- Validation checks run:", results)
            write_lines(session_path, lines)
            print(f"FAIL: implementation approval token check failed for {session_path.as_posix()}")
            print(f"- {reason}")
            return 1
        results.append("- PASS | approval_token_check")

    failed = False
    for spec in suite_for_phase(args.phase):
        rc, out, err = run_command_capture(spec.args, repo_root)
        if rc == 0:
            results.append(f"- PASS | {spec.display}")
        else:
            failed = True
            results.append(f"- FAIL | {spec.display} | {short_reason(err, out, rc)}")

    set_marker_block(lines, "- Validation checks run:", results)
    write_lines(session_path, lines)

    if failed:
        print(f"FAIL: harness run failed for phase={args.phase}")
        for line in results:
            print(line)
        return 1

    print(f"PASS: harness run passed for phase={args.phase}")
    for line in results:
        print(line)
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    repo_root = discover_repo_root(Path(args.root).resolve() if args.root else None)
    policy = load_policy(repo_root=repo_root)
    try:
        session_path = resolve_session_path(repo_root, policy, args.session, args.latest)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    if not session_path.exists():
        print(f"FAIL: session file not found: {session_path.as_posix()}")
        return 1

    lines = read_lines(session_path)
    missing = ensure_markers(lines, ["- Feedback received:", "- Feedback applied:"])
    if missing:
        print(f"FAIL: session missing required feedback markers in {session_path.as_posix()}")
        for marker in missing:
            print(f"- {marker}")
        return 1

    set_marker_value(lines, "- Feedback received:", f"harness_finalize_result={args.result}")
    applied = args.note.strip() if args.note.strip() else "none"
    set_marker_value(lines, "- Feedback applied:", applied)
    write_lines(session_path, lines)
    print(f"PASS: finalized session {session_path.as_posix()} result={args.result}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execution Harness v1")
    parser.add_argument(
        "--root",
        default=None,
        help="Optional repository root. Defaults to auto-discovery from current directory.",
    )
    subparsers = parser.add_subparsers(dest="command")

    start = subparsers.add_parser("start", help="Create a new session file from template.")
    start.add_argument("--phase", choices=["think", "implement"], required=True)
    start.add_argument("--task", required=True)
    start.add_argument("--scope", choices=["project", "toolkit", "both"], default=DEFAULT_SCOPE)

    run = subparsers.add_parser("run", help="Run governance checks for a phase.")
    run.add_argument("--phase", choices=["think", "implement"], required=True)
    run_group = run.add_mutually_exclusive_group()
    run_group.add_argument("--session", default=None, help="Path to a specific session file.")
    run_group.add_argument("--latest", action="store_true", help="Use latest session file.")

    finalize = subparsers.add_parser("finalize", help="Finalize a session with summary.")
    fin_group = finalize.add_mutually_exclusive_group()
    fin_group.add_argument("--session", default=None, help="Path to a specific session file.")
    fin_group.add_argument("--latest", action="store_true", help="Use latest session file.")
    finalize.add_argument("--result", choices=["pass", "fail"], default="pass")
    finalize.add_argument("--note", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "start":
        return command_start(args)
    if args.command == "run":
        return command_run(args)
    if args.command == "finalize":
        return command_finalize(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
