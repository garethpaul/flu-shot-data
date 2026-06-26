---
title: "design: Migrate the retired CDC weekly source"
type: design
date: 2026-06-26
status: proposed
issue: 24
---

# design: Migrate the retired CDC weekly source

## Confirmed current state

On June 26, 2026, the configured
`https://www.cdc.gov/flu/weekly/` endpoint returned HTTP 403 and a CDC Page Not
Found body. The official FluView landing and current-report routes return HTTP
200, but the report links separate clinical laboratory, public health
laboratory, ILINet, mortality, and other data products instead of the legacy
single regional summary table.

Primary evidence:

- `https://www.cdc.gov/fluview/index.html`
- `https://www.cdc.gov/fluview/surveillance/index.html`
- `https://www.cdc.gov/fluview/surveillance/2026-week-21.html`

## Existing contract

The utility emits one record per HHS region using eleven fields spanning week
metadata, outpatient illness, test positivity, reporting jurisdictions,
laboratory subtypes, and pediatric mortality. The maintained parser and paired
publication tests prove the historical fixture contract, not current live data
compatibility.

## Approaches

### Recommended: explicit multi-source adapter

Discover the current epidemiological week from the stable report route, fetch
official machine-readable products for each field group, validate each source
under the existing transport boundaries, and join by week and HHS region.
Version the source/schema contract if any legacy field is no longer available.

### Rejected: static weekly report URL

A URL such as `2026-week-21.html` becomes stale immediately and still lacks the
combined legacy table.

### Rejected: scrape report prose and presentation tables

Display wording and chart markup are not a stable machine-readable contract and
do not expose every existing regional field together.

## Requirements before implementation

1. Map every output field to a stable official CDC source and document its
   provenance.
2. Define current week and season discovery without hard-coded weekly paths.
3. Define exact regional join keys, missing-data behavior, and duplicate
   handling.
4. Preserve CDC-only HTTPS authority, no redirects, bounded reads, exact status
   and metadata validation, strict UTF-8, and credential-free requests.
5. Record representative official fixtures and write failing tests before new
   production code.
6. Keep paired CSV/JSON preflight and rollback behavior unchanged.

## Current validation boundary

Offline `make check` remains authoritative for the historical fixture and
output safety. Live generation is not supported until issue #24 completes this
design with source-specific fixtures and end-to-end provenance evidence.
