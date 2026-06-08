# Changes

## 2026-06-08

- Ported the CDC flu summary scraper from Python 2-era dependencies to Python 3
  standard-library code.
- Added fixture-based tests for parser and output schema behavior.
- Added `make check` and `scripts/check-baseline.sh` for repeatable offline
  verification.
- Ignored generated CSV/JSON outputs and Python cache artifacts.
