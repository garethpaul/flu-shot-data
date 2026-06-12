# CI Baseline

status: completed

## Context

The repository had a local Python 3 `make check` baseline for fixture-based CDC
parser and fetch validation, but no hosted workflow ran it for pushes and pull
requests.

## Changes

- Added a GitHub Actions workflow that installs Python 3.12 and runs
  `make check`.
- Extended the baseline script and docs so the hosted CI path stays visible.

## Verification

- `make check`
