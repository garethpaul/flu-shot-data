# Flu Week Metadata Validation

status: completed

## Context

The parser required week metadata text but accepted impossible values such as
week 99 or February 31, allowing mislabeled public-health records.

## Work Completed

- Required influenza season weeks in the range 1 through 53.
- Parsed week-ending labels with `datetime.strptime` to reject invalid dates.
- Added fixture-derived tests for both corruption modes.
- Extended the offline baseline and data-integrity documentation.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `make check`
- `make lint`
- `make test`
- `make build`
- `git diff --check`
