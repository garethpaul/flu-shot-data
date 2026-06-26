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

The historical CDC weekly summary endpoint used by the default command was
retired before June 26, 2026. The current FluView report splits the legacy
11-field schema across multiple data products, so unattended live generation
is temporarily unavailable rather than silently emitting incomplete or stale
records. Track the source migration in
[#24](https://github.com/garethpaul/flu-shot-data/issues/24).
Official FluView JSON and CSV endpoints now have a reviewed source map in
[`docs/plans/2026-06-26-cdc-fluview-source-provenance.md`](docs/plans/2026-06-26-cdc-fluview-source-provenance.md).
The research confirms that the historical `NUM_JURIS`, combined no-subtype,
and regional pediatric-death fields cannot be reproduced truthfully, so the
replacement requires an explicit `v2` schema rather than silent coercion.

The first migration stage now exposes source-specific FluView transport
functions for the two reviewed initialization JSON feeds, HHS-region phase 2
JSON, and the ILINet CSV export. They enforce exact URLs and methods, bounded
identity responses, strict UTF-8, reviewed media types, deterministic POST
bodies, JSON-object roots, and HHS region identifiers 1 through 10. These
functions do not change the legacy command or publish a partial `v2` schema.

A minimized official phase 2 initialization fixture now records exact source
provenance, and `parse_fluview_phase2_metadata()` produces validated FluView phase 2 metadata
for the current enabled season, latest populated MMWR week,
all ten canonical HHS regions, lab types, and virus categories. The decoder is
order-independent and rejects duplicate identifiers, invalid dates and
week/year metadata, incomplete region coverage, empty labels, and unknown lab
references before later joins can consume them.

A second minimized official fixture records the phase 2 regional response's
exact request and full-response provenance. `parse_fluview_phase2_region_data()`
validates the endpoint's declared positional structure for every returned week.
The result is validated FluView phase 2 regional data that preserves public
health and clinical labs, HHS regions, national records, virus-count windows,
ILI metrics, and source flags separately. It does not select or publish the
future `v2` schema.

The official ILINet CSV now has its own minimized provenance fixture and strict
decoder. `parse_fluview_phase2_line_csv()` produces a typed source model.
This is validated FluView ILINet CSV data keyed by MMWR year/week with age-group
visits, total ILI visits, total patients, provider counts, and
weighted/unweighted ILI. Provider counts remain explicitly distinct from the
retired `NUM_JURIS` field, and no cross-source join is implied.

`parse_fluview_phase4_mortality()` now produces validated FluView phase 4 mortality
as national weekly virus counts plus separate HHS season totals. It verifies
their shared season total and never copies national deaths into regional weeks.

`build_fluview_v2_dataset()` now assembles a deterministic FluView v2 dataset
with `schema_version: 2` from those validated sources. It fails closed unless
all ten HHS regions and every regional week join exactly, duplicated ILI
metrics agree, and mortality covers the regional weeks. Laboratory virus
categories and pediatric-mortality categories remain separate namespaces, and
national weekly mortality remains separate from HHS season totals. This pure
builder does not change the legacy default command or publish files yet.

FluView v2 publication is available only through the explicit JSON command:

```bash
python3 flushot.py v2 --json-path flu-v2.json
```

The path defaults to `flu-v2.json`. The command fetches and validates every
reviewed source, builds the complete dataset, and atomically replaces one
finite JSON file. Running `python3 flushot.py` with no arguments still uses the
unchanged historical command and schema.

The command below still documents the legacy entry point, but currently fails
before output publication because the retired CDC URL no longer returns the
expected summary page:

```bash
python3 flushot.py
```

Generated data files are ignored by default. Commit generated outputs only when
the data provenance and source date are reviewed.
CSV and JSON destinations must identify distinct filesystem targets; direct,
symlink-resolved, and existing same-file aliases are rejected before writes.
Each output parent must be an existing directory before either file is opened,
so an invalid second destination cannot truncate the first output.
Each existing resolved destination must be a regular file; directories, FIFOs,
devices, sockets, and other special targets are rejected before staging.
Every output record must use the exact documented headers, string values, and
valid UTF-8 text before either destination is opened or truncated.
CSV and JSON are staged completely before either destination is replaced. If
handled staging or publication fails, both prior outputs are restored (or both
new outputs remain absent) and invocation-owned temporary files are removed.
If cleanup also fails, the primary staging, publication, or incomplete-rollback
error is preserved, and every remaining invocation-owned cleanup is still attempted.
Published outputs retain normal umask-derived or existing file modes, and
distinct symlink destinations continue to update their resolved targets.
This rollback does not make two filesystem paths crash- or power-loss-atomic.
If rollback itself cannot restore a destination, the operation raises a stable
error and retains invocation-owned backups for manual recovery.

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
Live CDC fetch URLs reject every explicit port before network request construction or redirect handling.
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
markup. A live check on June 26, 2026 confirmed that the default source is
retired; do not publish current data until issue #24 defines and validates the
replacement official CDC sources.

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
- Live CDC fetch URLs reject every explicit port before network request construction or redirect handling.
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
