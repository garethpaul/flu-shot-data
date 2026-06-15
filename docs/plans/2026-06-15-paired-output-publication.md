---
title: Paired Output Publication
type: reliability
status: planned
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
