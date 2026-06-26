# FluView Phase 2 Metadata Design

Status: Completed

## Problem

The bounded phase 2 initialization transport returns an untrusted JSON object
whose arrays are ordered and shaped by the upstream dashboard. Later v2 work
needs stable season, week, HHS-region, lab-type, and virus-category metadata,
but directly indexing the live payload would allow missing fields, duplicates,
invalid dates, future placeholders, and order changes to corrupt joins.

## Fixture Provenance

Record a minimized fixture under `tests/fixtures` with a top-level provenance
object and a minimized `response` object. Provenance records the exact source
URL, GET method, retrieval timestamp, response media type, original byte count,
and SHA-256 of the full official response. The minimized response retains every
field consumed by the decoder, all ten HHS regions, both lab types, and the full
current virus catalog while omitting unrelated dashboard presentation data.

The fixture is evidence for structure and values at retrieval time, not a
runtime fallback or a promise that the upstream response is immutable.

## Options Considered

1. Return the raw upstream dictionary. This preserves all fields but provides no
   stable ownership boundary or validation for later joins.
2. Define several dataclasses. This is strongly typed but adds a public object
   model before the v2 output schema is decided.
3. Return a normalized dictionary with documented stable keys. This matches the
   existing dependency-free code style, is easy to serialize in tests, and can
   be replaced or wrapped when the v2 schema is finalized.

## Decision

Add `parse_fluview_phase2_metadata(payload)` returning:

- `season_id` and `season_label` for the highest enabled unique season ID;
- `week_id`, `week_number`, and ISO `week_end` for the greatest unique MMWR ID
  belonging to that season;
- `hhs_regions`, a numeric-key dictionary containing exactly active regions 1
  through 10 with canonical `Region N` names;
- `lab_types`, a numeric-key dictionary requiring unique public-health ID 1 and
  clinical ID 2 names;
- `viruses`, a numeric-key dictionary of unique positive virus IDs with
  non-empty description, label, and a known lab-type ID.

The decoder does not trust array order. It rejects booleans as integers,
duplicate identifiers, missing required collections or fields, disabled-only
seasons, missing current-season weeks, invalid week ranges, malformed ISO
dates, inconsistent `yearweek`, noncanonical regions, unknown lab references,
and empty strings. It returns fresh normalized values and never mutates input.

## Latest Week Semantics

The phase 2 initialization response currently includes only populated MMWR
rows through the report week, even though season metadata contains future range
identifiers. Select the greatest validated MMWR ID in the current season;
never derive the current report week from the season's range fields.

## Validation

Tests load the provenance fixture's `response` and cover the normalized happy
path plus unordered arrays, duplicates, missing collections, invalid IDs,
invalid dates/week metadata, incomplete HHS coverage, and unknown virus lab
references. The full offline gate, live fetch-to-decoder smoke, fixture hash
contracts, hostile mutations, and hosted Python/CodeQL must pass.
