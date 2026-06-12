# CI Baseline

status: completed

## Context

The repository had a local Python 3 `make check` baseline for fixture-based CDC
parser and fetch validation, but no hosted workflow ran it for pushes and pull
requests.

## Changes

- Added a least-privilege GitHub Actions workflow for pushes, pull requests,
  and manual runs.
- Pinned checkout and Python setup actions by commit, disabled persisted
  checkout credentials, and bounded superseded runs with concurrency
  cancellation and a timeout.
- Ran the offline fixture-based `make check` baseline on Python 3.10, 3.12,
  and 3.14 without contacting CDC endpoints.
- Added focused policy checks for unrestricted pull requests, the master push
  trigger, matrix values, immutable actions, and the exact verification step.

## Verification

- `make check`
- `git diff --check`
- Hosted Python 3.10, 3.12, and 3.14 GitHub Actions jobs
