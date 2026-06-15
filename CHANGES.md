# Changes

## 2026-06-15

- Reject ambiguous duplicate charset parameters in CDC HTML response metadata
  before reading the response body.

## 2026-06-14

- Rejected truncated or overlong CDC response bodies when a validated
  `Content-Length` does not match the final bounded byte count.
- Rejected duplicate, combined, signed, padded, empty, and non-decimal CDC
  `Content-Length` metadata before body reads while preserving streamed limits.
- Replaced recursive bytecode cleanup with in-memory syntax compilation and
  bytecode-disabled tests.
- Required exact HTTP 200 before CDC final-URL, response metadata, or body
  processing.

## 2026-06-13

- Made offline verification independent of the caller's working directory by
  resolving the baseline checker from the loaded Makefile.
- Rejected duplicate CDC response Content-Type fields before body reads.
- Enforced identity-only response content encoding before any live CDC body
  read and rejected compressed, duplicated, combined, blank, or unknown encodings.
- Added accepted identity and no-read rejection coverage plus mutation-sensitive
  static contracts.
- Rejected malformed UTF-8 in bounded live CDC response bodies without leaking
  response content in decode errors.
- Added valid multibyte and malformed response regression coverage plus a
  static strict-decoding contract.
- Required live CDC responses to declare `text/html` with no charset or a
  UTF-8-compatible charset before reading response bytes.
- Added accepted metadata, rejection, and guard-before-read regression tests.

## 2026-06-12

- Rejected exact and case-varied duplicate region rows before generating weekly
  flu CSV or JSON records.
- Added fixture-derived duplicate coverage and a static parser contract.

## 2026-06-10

- Rejected out-of-range influenza week numbers and impossible week-ending
  calendar dates before emitting records.
- Added a pinned, least-privilege GitHub Actions matrix that runs the offline
  baseline on Python 3.10, 3.12, and 3.14.
- Disabled persisted checkout credentials and added focused workflow policy
  checks for triggers, permissions, matrix values, actions, and commands.
- Rejected automatic redirects, revalidated final response URLs, and limited
  live response bodies to 2 MiB.
- Added exact week 1 and 53 acceptance plus week 0 rejection coverage.
- Added repository-wide ownership and corrected contributor guidance for the
  dependency-free parser workflow.
- Extended the baseline script and docs to require the hosted CI verification
  path.

## 2026-06-09

- Bounded live CDC fetch timeout values before opening network requests.
- Rejected query strings and fragments in live CDC fetch URLs before opening
  network requests.
- Rejected embedded credentials in live CDC fetch URLs before opening network
  requests.
- Limited live fetch URLs to `cdc.gov` or CDC subdomains before opening
  network requests.
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
