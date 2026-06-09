# Flu Shot Summary Table Selection

date: 2026-06-09
status: completed

## Context

The parser collected rows from every legacy `cellpadding=3` table but validated
only the first collected rows. If another matching table appeared before the CDC
flu summary table, parsing failed even when the expected summary table was still
present later in the document.

## Completed Scope

- Grouped parsed rows by matching table.
- Selected the first table whose headers match the expected CDC flu summary
  shape.
- Added fixture coverage for an unrelated `cellpadding=3` table before the real
  summary table.
- Extended the static baseline and docs to preserve table-selection behavior.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `make check`
- `git diff --check`
