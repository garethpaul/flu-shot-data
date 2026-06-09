# Flu Shot Summary Header Guard

date: 2026-06-09
status: completed

## Context

The scraper finds the CDC summary table by legacy `cellpadding=3` markup and
then skips two header rows before reading regional data. If the CDC page adds
another matching table or changes the header labels, the parser could emit rows
from the wrong table shape.

## Completed Scope

- Added `EXPECTED_TABLE_HEADERS` for the flu summary table.
- Added `has_expected_summary_header()` and a parser failure before data row
  extraction when the matched table headers do not match.
- Added a fixture test for a malformed summary header.
- Extended the static baseline and docs to preserve the header contract.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `make check`
- `git diff --check`
