# Changes

## 2026-06-09

- Added fetch URL validation so live requests require HTTPS URLs with hosts,
  plus `make lint`/`make test`/`make build` baseline aliases.
- Selected the first table with the expected CDC summary headers when unrelated
  `cellpadding=3` tables appear before the flu summary.
- Skipped repeated summary headers and blank-region rows inside the selected
  summary table.

## 2026-06-08

- Made the optional CDC summary subheading row non-required so the first region
  row is preserved when the subheading is absent.
- Ported the CDC flu summary scraper from Python 2-era dependencies to Python 3
  standard-library code.
- Added fixture-based tests for parser and output schema behavior.
- Added `make check` and `scripts/check-baseline.sh` for repeatable offline
  verification.
- Ignored generated CSV/JSON outputs and Python cache artifacts.
- Normalized percent-positive values with spaced percent signs in CDC table
  cells.
- Added a CDC summary header guard so parser mismatches fail before data rows
  are emitted.
