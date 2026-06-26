# Changes

## 2026-06-26 15:28 PDT - P1 - Build truthful FluView v2 dataset

### Summary

Added the first deterministic FluView v2 dataset contract and explicit
fail-closed joins across all validated current FluView sources without changing
the legacy default command or publishing partial files.

### Work completed

- Preserved each regional record's validated `yearweek` join key.
- Recorded exact full-response provenance for all ten official ILINet region
  exports while retaining the two fixture weeks shared by regional JSON.
- Added `build_fluview_v2_dataset()` with `schema_version: 2`, exact
  season/current-week identity, ten-region and week coverage, duplicated ILI
  agreement, deterministic ordering, and non-mutation guarantees.
- Kept public-health and clinical lab surveillance separate, used explicit
  virus count-window names, and kept laboratory virus IDs in their own catalog.
- Preserved pediatric mortality as national weekly records plus separate HHS
  season totals with its own virus category namespace.
- Added mutation-sensitive schema, provenance, ordering, coverage, metric,
  boolean, guidance, and plan contracts.

### Validation

- RED regressions covered missing `yearweek`, the absent builder, and malformed
  metric types escaping the intended validation boundary.
- GREEN fixture suite — all 110 tests passed.
- Live source smoke — built 380 regional weekly records, 38 national mortality
  weeks, ten HHS season totals, and the verified 184-death season total for
  current MMWR yearweek 202624.
- `make check`, `make lint`, `make test`, `make build`, repository-root Make,
  and absolute-Makefile verification from `/tmp` — passed.
- Ten isolated hostile fixture, source, schema, test, plan, and guidance
  mutations — all rejected.
- JSON syntax, Python compilation, shell syntax, current-tree gitleaks, and
  `git diff --check` — passed with no findings.

### Bugs / findings

- Phase 2 laboratory and phase 4 mortality sources reuse numeric virus IDs for
  different meanings, so the FluView v2 dataset exposes separate catalogs.
- All current regional and ILINet week/region combinations agree exactly on
  weighted and unweighted ILI, allowing missing or divergent joins to fail.

### Blockers

- None for the dataset contract and join stage.

### Next action

- Design versioned publication and CLI wiring without changing the historical
  default command.

## 2026-06-26 15:22 PDT - P1 - Decode phase 4 pediatric mortality

- Recorded a 41,171-byte current-season fixture with exact provenance for the
  1,017,561-byte official response.
- Added strict decoding of 38 published national weeks, four virus categories,
  previously/newly reported counts, and ten separate HHS season totals.
- Rejected malformed catalogs/weeks, incomplete groups, count disagreement,
  nonzero future placeholders, invalid regions/rates, and unequal totals.
- Live decoding and all 104 tests pass; the current season total is 184 deaths.
- The normalized result is validated FluView phase 4 mortality.
- National weekly deaths remain separate from HHS season totals; no regional
  weekly mortality is fabricated.

### Next action

- Define the versioned `v2` schema and explicit cross-source joins.

## 2026-06-26 15:16 PDT - P1 - Decode FluView ILINet CSV data

### Summary

Recorded a minimized official ILINet line-chart fixture and added strict typed
decoding of truthful regional provider, visit, patient, and ILI values for
issue #24 without changing the legacy default or joining sources prematurely.

### Work completed

- Recorded the exact POST body, retrieval time, response media type, full
  2,583-byte response length, and SHA-256 provenance.
- Retained the exact report title/header plus first, year-boundary, and current
  rows in a compact fixture.
- Added exact envelope, identifier, duplicate, numeric text, reserved-column,
  age-total, patient/provider, percentage, and displayed-precision validation.
- Added a stable `yearweek`-keyed source model with five age-group counts,
  total ILI visits, total patients, provider count, and weighted/unweighted ILI.
- Preserved the decision that provider counts are not legacy jurisdiction
  counts and deferred all cross-source joins to the versioned `v2` stage.

### Threads

- None; this stage follows the merged regional source decoder.

### Files changed

- `tests/fixtures/fluview_phase2_line_region1_2026-06-26.json` — minimized
  official CSV text and exact provenance.
- `flushot.py` — exact ILINet CSV envelope and typed row decoder.
- `tests/test_flushot.py` — provenance, normalization, order, envelope,
  identifier, numeric, arithmetic, and precision regressions.
- `scripts/check-baseline.sh` — durable fixture and decoder contracts.
- `AGENTS.md`, `README.md`, `SECURITY.md`, and `VISION.md` — maintained
  validated FluView ILINet CSV data policy and roadmap.
- `docs/plans/2026-06-26-fluview-ilinet-csv-decoder-design.md` — design record.
- `docs/plans/2026-06-26-fluview-ilinet-csv-decoder.md` — implementation record.

### Validation

- RED focused suite — five tests produced 18 expected errors on the missing
  decoder.
- RED precision regression — excessive decimal precision escaped as
  `decimal.InvalidOperation` before the parser bounded source text.
- GREEN focused/full suites — all 98 tests passed.
- Live source smoke — decoded all 38 rows from yearweek 202540 through 202624;
  the current Region 1 provider count is 270.
- `make check`, `make lint`, `make test`, `make build`, repository-root Make,
  and absolute-Makefile verification from `/tmp` — passed.
- Ten isolated hostile provenance, fixture envelope, row completeness, source,
  output, regression, guidance, and plan mutations — all rejected.
- JSON syntax, in-memory Python compilation, shell syntax, current-tree
  gitleaks, and `git diff --check` — passed with no findings.

### Bugs / findings

- The official CSV includes both `AGE 25-49` and an empty `AGE 25-64` column;
  the populated non-overlapping age groups sum to `ILITOTAL`.
- P1 live generation still requires the phase 4 mortality decoder, complete
  `v2` schema, explicit joins, and publication wiring.

### Blockers

- None for this ILINet decoding stage.

### Next action

- Record and decode the phase 4 national pediatric mortality source before
  defining the final `v2` contract and joins.

## 2026-06-26 15:01 PDT - P1 - Decode FluView phase 2 regional data

### Summary

Recorded a minimized official phase 2 regional fixture and added strict,
order-independent decoding of the endpoint's declared positional structure for
issue #24 without choosing or publishing the future `v2` schema.

### Work completed

- Recorded exact POST request, retrieval time, response media type, full
  1,166,773-byte response length, and SHA-256 provenance.
- Retained two official weeks with both lab types, all ten HHS regions,
  national region 0, every virus category, metric, flag, and declared schema
  field consumed by the decoder.
- Added complete response validation for week/catalog agreement, positional
  row shape, lab and region completeness, virus relationships, ordered counts,
  bounded finite metrics, and binary flags.
- Added a stable nested source model preserving lab, HHS-region, national,
  virus-count-window, ILI, and flag provenance before later joins.
- Added mutation-sensitive fixture, decoder, regression, plan, and guidance
  contracts.

### Threads

- None; this stage follows the merged source transport and metadata work.

### Files changed

- `tests/fixtures/fluview_phase2_region_2026-06-26.json` — minimized official
  regional response and provenance.
- `flushot.py` — exact declared-structure validation and full regional source
  normalization.
- `tests/test_flushot.py` — provenance, happy-path, order, structure, catalog,
  completeness, count, metric, and flag regressions.
- `scripts/check-baseline.sh` — durable fixture and decoder contracts.
- `AGENTS.md`, `README.md`, `SECURITY.md`, and `VISION.md` — maintained
  validated FluView phase 2 regional data policy and roadmap.
- `docs/plans/2026-06-26-fluview-phase2-regional-decoder-design.md` — design
  record.
- `docs/plans/2026-06-26-fluview-phase2-regional-decoder.md` — implementation
  record.

### Validation

- RED focused suite — six tests produced 21 expected errors on the missing
  decoder.
- GREEN focused/full suites — all 92 tests passed.
- Live fetch-to-decoder smoke — normalized all 38 current-season weeks, both
  lab types, ten HHS regions per lab, and national region 0.
- `make check`, `make lint`, `make test`, `make build`, repository-root Make,
  and absolute-Makefile verification from `/tmp` — passed.
- Ten isolated hostile provenance, fixture completeness, schema, decoder,
  regression, guidance, and plan mutations — all rejected.
- JSON syntax, in-memory Python compilation, shell syntax, current-tree
  gitleaks, and `git diff --check` — passed with no findings.

### Bugs / findings

- The endpoint's declared schema represents repeated region-type collections,
  while live lab rows serialize regional and national collections as separate
  positional segments; assuming one segment would discard national data.
- P1 live generation remains unavailable until the complete `v2` schema,
  remaining source fixtures/decoders, joins, and publication are implemented.

### Blockers

- None for this regional decoding stage.

### Next action

- Define the versioned `v2` record contract and explicit source joins without
  changing the legacy default command.

## 2026-06-26 14:52 PDT - P1 - Normalize FluView phase 2 metadata

### Summary

Recorded a minimized official phase 2 initialization fixture with exact
provenance and added strict order-independent metadata normalization for later
issue #24 joins.

### Work completed

- Recorded two seasons, four representative MMWR rows, all ten HHS regions,
  both lab types, and all twelve current virus categories from the exact
  357,473-byte official response.
- Added current enabled season and latest current-season MMWR selection without
  trusting array order or season range fields.
- Added duplicate, integer, string, date, week/year, region completeness,
  canonical name, lab catalog, and virus relationship validation.
- Added mutation-sensitive fixture, decoder, regression, plan, and guidance
  contracts.

### Threads

- None; this stage follows the merged source map and bounded transport work.

### Files changed

- `tests/fixtures/fluview_phase2_init_2026-06-26.json` — minimized official
  fixture and provenance.
- `flushot.py` — validated FluView phase 2 metadata normalization.
- `tests/test_flushot.py` — fixture, happy-path, order, duplicate, metadata,
  and catalog regressions.
- `scripts/check-baseline.sh` — durable provenance and decoder contracts.
- `AGENTS.md`, `README.md`, `SECURITY.md`, and `VISION.md` — maintained decoder
  ownership and roadmap.
- `docs/plans/2026-06-26-fluview-phase2-metadata-design.md` — design record.
- `docs/plans/2026-06-26-fluview-phase2-metadata.md` — implementation record.

### Validation

- RED focused suite — 37 cases errored on the missing decoder.
- GREEN focused/full suites — all 85 tests passed.
- Live fetch-to-decoder smoke — normalized season 2025-26, week 24 ending
  2026-06-20, ten HHS regions, two lab types, and twelve virus categories.
- Repository-root and absolute-Makefile `make check` from `/tmp` — passed all
  85 tests and specialized transport/fixture contracts.
- Ten isolated hostile provenance, fixture completeness, season/week selection,
  duplicate, date, region, relationship, guidance, and plan mutations — all
  rejected.
- JSON syntax, in-memory Python compilation, shell syntax, current-tree
  gitleaks, and `git diff --check` — passed with no findings.

### Bugs / findings

- P1 live generation remains unavailable until regional response fixtures and
  decoding, a complete `v2` schema, source joining, and publication exist.

### Blockers

- None for this metadata stage.

### Next action

- Record minimized regional phase 2 fixtures and decode the declared nested
  data structure without changing the default command.

## 2026-06-26 14:46 PDT - P1 - Add bounded FluView transports

### Summary

Added the first production stage for issue #24: source-specific FluView transport
functions with fixed request and response authority. The retired
legacy default and historical schema remain unchanged.

### Work completed

- Added fixed phase 2 and phase 4 initialization JSON GETs.
- Added fixed HHS-region phase 2 JSON and ILINet CSV POSTs.
- Added positive season and HHS region 1 through 10 validation before network
  construction.
- Added exact final-URL, reviewed media-type, identity encoding, bounded byte,
  strict UTF-8, deterministic JSON body, and JSON-object-root enforcement.
- Added mutation-sensitive baseline and synchronized maintenance guidance.

### Threads

- None; implementation followed the merged issue #24 source map directly.

### Files changed

- `flushot.py` — dedicated source transports and shared narrow validators.
- `tests/test_flushot.py` — request, response, identifier, media, and JSON
  regressions.
- `scripts/check-baseline.sh` — durable source, test, plan, and guidance
  contracts.
- `AGENTS.md`, `README.md`, `SECURITY.md`, and `VISION.md` — maintained source
  transport boundaries and roadmap.
- `docs/plans/2026-06-26-fluview-source-transports-design.md` — design record.
- `docs/plans/2026-06-26-fluview-source-transports.md` — implementation record.

### Validation

- RED focused suite — nine tests errored on missing source APIs.
- RED CSV parameter regression — accepted an unreviewed media parameter.
- RED JSON parameter regression — accepted an unrelated `profile` parameter.
- GREEN focused/full suites — all 78 tests passed.
- Live source smoke — all four functions returned the expected official source
  structures; phase 2 had 38 MMWR rows, the CSV was 2,583 bytes, and phase 4
  had 5,740 weekly mortality entries.
- `make check` — passed all 78 tests and specialized transport boundaries.
- The full gate exposed a pre-existing fetch-port checker that counted
  `build_opener.assert_not_called()` globally; it now scopes that proof to the
  named port regression so independent pre-network tests remain valid.
- A helper-ownership rename initially doubled private underscores; the baseline
  rejected the source-contract mismatch before the typo was corrected.
- Repository-root and absolute-Makefile verification from `/tmp` passed.
- Ten isolated hostile URL, final-response, request-body, identifier, media,
  JSON-root, JSON-parameter, legacy-default, guidance, and plan mutations were
  all rejected.
- In-memory Python compilation, shell syntax, current-tree gitleaks, and
  `git diff --check` passed.

### Bugs / findings

- P1 live generation remains unavailable until source fixtures, nested
  decoding, a complete `v2` schema, joining, and publication are implemented.

### Blockers

- None for this transport stage.

### Next action

- Record minimized official fixtures and implement validated phase 2 metadata
  decoding without changing the default command.

## 2026-06-26 14:42 PDT - P1 - Map current FluView sources

### Summary

Completed the official source-provenance research needed for issue #24 and
proved that the retired eleven-field schema cannot be reproduced truthfully
from current FluView products.

### Work completed

- Verified official JSON endpoints for season/MMWR metadata, HHS-region ILI,
  positivity, subtype counts, and pediatric mortality.
- Verified the official line-chart CSV provider-count export.
- Mapped each usable source field and documented request shapes.
- Decided to preserve the historical schema as `v1` and require an explicit
  live `v2` schema rather than coercing incompatible fields.
- Defined staged transport, fixture, validation, join, and publication work.

### Threads

- None; issue #24, prior design records, the parser, tests, current CDC pages,
  dashboard bundles, and live official responses were reviewed directly.

### Files changed

- `docs/plans/2026-06-26-cdc-fluview-source-provenance.md` — verified source
  map, incompatibility decision, and implementation stages.
- `docs/plans/2026-06-26-cdc-fluview-source-migration.md` — linked evidence and
  recorded the required versioned replacement.
- `AGENTS.md`, `README.md`, `SECURITY.md`, and `VISION.md` — synchronized
  migration and safety guidance.

### Validation

- Official FluView phase 2 initialization JSON — HTTP 200; seasons, MMWR,
  regions, lab types, and virus categories verified.
- Official FluView phase 2 regional JSON — HTTP 200; declared nested structure,
  ILI, positivity, and subtype counts verified.
- Official FluView line-chart CSV — HTTP 200; `NUM. OF PROVIDERS` confirmed as
  distinct from legacy jurisdictions.
- Official FluView phase 4 initialization JSON — HTTP 200; national pediatric
  mortality grain verified.
- Machine assertions over the four exact downloaded responses — passed source
  key, category, field, and grain checks after correcting one local `jq`
  operator-precedence mistake against the same response bytes.
- `make check` — passed all 69 offline regressions and specialized transport
  boundary checks.
- Current-tree gitleaks and `git diff --check` — passed with no findings.

### Bugs / findings

- P1 remains open: the default live source is retired.
- `NUM_JURIS` has no verified current equivalent.
- Current no-subtype categories and pediatric mortality grain are incompatible
  with the historical regional schema.

### Blockers

- Production migration still requires source-specific bounded JSON/CSV
  transports, minimized official fixtures, and a complete `v2` output schema.

### Next action

- Implement the source-specific transport layer test-first without changing
  the default command.

## 2026-06-26 11:46 PDT - P1 - Record retired CDC live source

### Summary
Confirmed that the default CDC weekly URL now returns HTTP 403 with a CDC Page
Not Found response. The current FluView report splits the legacy output fields
across multiple products, so a one-line URL replacement would be incorrect.

### Work completed
- Opened issue #24 with official CDC evidence and migration requirements.
- Marked unattended live generation unavailable until the schema is rebuilt
  from stable official sources.
- Preserved the fixture-backed historical parser and output safety contracts.

### Threads
- Started: CDC FluView source migration — tracked in issue #24.
- Delegated: none.

### Files changed
- `README.md` — documented the retired default and publication boundary.
- `VISION.md` — prioritized the source and schema migration.
- `docs/plans/2026-06-26-cdc-fluview-source-migration.md` — recorded evidence,
  rejected shortcuts, requirements, and validation boundaries.

### Validation
- Live request to `https://www.cdc.gov/flu/weekly/` — HTTP 403 Page Not Found.
- Official `https://www.cdc.gov/fluview/surveillance/index.html` — HTTP 200.
- `make check` — passed after documentation changes.

### Bugs / findings
- P1: `python3 flushot.py` cannot currently fetch its default live source.
- Current FluView pages do not contain the legacy combined regional table.

### Blockers
- Stable official sources and join semantics for every legacy field require a
  separate, fixture-backed design; static weekly URLs are not acceptable.

### Next action
- Implement issue #24 test-first using recorded official CDC fixtures and a
  versioned source/schema contract.

## 2026-06-17

- Rejected existing directory and special-file output targets before staging
  or publication can mutate them.

## 2026-06-16

- Preserved primary output-staging errors when temporary-file cleanup also
  fails, while continuing cleanup of every reserved stage.
- Preserved primary paired-publication and incomplete-rollback errors when
  invocation-owned artifact cleanup also fails, while continuing every
  remaining cleanup attempt.

## 2026-06-15

- Added rollback-capable paired CSV and JSON publication after complete
  same-directory staging, retaining recovery backups if rollback is incomplete
  and preserving output modes and distinct symlink targets.
- Preflighted output record headers, value types, and UTF-8 text before opening
  either generated destination.
- Preflighted CSV and JSON output parent directories before truncating either
  destination.
- Rejected colliding CSV and JSON output destinations before file writes.
- Live CDC fetch URLs reject every explicit port before network request construction or redirect handling.
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
