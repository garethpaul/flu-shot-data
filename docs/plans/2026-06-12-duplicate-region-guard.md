---
title: Duplicate Flu Region Guard
date: 2026-06-12
status: completed
execution: code
---

## Context

The parser skips repeated header rows and blank region rows, but it emits every
remaining region row without checking uniqueness. If upstream markup repeats a
region or changes only its letter case, the generated CSV and JSON contain
multiple records for the same week and region with no indication that the
source table was ambiguous.

## Goals

- Require each parsed region label to be unique within the selected weekly
  summary table.
- Compare normalized region labels case-insensitively while preserving the
  original display value in valid output.
- Fail before output files are written when a duplicate is found.
- Preserve optional subheadings, repeated-header skipping, and partial fixture
  tables used by offline tests.

## Implementation

- Track `region.casefold()` values while building records in `parse_records`.
- Raise a clear `ValueError` before appending a duplicate region record.
- Add fixture-derived tests for exact and case-varied duplicates and retain the
  existing valid-output assertions.
- Extend `scripts/check-baseline.sh`, README, VISION, SECURITY, and CHANGES to
  preserve the duplicate-region integrity boundary.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `python3 -m py_compile flushot.py tests/test_flushot.py`
- `sh -n scripts/check-baseline.sh`
- `make lint`
- `make test`
- `make build`
- `make check`
- `git diff --check`
- GitHub Actions on Python 3.10, 3.12, and 3.14

## Work Completed

- Added case-insensitive region-key tracking while preserving each valid
  region's original display value.
- Rejected a duplicate before appending its record or writing output files.
- Added exact and case-varied duplicate coverage while retaining the existing
  partial-fixture and repeated-header behavior.

## Verification Completed

- All 22 offline tests, all four Make gates, Python compilation, shell syntax,
  and `git diff --check` passed locally.
- Pull-request run `27392428650` passed the Python 3.10, 3.12, and 3.14 matrix
  at implementation commit `5a8853935bf285c38df26afc10392d83905704a6`.
- Post-merge push run `27392439231` and CodeQL run `27402320646` passed at
  default-branch merge commit `3b35641376524125ff11d3fa4366cf8a8b1ddc3d`.
- The workflow intentionally limits push execution to `master`, so the
  implementation feature head has a pull-request run but no push run.
