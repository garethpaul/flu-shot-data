# FluView ILINet CSV Decoder Design

Status: Completed

## Goal

Record a minimized official ILINet CSV fixture and decode truthful regional
provider and visit counts without substituting them into the historical `v1`
jurisdiction field or prematurely defining the complete `v2` join.

## Evidence

- `POST https://gis.cdc.gov/grasp/flu2/PostPhase02LineChartDataDownload`
  returned HTTP 200 with `application/octet-stream` on 2026-06-26.
- The exact 2,583-byte response had SHA-256
  `985493ce04d949f06ac66d846b9bf56e513711bf362c3c00b6f0241448115128`.
- The response has one exact report-title row, one exact 13-column header, and
  38 current-season data rows from MMWR year/week 2025/40 through 2026/24.
- `NUM. OF PROVIDERS` is a provider count and is not the retired schema's
  `NUM_JURIS` value.
- `AGE 25-64` is present but empty in every current official row; `AGE 25-49`
  and `AGE 50-64` contain the non-overlapping counts used by `ILITOTAL`.
- The five populated age counts sum to `ILITOTAL`, which does not exceed total
  patients. The displayed unweighted ILI is the rounded percentage of those
  two totals.

## Approaches

### Recommended: independent strict CSV decoder keyed by yearweek

Validate the exact title and headers, parse every row into typed values, reject
duplicates and malformed counts, verify age/count arithmetic, and return rows
keyed by MMWR `yearweek`. Tag the normalized source with the reviewed season
and HHS region identifiers supplied to the transport.

This preserves a stable source boundary while leaving MMWR-ID matching and
cross-source completeness checks to the later explicit join stage.

### Rejected: join directly inside the CSV parser

Accept phase 2 regional output and merge provider counts immediately. This
would combine parsing, source validation, and product schema decisions before
the phase 4 source and complete `v2` contract are designed.

### Rejected: expose raw strings

Return `csv.DictReader` rows unchanged. This would defer duplicate, numeric,
arithmetic, and semantic validation into every downstream consumer.

## Decoder Contract

`parse_fluview_phase2_line_csv(csv_text, season_id, region_id)` returns:

- validated positive season and HHS region identifiers;
- rows keyed by integer `yearweek`;
- MMWR year and week number;
- age 0-4, 5-24, 25-49, 50-64, and 65+ ILI visit counts;
- total ILI visits, total patients, and provider count;
- unweighted and weighted ILI percentages.

The decoder does not mutate input, infer MMWR IDs, perform cross-source joins,
or map provider counts to legacy jurisdiction semantics.

## Validation Boundaries

Reject non-string input, unexpected title/header rows, blank or extra records,
duplicate `yearweek` values, booleans or malformed numeric text, invalid MMWR
years/weeks, non-empty deprecated `AGE 25-64` cells, negative counts, zero
patients/providers, age totals that do not equal `ILITOTAL`, ILI totals above
patient totals, non-finite or out-of-range percentages, and displayed
unweighted ILI that does not match the source counts at its declared precision.

## Fixture

The fixture records the exact POST body, retrieval timestamp, response media
type, full byte length, and SHA-256. It retains the title/header plus the first,
year-crossover, and current rows so parsing and arithmetic contracts remain
small and reviewable.

## Validation Plan

Tests first prove the decoder is absent, then cover normalization,
order-independence, provenance, exact title/header enforcement, duplicate and
numeric rejection, reserved-column behavior, count arithmetic, percentage
precision, and identifier validation. The full offline gate, live full-response
decode, hostile mutations, gitleaks, and hosted Python/CodeQL must pass before
an exact-head merge.
