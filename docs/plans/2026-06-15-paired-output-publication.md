---
title: Paired Output Publication
type: reliability
status: completed
date: 2026-06-15
execution: code
---

# Paired Output Publication

## Problem

`write_outputs` writes the CSV destination before opening and serializing the
JSON destination. A JSON serialization or write failure therefore destroys the
previous CSV and may truncate the previous JSON, leaving two outputs from
different generations. The current regression reproduces this by injecting a
`json.dump` failure: neither sentinel survives.

## Approach

- Render and flush each complete output into an invocation-owned temporary
  file in the destination's parent directory before changing either target.
- Publish the staged files with same-filesystem replacements while retaining
  invocation-owned backups of any prior destinations.
- If staging or either publication step fails, restore both prior destinations
  or remove newly created targets, then re-raise the original failure. Track
  each destination's state independently so rollback touches only paths whose
  backup or publication step this invocation completed.
- Clean all invocation-owned staged and backup paths on success and failure.
- Preserve valid CSV/JSON formatting, path and record preflight behavior,
  source fetching, parsing, CLI output, and existing stable validation errors.

## Files

- `flushot.py`
- `tests/test_flushot.py`
- `scripts/check-baseline.sh`
- `README.md`
- `SECURITY.md`
- `VISION.md`
- `CHANGES.md`
- `AGENTS.md`
- `docs/plans/2026-06-15-paired-output-publication.md`

## Implementation Units

1. Separate complete CSV and JSON staging from destination publication.
2. Add rollback-capable paired publication with invocation-owned backup and
   cleanup state.
3. Add fault-injection regressions for staging failure, second-publication
   failure with existing outputs, backup-step failure, second-publication
   failure with absent outputs, valid output parity, and temporary artifact
   cleanup.
4. Add portable implementation, regression, guidance, and completed-plan
   contracts.

## Verification

- Reproduce the current paired-output corruption before implementation.
- Run focused publication regressions and the full repository-root and
  external-directory `make check` gate.
- Reject isolated staging, rollback, absent-output cleanup, valid-parity,
  artifact-cleanup, guidance, and completed-plan mutations.
- Audit shell syntax, Python compilation, exact diff, generated artifacts,
  dependency/workflow drift, file modes, conflict markers, whitespace, and
  credential-shaped additions.

## Scope Boundaries

- This change guarantees rollback for handled Python exceptions during staging
  and publication; it does not claim multi-path crash or power-loss atomicity.
- Do not add dependencies, create missing output directories, change valid
  output bytes, or alter CDC network and parsing behavior.
- Do not merge or close stacked pull requests without explicit authorization.

## Success Criteria

- A failure before both publications complete leaves both destinations at
  their prior bytes or both absent when they were initially absent.
- Successful writes retain the documented CSV schema and matching JSON rows.
- No invocation-owned stage or backup files remain after success or failure.
- The completed plan records actual local, mutation, audit, and hosted evidence.

## Work Completed

- Stage complete CSV and JSON files in their respective destination
  directories, flush and sync them, and publish only after both stages succeed.
- Move existing destinations to invocation-owned backups before replacement and
  restore each prior destination in reverse order when backup or publication
  raises.
- Remove newly published paths when no prior output existed and remove every
  invocation-owned stage or backup after success and handled failure.
- Attempt rollback for both destinations when one restoration fails, retain
  unresolved recovery backups, and surface a stable incomplete-rollback error.
- Preserve default and existing output modes plus distinct symlink destination
  behavior while publishing through resolved destination directories.
- Add fault-injection coverage for JSON staging, second backup, and second
  publication failures with both existing and initially absent outputs.

## Verification Completed

- The pre-fix fault injection proved a JSON serialization failure replaced the
  CSV sentinel and truncated the JSON sentinel; both are preserved now.
- Python 3.12 repository-root and external-directory `make check` passed all 59 offline tests,
  source contracts, and in-memory syntax compilation.
- Twelve focused isolated hostile mutations were rejected across staging, rollback,
  initially absent outputs, valid output parity, artifact cleanup, guidance,
  and completed-plan evidence.
- Exact diff, generated-artifact, dependency/workflow-drift, mode,
  conflict-marker, whitespace, and credential-shaped-addition audits passed.
- No live CDC request was made.
- This handled-exception rollback does not claim multi-path crash or power-loss atomicity.
