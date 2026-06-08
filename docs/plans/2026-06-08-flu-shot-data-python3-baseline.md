# Flu Shot Data Python 3 Baseline

date: 2026-06-08
status: completed

## Context

Flu Shot Data was a Python 2-era live scraper for the CDC weekly flu summary
page. It depended on unmaintained libraries, wrote generated outputs directly,
and had no fixture coverage for the fragile HTML parser.

## Completed Scope

- Ported the scraper to Python 3 using only standard-library modules.
- Switched the CDC source URL to HTTPS.
- Split fetching, parsing, and output writing into separate functions.
- Added fixture-based unit tests for week metadata parsing, table parsing, CSV
  output, and JSON output.
- Added `scripts/check-baseline.sh` and `make check` for repeatable offline
  verification.
- Ignored generated `flu.csv`, `flu.json`, and Python cache artifacts.

## Verification

- `make check`

## Follow-Ups

- Validate the parser against the live CDC page before publishing any generated
  data as current.
- Add provenance metadata if generated data outputs are intentionally committed.
- Consider packaging only if this becomes more than a preserved scraper.
