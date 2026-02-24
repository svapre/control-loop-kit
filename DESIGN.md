# Design Guardrails

## Purpose
This file defines the design parameters used to evaluate ideas and implementation changes for the PDF accessibility project.

## Project Design Parameters
1. Structural correctness first:
   - Output PDF must remain valid and readable after bookmark/link changes.
   - Accessibility improvements must not corrupt existing document content.

2. Deterministic behavior:
   - Same input PDF and same config must produce the same output.

3. Traceable decisions:
   - Created bookmarks/links must be explainable from recorded evidence (logs, mappings, or proposal rationale).

4. No silent guessing:
   - Ambiguous references should go to manual review or explicit skip with reason.
   - Do not create links based on low-confidence guesses without documentation.

5. Configuration over hardcoding:
   - Thresholds, matching rules, and environment-specific settings must come from config files.

6. Idempotent processing:
   - Re-running the same job should not duplicate links/bookmarks or progressively degrade output quality.

7. Fail loudly on invalid state:
   - Invalid references, impossible page targets, and schema mismatches must raise clear errors or explicit warnings.

8. Performance budget awareness:
   - Changes should state expected runtime/memory impact for representative document sizes.

9. Extensible module boundaries:
   - Parsing, indexing, matching, and annotation should remain separable to reduce coupling.

10. Evidence-backed claims:
    - Architecture/process claims must reference tests, CI, logs, or measurable checks.

11. Generality over one-off fixes:
    - Changes should work for document classes, not only one known PDF.
    - If a change is intentionally single-document or temporary, it must be declared, reviewed, and time-bounded.

## Exception Rule
A solution that violates one or more design parameters is allowed only if all are true:
1. The violation is explicitly listed.
2. Why alternatives are worse is documented.
3. Risk, mitigation, and rollback are documented.
4. The proposal scorecard still shows best overall outcome for current constraints.

## Brainstorming Protocol
Every solution discussion must include:
1. Parameters satisfied
2. Parameters violated (if any)
3. Why violation is necessary (if any)
4. Risk and mitigation
5. Rollback plan

