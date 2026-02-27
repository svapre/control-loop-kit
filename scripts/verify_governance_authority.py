"""Verify machine-checkable human authority for governance-file changes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_loop.policy import load_policy  # noqa: E402


NEXT_LINK_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


def _normalize_login(login: str) -> str:
    return login.strip().lower()


def _get_marker_value(text: str, marker: str) -> str:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(marker):
            return line[len(marker) :].strip()
    return ""


def _next_link(link_header: str) -> str | None:
    if not link_header:
        return None
    match = NEXT_LINK_RE.search(link_header)
    if match:
        return match.group(1)
    return None


def _api_get_json(url: str, token: str) -> tuple[Any, str]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "control-loop-kit-governance-authority-check",
        },
    )
    with urlopen(request) as response:
        body = response.read().decode("utf-8")
        data = json.loads(body)
        return data, response.headers.get("Link", "")


def _api_get_paginated(url: str, token: str) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    next_url: str | None = url
    while next_url:
        data, link_header = _api_get_json(next_url, token)
        if not isinstance(data, list):
            raise ValueError(f"Expected list response from GitHub API for: {next_url}")
        for item in data:
            if isinstance(item, dict):
                collected.append(item)
        next_url = _next_link(link_header)
    return collected


def _latest_reviews_by_user(reviews: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    def _sort_key(item: dict[str, Any]) -> tuple[str, int]:
        submitted_at = str(item.get("submitted_at", ""))
        review_id_raw = item.get("id", 0)
        review_id = int(review_id_raw) if isinstance(review_id_raw, int) else 0
        return (submitted_at, review_id)

    latest: dict[str, dict[str, Any]] = {}
    for review in sorted(reviews, key=_sort_key):
        user = review.get("user", {})
        if not isinstance(user, dict):
            continue
        login_raw = user.get("login")
        if not isinstance(login_raw, str) or not login_raw.strip():
            continue
        latest[_normalize_login(login_raw)] = review
    return latest


def evaluate_governance_authority(
    changed_files: set[str],
    reviews: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    head_sha: str,
    pr_author: str,
    pr_body: str,
    repo_owner: str,
) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    governance_files = {
        item for item in config.get("governance_files", []) if isinstance(item, str) and item.strip()
    }
    changed_governance = sorted(path for path in changed_files if path in governance_files)
    if not changed_governance:
        return failures, warnings

    min_approvals_raw = config.get("minimum_approvals", 1)
    min_approvals = min_approvals_raw if isinstance(min_approvals_raw, int) else 1
    if min_approvals < 1:
        min_approvals = 1

    require_latest = bool(config.get("require_approval_on_latest_commit", True))
    require_human = bool(config.get("require_human_reviewers", True))
    allow_authority_bypass = bool(config.get("allow_pr_authority_bypass", False))
    bypass_field = str(config.get("pr_authority_bypass_field", "- Governance authority sign-off:"))
    bypass_token = str(config.get("pr_authority_bypass_token", "OWNER_APPROVED"))

    required_approvers = {
        _normalize_login(item)
        for item in config.get("required_approvers", [])
        if isinstance(item, str) and item.strip()
    }
    if not required_approvers:
        owner = _normalize_login(repo_owner)
        if owner:
            required_approvers = {owner}
            warnings.append(
                "governance_human_authority_rule.required_approvers is empty; "
                f"falling back to repository owner '{owner}'."
            )
        else:
            failures.append(
                "Governance files changed but no required approvers configured and repository owner is unknown."
            )
            return failures, warnings

    latest_reviews = _latest_reviews_by_user(reviews)
    qualifying_approvals: set[str] = set()

    for approver in sorted(required_approvers):
        review = latest_reviews.get(approver)
        if not review:
            continue
        if str(review.get("state", "")).upper() != "APPROVED":
            continue

        user = review.get("user", {})
        if require_human and isinstance(user, dict):
            if str(user.get("type", "")).lower() == "bot":
                continue

        if require_latest and head_sha:
            if str(review.get("commit_id", "")) != head_sha:
                continue

        qualifying_approvals.add(approver)

    if len(qualifying_approvals) >= min_approvals:
        return failures, warnings

    normalized_author = _normalize_login(pr_author)
    if allow_authority_bypass and normalized_author in required_approvers:
        bypass_value = _get_marker_value(pr_body or "", bypass_field).strip()
        if bypass_value == bypass_token:
            warnings.append(
                "No qualifying reviewer approval found. "
                f"Accepted authority self-signoff via PR body marker '{bypass_field} {bypass_token}'."
            )
            return failures, warnings

    failures.append(
        "Governance files changed without required human authority approval. "
        f"Changed governance files: {', '.join(changed_governance)}. "
        f"Required approvers: {', '.join(sorted(required_approvers))}. "
        f"Qualifying approvals found: {len(qualifying_approvals)}/{min_approvals}."
    )
    if allow_authority_bypass and normalized_author in required_approvers:
        failures.append(
            "Authority self-bypass is enabled, but PR body does not contain required marker: "
            f"'{bypass_field} {bypass_token}'."
        )
    return failures, warnings


def _governance_authority_config(policy: dict[str, Any]) -> dict[str, Any]:
    cfg = policy.get("governance_human_authority_rule", {})
    return cfg if isinstance(cfg, dict) else {}


def _governance_files_from_policy(policy: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    files = cfg.get("governance_files")
    if isinstance(files, list) and files:
        return [item for item in files if isinstance(item, str)]
    amendment = policy.get("governance_amendment_rule", {})
    if isinstance(amendment, dict):
        fallback = amendment.get("governance_files", [])
        if isinstance(fallback, list):
            return [item for item in fallback if isinstance(item, str)]
    return []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _bool_from(cfg: dict[str, Any], key: str, default: bool) -> bool:
    value = cfg.get(key, default)
    return value if isinstance(value, bool) else default


def _int_from(cfg: dict[str, Any], key: str, default: int) -> int:
    value = cfg.get(key, default)
    if isinstance(value, int):
        return value
    return default


def _load_policy_json_from_git_ref(ref: str, path: str = ".control-loop/policy.json") -> tuple[dict[str, Any], str | None]:
    if not ref.strip():
        return {}, "No base ref available for policy comparison."

    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        return {}, f"Unable to load base policy from {ref}:{path}: {detail}"

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"Invalid JSON in base policy at {ref}:{path}: {exc}"

    if not isinstance(data, dict):
        return {}, f"Base policy at {ref}:{path} is not a JSON object."
    return data, None


def _merge_authority_config(current_cfg: dict[str, Any], base_cfg: dict[str, Any]) -> dict[str, Any]:
    base_present = bool(base_cfg)
    merged: dict[str, Any] = {}

    current_enabled = _bool_from(current_cfg, "enabled", False)
    base_enabled = _bool_from(base_cfg, "enabled", False)
    merged["enabled"] = current_enabled or base_enabled

    if base_present:
        merged["minimum_approvals"] = max(
            1,
            _int_from(current_cfg, "minimum_approvals", 1),
            _int_from(base_cfg, "minimum_approvals", 1),
        )
        merged["require_approval_on_latest_commit"] = _bool_from(
            current_cfg, "require_approval_on_latest_commit", True
        ) or _bool_from(base_cfg, "require_approval_on_latest_commit", True)
        merged["require_human_reviewers"] = _bool_from(
            current_cfg, "require_human_reviewers", True
        ) or _bool_from(base_cfg, "require_human_reviewers", True)
        merged["allow_pr_authority_bypass"] = _bool_from(
            current_cfg, "allow_pr_authority_bypass", False
        ) and _bool_from(base_cfg, "allow_pr_authority_bypass", False)

        approvers = set(_string_list(current_cfg.get("required_approvers")))
        approvers.update(_string_list(base_cfg.get("required_approvers")))
        merged["required_approvers"] = sorted(approvers)
    else:
        merged["minimum_approvals"] = max(1, _int_from(current_cfg, "minimum_approvals", 1))
        merged["require_approval_on_latest_commit"] = _bool_from(
            current_cfg, "require_approval_on_latest_commit", True
        )
        merged["require_human_reviewers"] = _bool_from(current_cfg, "require_human_reviewers", True)
        merged["allow_pr_authority_bypass"] = _bool_from(current_cfg, "allow_pr_authority_bypass", False)
        merged["required_approvers"] = _string_list(current_cfg.get("required_approvers"))

    merged["pr_authority_bypass_field"] = str(
        current_cfg.get(
            "pr_authority_bypass_field",
            base_cfg.get("pr_authority_bypass_field", "- Governance authority sign-off:"),
        )
    )
    merged["pr_authority_bypass_token"] = str(
        current_cfg.get(
            "pr_authority_bypass_token",
            base_cfg.get("pr_authority_bypass_token", "OWNER_APPROVED"),
        )
    )
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify governance human authority for constitutional changes.")
    parser.add_argument("--check", action="store_true", help="Run verification checks")
    parser.add_argument("--policy", default=None, help="Path to policy JSON override")
    args = parser.parse_args()

    if not args.check:
        parser.print_help()
        return 0

    try:
        policy = load_policy(args.policy)
    except Exception as exc:
        print(f"FAIL: policy load/validation error: {exc}")
        return 1

    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    if event_name not in {"pull_request", "pull_request_target"}:
        print("PASS: governance authority check skipped (non-PR event).")
        return 0

    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path or not Path(event_path).is_file():
        print("FAIL: missing GITHUB_EVENT_PATH for pull_request event.")
        return 1

    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pull_request = event.get("pull_request", {})
    if not isinstance(pull_request, dict):
        print("FAIL: event payload missing pull_request object.")
        return 1

    pr_number = pull_request.get("number")
    if not isinstance(pr_number, int):
        print("FAIL: pull_request.number missing from event payload.")
        return 1

    current_cfg = _governance_authority_config(policy)
    base_sha = ""
    base_obj = pull_request.get("base", {})
    if isinstance(base_obj, dict):
        base_sha = str(base_obj.get("sha", "") or "")

    base_policy: dict[str, Any] = {}
    if base_sha:
        loaded_base, base_warning = _load_policy_json_from_git_ref(base_sha)
        if base_warning:
            print(f"WARN: {base_warning}")
        else:
            base_policy = loaded_base

    base_cfg = _governance_authority_config(base_policy)
    cfg = _merge_authority_config(current_cfg, base_cfg)
    current_governance_files = _governance_files_from_policy(policy, current_cfg)
    base_governance_files = _governance_files_from_policy(base_policy, base_cfg)
    cfg["governance_files"] = sorted(set(current_governance_files) | set(base_governance_files))

    if not cfg.get("enabled", False):
        print("PASS: governance human authority rule disabled.")
        return 0

    repo = os.getenv("GITHUB_REPOSITORY", "")
    if not repo:
        repo_obj = event.get("repository", {})
        if isinstance(repo_obj, dict):
            owner_obj = repo_obj.get("owner", {})
            name = repo_obj.get("name")
            if isinstance(owner_obj, dict) and isinstance(owner_obj.get("login"), str) and isinstance(name, str):
                repo = f"{owner_obj['login']}/{name}"
    if "/" not in repo:
        print("FAIL: could not resolve GITHUB_REPOSITORY.")
        return 1
    repo_owner = repo.split("/", 1)[0]

    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        print("FAIL: missing GITHUB_TOKEN (or GH_TOKEN) for GitHub API verification.")
        return 1

    api_base = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    files_url = f"{api_base}/repos/{repo}/pulls/{pr_number}/files?per_page=100"
    reviews_url = f"{api_base}/repos/{repo}/pulls/{pr_number}/reviews?per_page=100"

    try:
        files = _api_get_paginated(files_url, token)
        reviews = _api_get_paginated(reviews_url, token)
    except HTTPError as exc:
        print(f"FAIL: GitHub API HTTP error {exc.code} while verifying governance approval: {exc.reason}")
        return 1
    except URLError as exc:
        print(f"FAIL: GitHub API connection error while verifying governance approval: {exc.reason}")
        return 1
    except Exception as exc:
        print(f"FAIL: governance approval API verification error: {exc}")
        return 1

    changed_files: set[str] = set()
    for item in files:
        name = item.get("filename")
        if isinstance(name, str):
            changed_files.add(name)

    head = pull_request.get("head", {})
    author = pull_request.get("user", {})
    head_sha = head.get("sha") if isinstance(head, dict) else ""
    pr_author = author.get("login") if isinstance(author, dict) else ""
    pr_body = pull_request.get("body", "")

    failures, warnings = evaluate_governance_authority(
        changed_files,
        reviews,
        cfg,
        head_sha=str(head_sha or ""),
        pr_author=str(pr_author or ""),
        pr_body=str(pr_body or ""),
        repo_owner=repo_owner,
    )

    for warning in warnings:
        print(f"WARN: {warning}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: governance human authority verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
