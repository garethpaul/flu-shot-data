# FluView V2 Dataset Design

Status: Completed

## Goal

Define and build the first truthful versioned dataset from the validated
FluView sources without changing the historical default command or `v1` files.

## Evidence

- Phase 2 regional JSON and ILINet CSV both cover 38 current-season weeks for
  all ten HHS regions.
- Across all 380 region/week combinations, ILINet weighted and unweighted ILI
  exactly match the phase 2 regional values for both lab collections.
- Phase 2 regional JSON contains distinct public-health and clinical lab
  percent-positive and virus-count data that must not be flattened together.
- ILINet provider counts are complete but are not jurisdiction counts.
- Phase 4 provides national weekly mortality and HHS season totals, not HHS
  weekly mortality.
- The regional decoder validates `yearweek` but currently discards it, so it
  must preserve that join key before a safe join can be built.

## Dataset Contract

`build_fluview_v2_dataset(metadata, regional_data, ilinet_by_region, mortality)`
returns a JSON-compatible object with `schema_version: 2` and four resources:

### Season

`season` contains `id`, `label`, and a `current_week` object with `mmwr_id`,
`yearweek`, `week_number`, and `week_end`.

### Virus categories

`laboratory_virus_categories` is a sorted list containing `id`, `description`, `label`,
`lab_type_id`, and `lab_type`. It is the shared catalog referenced by regional
lab count records.

### Regional weekly

`regional_weekly` is sorted by MMWR ID then HHS region ID. Each record contains:

- week and HHS-region identity;
- one canonical `ili` object with age-group visits, total ILI visits, total
  patients, provider count, weighted/unweighted percentages, baseline, and
  explicit boolean flags;
- `laboratory_surveillance.public_health` and `.clinical`, each preserving its
  own percent-positive/A/B fields and sorted virus counts.

Virus counts use explicit `weekly_positive_count`,
`three_week_positive_count`, and `season_cumulative_positive_count` names.

### Pediatric mortality

`pediatric_mortality` contains a documented scope string, national weekly
records, its own phase 4 virus category list, separate HHS season totals, and
the verified season total. National weekly records preserve previously
reported, newly reported, and total deaths per virus category. Phase 4 category
IDs are deliberately not shared with the laboratory catalog because the same
integers have different meanings. No regional weekly death field exists.

## Join Policy

- Require schema source season/current-week identity to agree.
- Require all ten ILINet regions and exact regional `yearweek` coverage.
- Require all regional weeks to exist in national mortality.
- Require phase 2 public-health and clinical ILI values to agree with each
  other and with ILINet before emitting one canonical ILI object.
- Fail closed on missing source rows, duplicate identifiers, catalog drift,
  inconsistent region IDs, or metric disagreement. Missing data is an error,
  not an implicit zero or omitted field.
- Preserve deterministic ordering and do not mutate decoded inputs.

## Alternatives Rejected

### One flat legacy-shaped record

Rejected because it would require false provider/jurisdiction equivalence,
combining distinct virus categories, and copying national mortality into HHS
rows.

### Separate unjoined source dumps

Rejected as the final contract because consumers would repeatedly reimplement
the same key, completeness, and metric-consistency rules.

### Nullable partial joins

Rejected for the initial contract because all verified current sources are
complete. Fail-closed publication makes upstream drift visible rather than
silently degrading a public-health dataset.

## Validation

Tests use official minimized regional, all-region ILINet, metadata, and phase 4
fixtures. They cover the complete schema, deterministic ordering, non-mutation,
preserved yearweek, source identity, coverage, lab/catalog separation, metric
equality, mortality grain, and failure on missing or inconsistent joins. A
full live build must produce 380 regional records and 38 national mortality
weeks before exact-head merge.

## Result

Implemented the reviewed contract as a pure JSON-compatible builder. The
fixture-backed suite passes 110 tests, and a live build produced 380 regional
weekly records, 38 national mortality weeks, ten HHS season totals, and the
verified 184-death season total for MMWR yearweek 202624.
