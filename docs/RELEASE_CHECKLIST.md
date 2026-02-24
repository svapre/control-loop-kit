# Release Checklist

Use this checklist for every toolkit release.

## 1) Pre-Release Validation
- Confirm working tree is clean.
- Run:
  - `python scripts/generate_model_catalog_prompt.py --check`
  - `python scripts/validate_backlog.py --check`
  - `python scripts/render_dashboard.py --check`
  - `python scripts/validate_onboarding_docs.py --check`
  - `python scripts/validate_release_hygiene.py --check --allow-unreleased-latest`
  - `python -m ruff check .`
  - `python -m pytest -q`

## 2) Version + Changelog
- Update `pyproject.toml` version.
- Add a `## vX.Y.Z` entry at the top of `CHANGELOG.md`.
- Ensure changelog latest version matches `pyproject.toml`.

## 3) Merge to Master
- Open PR.
- Wait for CI `verify` to pass.
- Merge using repository policy.

## 4) Tag Release
- Create annotated tag on merged `master` commit:
  - `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- Push tag:
  - `git push origin vX.Y.Z`

## 5) Post-Release Verification
- Confirm tag exists remotely:
  - `git ls-remote --tags origin`
- Confirm release hygiene check passes without drift.
