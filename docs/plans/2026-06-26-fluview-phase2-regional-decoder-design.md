# FluView Phase 2 Regional Decoder Design

Status: Completed

## Goal

Record a minimized official phase 2 regional response and decode the endpoint's
declared positional structure without choosing or flattening the future `v2`
publication schema.

## Evidence

- `POST https://gis.cdc.gov/grasp/flu2/PostPhase02WHOGetData` returned HTTP 200
  with `application/json; charset=utf-8` on 2026-06-26.
- The exact 1,166,773-byte response had SHA-256
  `519d0af02375ba80319b1981ba45fd3659d71a51e393d32d68583e0eba31b994`.
- The response contains 38 MMWR weeks, both required lab types, all ten HHS
  regions, and a national region for every week and lab.
- The declared `data_structure` is stored in
  `WHO_Virus_Counts_Summary_Cumulative`, not at the response root.
- Each lab row contains separate positional collection segments for regional
  region type `1` and national region type `3`. A decoder that assumes a
  single nested collection would silently discard national data.
- Public-health labs contain virus IDs 1-9 and 12; clinical labs contain virus
  IDs 10-11. Counts satisfy cumulative >= three-week >= current.

## Approaches

### Recommended: strict source-specific full-response decoder

Validate the exact declared structure, every week, both lab types, all HHS
regions, the national region, every expected virus category, metrics, flags,
and relationships against normalized phase 2 metadata. Return a stable nested
source model that preserves lab type and region grain.

This is the narrowest approach that proves the complete official response is
understood before any `v2` records or joins are selected.

### Rejected: selected-region-only decoder

Decode only the requested HHS region. This is smaller, but the official
endpoint returns all regions and national data. Ignoring the rest would allow
malformed or drifting source content to pass validation and would discard
useful provenance.

### Rejected: generic positional-schema interpreter

Build an arbitrary recursive interpreter for any future `data_structure`.
This would be substantially more code and a broader public contract than the
single reviewed endpoint requires. Exact structure validation plus a focused
decoder is easier to audit and fails closed on schema drift.

## Decoder Contract

`parse_fluview_phase2_region_data(payload, metadata)` accepts the raw regional
response object and the validated result from `parse_fluview_phase2_metadata`.
It returns:

- the validated season and current week identifiers;
- all response weeks keyed by MMWR identifier with week number and end date;
- both lab types kept separate;
- HHS regions 1 through 10 and national region 0 kept separate;
- virus counts keyed by virus identifier with cumulative, three-week, and
  current values;
- percent-positive, A/B percentages, weighted/unweighted ILI, baseline, and
  normalized boolean source flags.

The decoder does not mutate either input and does not infer publication fields.

## Validation Boundaries

Reject non-object inputs, missing or malformed collections, any declared
structure drift, duplicate or unknown identifiers, response/metadata catalog
disagreement, invalid week metadata, missing current week, malformed positional
row lengths, missing or extra region types, incomplete HHS coverage, invalid
national identifiers, missing or extra virus categories, negative or unordered
counts, non-finite or out-of-range metrics, and non-binary flags.

## Fixture

The provenance-bearing fixture retains two official weeks, both lab types, all
HHS regions, national records, all virus categories, the exact declared
structure, and only fields consumed by the decoder. The fixture records the
exact request, retrieval timestamp, response media type, full response byte
length, and full response SHA-256.

## Validation Plan

Tests first prove the API is absent, then cover successful normalization,
non-mutation, order independence, exact schema drift rejection, malformed
positional rows, catalog disagreement, duplicates, completeness, count
relationships, metric/flag boundaries, and missing current-week data. The full
offline gate, live fetch-to-decoder smoke, hostile baseline mutations, gitleaks,
and hosted Python/CodeQL checks must pass before an exact-head merge.
