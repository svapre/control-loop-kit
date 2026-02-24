# Control Loop Kit

Reusable process-control toolkit for AI-assisted software projects.

## What this repository provides
- `control_loop.control_gate`: readiness and CI gate checks.
- `control_loop.process_guard`: process-governance checks for proposal/design coupling.

## Intended usage
1. Add this repository to a project as a submodule or package dependency.
2. Expose local wrapper scripts that call the toolkit modules.
3. Run project-specific checks through your CI pipeline.

## Versioning
Use tagged releases and pin versions per project. Upgrade via explicit version bump PRs.

