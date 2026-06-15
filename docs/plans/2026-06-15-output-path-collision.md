---
title: Output Path Collision Guard
type: reliability
status: completed
date: 2026-06-15
execution: code
---

# Output Path Collision Guard

## Problem Frame

`write_outputs()` writes CSV first and JSON second without proving that the two
destinations are distinct. If callers provide the same path, a symlink alias,
or two existing names for the same file, the JSON write silently replaces the
CSV output. The writer must reject colliding destinations before opening or
truncating either output.

## Prioritized Engineering Work

1. **P0 - Output integrity:** fail before writes when CSV and JSON destinations
   identify the same filesystem target.
2. **P1 - Regression coverage:** prove direct equality, resolved symlink
   aliases, and existing same-file aliases preserve pre-existing bytes.
3. **P2 - Maintained contract:** enforce validation ordering, regression
   coverage, synchronized guidance, and completed verification evidence.

This change implements P0 through P2 without changing CDC fetching, parsing,
record schemas, output serialization, or successful distinct-path behavior.

## Requirements

- Distinct CSV and JSON destinations must retain current output behavior.
- Lexically identical paths must fail before either destination is opened.
- Resolved symlink aliases and existing same-file aliases must fail before
  either destination is opened or truncated.
- Collision errors must use a deterministic message without exposing record
  content.
- Static contracts must reject validation removal, post-write validation,
  regression loss, guidance drift, and incomplete plan evidence.

## Implementation Units

### Validate Output Destination Identity

Files:

- `flushot.py`
- `tests/test_flushot.py`

Approach:

- Add a focused destination validator that normalizes path inputs and rejects
  resolved-path equality.
- When both destinations already exist, also reject operating-system same-file
  identity so hard-link aliases cannot be used as separate outputs.
- Invoke validation before materializing records or opening either output.
- Add test-first regressions for direct equality, symlink aliases, hard-link
  aliases, unchanged sentinel bytes, and successful distinct outputs.

### Enforce The Contract

Files:

- `scripts/check-baseline.sh`
- `docs/plans/2026-06-15-output-path-collision.md`

Approach:

- Require the validator, its pre-write ordering, focused regressions, and
  truthful completed evidence.
- Add mutation-sensitive checks for resolved and same-file identity handling.

### Synchronize Guidance

Files:

- `AGENTS.md`
- `CHANGES.md`
- `README.md`
- `SECURITY.md`
- `VISION.md`

## Verification

- Focused output destination regressions.
- Repository and external-directory `make check` on the maintained Python
  runtime.
- Hostile mutations for validator invocation, validation ordering, resolved
  aliases, same-file aliases, regression coverage, guidance, and plan status.
- Exact diff, generated artifact, conflict marker, and changed-line secret
  audits.

## Risks

- Existing callers that intentionally point both formats at one filesystem
  object will now receive an error instead of silently retaining only JSON.
- Filesystem identity can change after validation; this guard prevents known
  collisions at call time but does not introduce directory locking or a
  multi-file transactional publication protocol.

## Work Completed

- Added pre-write destination identity validation using resolved path equality
  and operating-system same-file checks for existing aliases.
- Kept validation ahead of record materialization and both output file opens.
- Added direct-path, symlink-alias, and hard-link-alias regressions proving
  pre-existing bytes remain unchanged after rejection.
- Added ordering-sensitive source, regression, guidance, and completed-plan
  contracts to the offline baseline.

## Verification Completed

- The test-first focused run failed all three collision regressions on the
  previous writer; all 44 offline tests passed after implementation.
- The repository and external-directory `make check` gates passed with
  bytecode generation disabled.
- A completed-plan disposable baseline copy passed before the real plan status
  changed, avoiding circular evidence.
- Seven isolated hostile mutations were rejected for validator invocation,
  validation ordering, resolved aliases, same-file aliases, regression
  coverage, guidance, and plan completion evidence.
- In-memory Python compilation, POSIX shell syntax, exact diff, generated
  artifact, conflict marker, and changed-line secret audits passed.
- No live CDC request was made.

## Status: Completed
