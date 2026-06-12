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
