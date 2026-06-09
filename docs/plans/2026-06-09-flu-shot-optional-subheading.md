# Flu Shot Optional Subheading

date: 2026-06-09
status: completed

## Context

The CDC summary table fixture includes an extra non-data subheading row between
the header row and the first regional data row. The parser skipped the first two
rows unconditionally, which meant the first real region row was dropped if that
optional subheading was absent.

## Completed Scope

- Started row extraction immediately after the header row.
- Kept short non-data rows ignored so the existing subheading fixture still
  parses correctly.
- Added fixture coverage for a summary table without the optional subheading.
- Extended the static baseline and docs to preserve the optional subheading
  behavior.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `make check`
- `git diff --check`
