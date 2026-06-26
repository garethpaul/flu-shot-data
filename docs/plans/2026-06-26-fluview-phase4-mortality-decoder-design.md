# FluView Phase 4 Mortality Decoder Design

Status: Completed

## Goal

Record a minimized official phase 4 fixture and decode pediatric mortality
without copying national weekly deaths into HHS-region weekly records.

## Evidence

- `GET https://gis.cdc.gov/grasp/flu4/GetPhase04InitApp?appVersion=Public`
  returned HTTP 200 with `application/json; charset=utf-8` on 2026-06-26.
- The exact 1,017,561-byte response had SHA-256
  `81d560217254765f707d65b949272c56c305bcd65d13fe001f172789a46543fe`.
- `ped_flu_reported` identifies current MMWR week 24 ending 2026-06-20.
- `ped_flu_weekly` contains five records per MMWR week: virus ID 0 total plus
  IDs 1-4 for A, B, A/B not distinguished, and A and B.
- Each weekly `allwks` count equals `pwk + cwk`; total virus ID 0 equals the
  sum of virus IDs 1-4 for all three count fields.
- Current-season national totals sum to 184 deaths. The ten current-season
  `ped_flu_map` HHS counts also sum to 184, but those map values are season-level
  rather than week-level.
- Future current-season placeholder weeks are present with zero counts.

## Approaches

### Recommended: grain-preserving strict decoder

Validate the current season, current report week, all current-season week and
weekly-virus rows, the exact virus catalog, future-zero placeholders, and all
ten HHS season totals. Return national weekly records through the current report
week and a separate HHS season-total map, with equal national/regional totals.

This captures all verified mortality information without inventing a
week-by-region value.

### Rejected: attach national deaths to every HHS record

This would reproduce the legacy shape by misrepresenting national data as
regional data and multiplying the same deaths across ten rows.

### Rejected: expose only the national total

This would discard verified virus categories, reporting-status counts, weekly
timing, and season-level HHS totals needed for a truthful `v2` side table.

## Decoder Contract

`parse_fluview_phase4_mortality(payload, metadata)` accepts the raw phase 4
response and validated phase 2 metadata. It returns:

- current season and report-week identifiers;
- exact virus labels for IDs 1-4;
- national weeks through the current report week keyed by MMWR ID, with
  `yearweek`, total deaths, and per-virus previously reported, newly reported,
  and total counts;
- HHS regions 1-10 keyed to season death count and rate per million;
- the verified equal national and HHS season total.

The decoder does not mutate inputs, expose future placeholders, or infer
regional weekly deaths.

## Validation Boundaries

Reject malformed collections, duplicate/unknown IDs, season or report-week
disagreement, invalid year/week labels, incomplete five-record weekly groups,
negative or boolean counts, `pwk + cwk` disagreement, virus-total disagreement,
nonzero future placeholders, incomplete/noncanonical HHS coverage, invalid
rates, and national/HHS total disagreement.

## Fixture

The provenance-bearing fixture retains the current season record, all 53
current-season week rows and 265 weekly-virus rows, the exact virus catalog,
the singleton report metadata, and all ten current-season HHS map rows using
only decoder-consumed fields.

## Validation Plan

Tests first cover normalization, non-mutation, order independence, exact
provenance, catalog/report disagreement, malformed weekly groups and counts,
future placeholders, HHS completeness/rates, and cross-total disagreement. The
full offline gate, live full-response decode, hostile mutations, gitleaks, and
hosted Python/CodeQL must pass before exact-head merge.
