---
title: "research: Map current FluView machine-readable sources"
type: research
date: 2026-06-26
status: completed
issue: 24
---

# research: Map current FluView machine-readable sources

## Scope

Identify official CDC machine-readable sources for the retired weekly summary
without changing the live default or weakening the existing fetch boundaries.
All probes were performed on June 26, 2026 against `https://gis.cdc.gov`.

## Verified source map

### Season, week, region, and category metadata

`GET /grasp/flu2/GetPhase02InitApp?appVersion=Public` returns JSON containing:

- `seasons` with stable numeric season identifiers and labels;
- `mmwr` with MMWR identifiers, week numbers, and week-ending dates;
- `hhsregion` with the ten HHS region identifiers and names;
- `labtypes` and `viruslist` category metadata.

The latest populated MMWR entry, not the final future placeholder in the
season, must determine the report week.

### Regional illness, positivity, and subtype counts

`POST /grasp/flu2/PostPhase02WHOGetData` accepts JSON such as:

```json
{
  "AppVersion": "Public",
  "SeasonID": 65,
  "RegionTypeID": 1,
  "RegionID": 1
}
```

The response's declared `data_structure` maps each MMWR identifier through lab
type, region type, and region to `PercentPositive`, `PercentWeightedILI`, and
virus counts. The verified public-health-laboratory categories include A(H3),
A(H1N1)pdm09, A unable to subtype, A subtyping not performed, B lineage
unspecified, B Victoria, and B Yamagata.

### Provider counts

`POST /grasp/flu2/PostPhase02LineChartDataDownload` returns the official
`FluView_LineChart_Data.csv`. Its columns include `NUM. OF PROVIDERS`, not the
legacy summary's `Jurisdictions` value. These fields are not semantically
interchangeable.

### Pediatric mortality

`GET /grasp/flu4/GetPhase04InitApp?appVersion=Public` returns JSON containing
current-report metadata and national pediatric mortality series, including
`ped_flu_reported` and `ped_flu_weekly`. The weekly series is organized by MMWR
week and virus category, while HHS-region data is season-level. It cannot
reproduce a pediatric-deaths value for every HHS-region row.

## Schema decision

The historical eleven-field schema is not supportable as a truthful live
contract:

- `NUM_JURIS` has no verified current equivalent; provider counts use different
  units and meaning.
- `A_NO_SUBTYPE` now spans at least two distinct official categories.
- `PED_DEATHS` is not available with the same week-by-HHS-region grain.

Keep the existing schema and HTML parser as a historical `v1` fixture contract.
The live adapter must publish an explicitly versioned `v2` schema with precise
current category names and separate national pediatric mortality provenance.
It must not silently place provider counts in `NUM_JURIS`, combine distinct
subtype categories, or copy national deaths into regional records.

## Required implementation stages

1. Add source-specific, bounded JSON and CSV transports without relaxing the
   legacy HTML fetcher. Allow only the reviewed CDC paths, methods, request
   bodies, query, response media types, and redirect policy.
2. Record minimized official fixtures with source URL, retrieval date, request
   shape, and response-field provenance.
3. Decode the nested FluView structure with duplicate, missing-field, numeric,
   week, season, and region validation.
4. Define and test the `v2` record schema before changing the default command.
5. Join only sources with matching MMWR identifiers and explicit missing-data
   behavior.
6. Preserve paired CSV/JSON preflight, staging, rollback, and cleanup behavior.

## Non-solutions

- Do not substitute `NUM. OF PROVIDERS` for `NUM_JURIS`.
- Do not copy national pediatric mortality into every regional row.
- Do not parse the dashboard's minified JavaScript as a runtime data source.
- Do not pin a static weekly report URL or scrape report prose.
- Do not globally permit arbitrary CDC queries or POST bodies.
