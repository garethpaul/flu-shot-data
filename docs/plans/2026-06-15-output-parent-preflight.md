---
title: Output Parent Preflight
type: reliability
status: completed
date: 2026-06-15
execution: code
---

# Output Parent Preflight

## Problem

`write_outputs` opens and truncates the CSV before it discovers that the JSON
parent directory is missing or is not a directory. A configuration error in the
second output can therefore destroy a valid first output while reporting
failure.

## Approach

- Validate that both resolved output parent paths exist and are directories
  before either destination is opened.
- Raise a clear `ValueError` for an invalid parent while preserving existing
  destination bytes.
- Add focused regressions and static contracts for missing and non-directory
  parents, guidance, and completed verification evidence.

## Files

- `flushot.py`
- `tests/test_flushot.py`
- `scripts/check-baseline.sh`
- `README.md`
- `SECURITY.md`
- `VISION.md`
- `CHANGES.md`
- `AGENTS.md`
- `docs/plans/2026-06-15-output-parent-preflight.md`

## Verification

- Prove the current implementation truncates the CSV before the JSON open
  fails, then prove the fixed implementation preserves the sentinel.
- Run the full repository and external-directory gates.
- Reject isolated source, regression, guidance, and plan-evidence mutations.
- Audit the exact diff, generated artifacts, and secret patterns.

## Non-Goals

- Do not implement multi-file transactional publication or create directories.
- Do not change parsing, CDC fetching, output schemas, or CLI behavior.
- Do not merge or close stacked pull requests without owner authorization.

## Status: Completed

## Work Completed

- Preflight both resolved output parents before opening either destination.
- Reject missing and non-directory parents with a stable `ValueError` while
  preserving existing CSV and parent-file sentinel bytes.
- Add source, regression, guidance, and completed-plan baseline contracts.

## Verification Completed

- Focused regression failed against the prior implementation and passed after
  the parent preflight was added.
- Python 3.12.8 repository and external-directory `make check` passed all 46 offline tests,
  static contracts, and in-memory syntax compilation.
- Six isolated hostile mutations were rejected for the source guard, both
  regressions, sentinel assertion, guidance, and completed plan evidence.
- Exact diff, generated-artifact, and secret-pattern audits passed.
- No live CDC request was made.
