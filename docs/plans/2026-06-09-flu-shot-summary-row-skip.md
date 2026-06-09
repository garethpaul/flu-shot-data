---
title: Flu Shot Summary Row Skip
date: 2026-06-09
status: completed
execution: code
---

## Context

The parser now selects the CDC summary table by expected headers and no longer
requires an extra subheading row. Within a selected table, repeated header rows
or blank-region rows should not be emitted as region records.

## Goals

- Skip repeated summary header rows after the first header.
- Skip rows that do not contain a region value.
- Preserve percent normalization and output schema behavior.
- Extend fixture-based coverage for these row-level parser cases.

## Implementation

- Added row-level checks in `parse_records` before building each output record.
- Added a fixture test with a repeated header row and a blank-region row.
- Updated README, VISION, CHANGES, and the static baseline.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `scripts/check-baseline.sh`
- `make check`
- `git diff --check`
