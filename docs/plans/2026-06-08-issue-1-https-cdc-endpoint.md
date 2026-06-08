# Issue 1 HTTPS CDC Endpoint

## Issue

`garethpaul/flu-shot-data#1` reports that `flushot.py` opens
`http://www.cdc.gov/flu/weekly/` at runtime.

## Plan

- Move the CDC weekly flu summary URL to HTTPS in the scraper docstring and
  runtime browser request.
- Preserve the existing mechanize scraping, parsing, CSV, and JSON output flow.
- Add a source-level baseline script because this workspace does not provide a
  Python 2 runtime for the legacy scraper.

## Verification

- `scripts/check-baseline.sh`
- `rg -n "http://www\\.cdc\\.gov/flu/weekly|https://www\\.cdc\\.gov/flu/weekly" flushot.py scripts/check-baseline.sh`
- `git diff --check`
- `curl -I -L --max-time 15 https://www.cdc.gov/flu/weekly/`
