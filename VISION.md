## Flu Shot Data Vision

This document explains the current state and direction of the project.
Project overview and developer docs: [`README.md`](README.md)

Flu Shot Data is a Python 3 scraper that reads CDC weekly flu summary data
and writes `flu.csv` and `flu.json`.

The repository is useful as a preserved public-health data extraction script
using standard-library fetching, table parsing, CSV output, and JSON conversion.
Basic context lives in [`README.md`](README.md).

The goal is to keep the data extraction process understandable while making
source fragility, generated outputs, and runtime assumptions explicit.

The current focus is:

Priority:

- Replace the retired single-page CDC source through issue #24 using stable
  official FluView data products and an explicitly versioned schema
- Preserve the reviewed FluView source map and the decision that current
  provider, subtype, and pediatric mortality semantics require a `v2` schema
- Preserve the CDC weekly-summary extraction logic
- Keep CSV and JSON output schemas visible
- Avoid committing generated data unless intentionally versioned
- Keep the parser testable without live CDC network access

Current baseline:

- `scripts/check-baseline.sh` and `make check` verify Python 3 syntax,
  fixture-based tests, generated-output ignores, and static parser guardrails.
- Fetching, parsing, and output writing are separate functions in `flushot.py`.
- The CDC URL uses HTTPS, and fetch URLs are validated as HTTPS URLs with hosts
  before network requests are opened.
- Live fetch URLs are limited to `cdc.gov` or CDC subdomains before network
  requests are opened.
- Live fetch URLs reject embedded credentials before network requests are
  opened.
- Live fetch URLs reject query strings or fragments before network requests are
  opened.
- Live CDC fetch URLs reject every explicit port before network request construction or redirect handling.
- Live fetch timeout values are bounded before `urlopen` is called, with
  invalid values falling back to 30 seconds.
- Automatic redirects are rejected and final response URLs are revalidated
  against the CDC hostname policy, with a 2 MiB response ceiling.
- Live CDC responses require exact HTTP 200 before final URL or metadata checks.
- Optional response lengths are single-valued ASCII decimals and remain subject
  to the independent streamed 2 MiB ceiling; a present declaration must equal
  the final bounded byte count.
- Live responses require exactly one HTML media metadata field and an absent or
  UTF-8-compatible charset declaration before any body read.
- Bounded response bytes are decoded strictly as UTF-8, with malformed bodies
  rejected before parsing.
- Live responses enforce identity-only content encoding before bounded body
  reads; compressed, duplicated, or transformed representations are unsupported.
- The parser validates expected CDC summary table headers and selects the first
  matching summary table before emitting rows.
- Repeated header rows and rows without a region value are skipped within the
  selected summary table.
- Duplicate region labels are rejected case-insensitively before output.
- Summary subheading rows are optional; the parser starts after the header row
  and skips short non-data rows.
- Percent-positive cells are normalized without a trailing percent sign or
  extra spacing.
- Influenza week numbers and week-ending labels are validated against numeric
  and calendar boundaries before output.
- `flu.csv` and `flu.json` are treated as generated outputs unless intentionally
  reviewed as data artifacts.
- Reject direct, symlink-resolved, and same-file output destination collisions
  before materializing records or opening generated files.
- Preflight both output parent directories before opening generated files.
- Reject existing non-regular output targets before staging or publication.
- Preflight the complete output record schema and UTF-8 text before opening
  generated files.
- Roll back paired output publication failures without leaving mixed
  generations or invocation-owned temporary artifacts.
- Retain recoverable prior output bytes when rollback itself cannot complete.
- Preserve primary staging and publication failures across cleanup errors while
  attempting every remaining invocation-owned artifact cleanup.
- Preserve output file modes and resolved symlink targets across publication.
- `make lint`, `make test`, and `make build` run the same offline baseline
  while no narrower gates are installed.
- GitHub Actions runs the offline `make check` baseline on Python 3.10, 3.12,
  and 3.14 for pushes and pull requests.
- Hosted checkout credentials are not persisted and actions remain pinned to
  immutable revisions.

Next priorities:

- Complete issue #24 before publishing current generated data
- Implement source-specific bounded JSON/CSV transport and minimized official
  fixtures before changing the default command
- Keep the completed source-specific FluView transport stage separate from
  schema decoding and publication so the historical default remains unchanged
- Build later joins only from validated FluView phase 2 metadata with recorded
  official fixture provenance
- Define `v2` records only from validated FluView phase 2 regional data that
  preserves separate lab, HHS-region, national, virus-count, ILI, and flag
  provenance
- Keep expected CDC summary table headers visible when upstream markup changes
- Keep optional summary subheading behavior covered by fixtures
- Keep row-level skip behavior covered by fixtures when CDC repeats headers
- Keep region uniqueness covered when CDC summary row handling changes
- Add provenance metadata if generated outputs are intentionally committed
- Update source URLs if CDC structure changes
- Keep URL validation covered if alternate CDC source URLs are introduced
- Keep source host validation reviewed when CDC URL provenance changes
- Keep response content-type validation ahead of live response-body reads
- Keep strict UTF-8 decoding after bounded live response-body reads
- Keep identity-only content encoding validation before response-body reads
- Keep fetch credential rejection covered when source URL handling changes
- Keep fetch query and fragment rejection covered when source URL handling
  changes
- Keep fetch timeout validation covered when live fetch behavior changes
- Keep `.github/workflows/check.yml` in sync with the local Python baseline.

Contribution rules:

- One PR = one focused parser, dependency, output, or documentation change.
- Document source URL and output schema changes.
- Use small HTML fixtures for parser tests.
- Keep generated outputs separate from code changes unless reviewed as data.

## Security And Responsible Use

Canonical security policy and reporting:

- [`SECURITY.md`](SECURITY.md)

Public health data should be handled carefully. Changes must avoid silently
mislabeling weeks, dates, regions, or metrics when the upstream page changes.

## What We Will Not Merge (For Now)

- Live-only tests as the default quality gate
- Generated data dumps without provenance
- Parser rewrites without fixture coverage
- Claims of current CDC compatibility without verification

This list is a roadmap guardrail, not a permanent rule.
Strong user demand and strong technical rationale can change it.
