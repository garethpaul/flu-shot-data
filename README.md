# flu-shot-data

<!-- README-OVERVIEW-IMAGE -->
![Project overview](docs/readme-overview.svg)

## Overview

`garethpaul/flu-shot-data` is a public sample, documentation, or utility project. Flu Shot Data to CSV

This repository contains a small Python 3 scraper for the CDC weekly flu summary
page. It parses the national and regional summary table and writes `flu.csv`
and `flu.json`.

## Repository Contents

- `README.md` - project overview and local usage notes
- `CHANGES.md` - concise history of maintenance changes
- `Makefile` - local verification entry point
- `SECURITY.md` - security reporting and disclosure guidance
- `VISION.md` - project direction and maintenance guardrails
- `flushot.py` - Python 3 scraper, parser, and output writer
- `scripts/check-baseline.sh` - offline syntax, unit, and static baseline checks
- `tests/` - fixture-based tests for parser and output schema behavior

Additional scan context:

- Source directories: tests
- Dependency and build manifests: none detected
- Entry points or build surfaces: flushot.py
- Test-looking files: tests/test_flushot.py

## Getting Started

### Prerequisites

- Git
- Python 3.10 or newer

### Setup

```bash
git clone https://github.com/garethpaul/flu-shot-data.git
cd flu-shot-data
```

No third-party Python dependencies are required for the current baseline.

## Running or Using the Project

Generate `flu.csv` and `flu.json` from the CDC weekly flu summary page:

```bash
python3 flushot.py
```

Generated data files are ignored by default. Commit generated outputs only when
the data provenance and source date are reviewed.

## Testing and Verification

Run the offline baseline:

```bash
make check
```

Use the absolute Makefile path to run the same gate from another working
directory. Verification resolves the checker relative to the loaded Makefile
and runs Python from the repository root rather than the caller's directory.

The baseline compiles the Python files, runs fixture-based unit tests, and
checks that the scraper stays Python 3 compatible, uses HTTPS, and keeps
fetching, parsing, and writing separated. Fetch URLs are validated as HTTPS
URLs with CDC-owned hostnames and no embedded credentials before any network
request is opened. The parser tests also cover CDC percent-positive cells that
include a space before the
percent sign, and they fail when the expected flu summary headers are missing.
They also cover unrelated legacy `cellpadding=3` tables before the expected
summary table, and summary tables that omit the extra non-data subheading row
before regional data. Repeated header rows or blank-region rows inside the
selected summary table are skipped before records are written. Duplicate region
labels, including case-only variants, fail parsing instead of producing
ambiguous records. Extracted week
numbers must be between 1 and 53, and week-ending labels must parse as real
calendar dates before records are written.
Live fetch URLs must not include query strings or fragments.
Live fetch timeouts are bounded before `urlopen` is called; invalid or
out-of-range timeout values fall back to 30 seconds.
Automatic redirects are rejected, and final response URLs are revalidated
against the same HTTPS CDC host policy. Live response bodies are limited to
2 MiB while the validated socket timeout bounds stalled operations.
Live CDC processing requires an exact HTTP 200 before final URL, metadata, or
body handling.
An optional `Content-Length` must be one ASCII-decimal field within the 2 MiB
limit; duplicate, combined, signed, padded, or malformed declarations fail
before the first body read. When present, the declaration must equal the final
bounded byte count; truncated or overlong bodies fail instead of reaching the
HTML parser. Streaming still enforces the limit independently.
Responses must declare exactly one `text/html` field with no charset or a
UTF-8-compatible charset before the first body read. Duplicate media metadata
is rejected. Bounded response bytes are decoded as
strict UTF-8; malformed byte sequences fail without exposing response content.
Only absent or one explicit identity Content-Encoding field is accepted;
compressed, duplicated, or otherwise transformed bodies are rejected before
the first body read.

The `make lint`, `make test`, and `make build` aliases run the same offline
baseline while this project has no narrower installed gates.
GitHub Actions runs the same offline `make check` baseline for pushes and pull
Checkout uses read-only permissions without persisting the GitHub token.

Fixture tests do not prove that the current live CDC page still has compatible
markup. Validate live scraping separately before publishing current data.

## Configuration and Secrets

- No required secret or credential file was identified in the repository scan. If you add integrations later, keep secrets out of git.

## Security and Privacy Notes

- Review changes touching network requests, sockets, or service endpoints; examples from the scan include flushot.py.
- Review changes touching file, media, JSON, XML, CSV, OCR, or data parsing; examples from the scan include flushot.py.
- Keep live fetch URLs on HTTPS with a hostname; use fixtures for default tests
  rather than live network calls.
- Keep live fetch hosts limited to `cdc.gov` or CDC subdomains unless a
  reviewed source migration changes the data provenance boundary.
- Reject embedded credentials in live fetch URLs before opening network
  requests.
- Reject query strings or fragments in live fetch URLs unless a reviewed source
  migration changes the provenance boundary.
- Keep live fetch timeouts bounded so network requests do not use invalid or
  excessive caller-provided values.

## Maintenance Notes

- Run `make check` before pushing parser, output schema, or documentation changes.
- See `SECURITY.md` for vulnerability reporting and safe research guidance.
- See `VISION.md` for project direction and contribution guardrails.
- See `docs/plans/2026-06-09-flu-shot-percent-normalization.md` for the
  percent field normalization contract.
- See `docs/plans/2026-06-09-flu-shot-summary-header-guard.md` for the CDC
  summary table header contract.
- See `docs/plans/2026-06-09-flu-shot-optional-subheading.md` for optional
  summary subheading handling.
- See `docs/plans/2026-06-09-flu-shot-table-selection.md` for selecting the
  expected summary table when unrelated matching tables are present.
- See `docs/plans/2026-06-09-flu-shot-summary-row-skip.md` for repeated header
  and blank-region row handling.
- See `docs/plans/2026-06-12-duplicate-region-guard.md` for region uniqueness
  validation.
- See `docs/plans/2026-06-09-flu-shot-fetch-url-validation.md` for fetch URL
  validation coverage.
- See `docs/plans/2026-06-09-flu-shot-fetch-host-validation.md` for CDC host
  validation coverage.
- See `docs/plans/2026-06-09-flu-shot-fetch-credential-guard.md` for fetch URL
  credential guard coverage.
- See `docs/plans/2026-06-09-flu-shot-fetch-url-parts-guard.md` for fetch URL
  query and fragment guard coverage.
- See `docs/plans/2026-06-09-flu-shot-fetch-timeout-validation.md` for live
  fetch timeout validation coverage.
- See `docs/plans/2026-06-10-ci-baseline.md` for the hosted GitHub Actions
  baseline.
- See `docs/plans/2026-06-12-live-fetch-boundaries.md` for redirect and response
  size guards.
- See `docs/plans/2026-06-13-response-content-type-boundary.md` for HTML media
  type, charset, and guard-before-read coverage.
- See `docs/plans/2026-06-13-strict-utf8-response-decoding.md` for strict body
  decoding and malformed-response coverage.
- See `docs/plans/2026-06-13-response-content-encoding-boundary.md` for the
  identity-only transport representation and guard-before-read coverage.
- See `docs/plans/2026-06-14-response-content-length-integrity.md` for exact
  declared-versus-received response length verification.

## Contributing

Keep changes small and tied to the project that is already present in this repository. For code changes, document the toolchain used, avoid committing generated dependency directories or local configuration, and update this README when setup or verification steps change.
