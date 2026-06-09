# Flu Shot Percent Normalization

date: 2026-06-09
status: completed

## Context

The CDC summary table can render percent-positive cells with spacing before the
percent sign. The parser removed `%` with `rstrip("%")`, which left a trailing
space in values like `12.5 %`.

## Completed Scope

- Added a parser unit test for percent-positive cells with spaced percent signs.
- Added a `normalize_percent` helper for percent-positive values.
- Updated the static baseline to require the helper and fixture coverage.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `make check`
- `git diff --check`
