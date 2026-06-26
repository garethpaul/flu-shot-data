# FluView Phase 2 Regional Decoder Implementation Plan

Status: Completed

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Record a minimized official phase 2 regional fixture and add a strict full-response positional decoder for later `v2` design.

**Architecture:** Keep fetching, metadata normalization, and regional decoding separate. Validate the endpoint's exact declared positional structure and complete source response, then return a stable nested source model that preserves week, lab, region type, region, virus, metric, and flag provenance without selecting future publication fields.

**Tech Stack:** Python 3 standard library, JSON, unittest, GNU Make, GitHub Actions.

---

### Task 1: Record Official Regional Fixture

**Files:**
- Create: `tests/fixtures/fluview_phase2_region_2026-06-26.json`

**Step 1: Record exact source provenance**

Include the reviewed URL, POST method, deterministic request body, retrieval
timestamp, media type, full response byte count, and full response SHA-256.

**Step 2: Minimize the official response**

Retain two MMWR rows and their matching summary rows, the exact declared
structure, both lab types, all ten HHS regions, national region 0, and every
virus category using only decoder-consumed fields.

**Step 3: Validate the fixture**

Run `python3 -m json.tool tests/fixtures/fluview_phase2_region_2026-06-26.json`.
Expected: valid JSON with provenance matching the full official response.

### Task 2: Define Regional Decoder Test-First

**Files:**
- Modify: `tests/test_flushot.py`

**Step 1: Write happy-path normalization tests**

Assert the stable season/current-week envelope, two decoded weeks, separate lab
types, complete HHS and national records, exact representative counts and
metrics, normalized flags, and input non-mutation.

**Step 2: Run the focused test to verify RED**

Run: `python3 -m unittest tests.test_flushot.FluShotParserTests.test_parse_fluview_phase2_region_data_normalizes_declared_structure -v`
Expected: ERROR because `parse_fluview_phase2_region_data` does not exist.

**Step 3: Write malformed-source regressions**

Cover exact schema drift, malformed collection segments and row lengths,
duplicates, missing region types or coverage, catalog disagreement, invalid
counts, invalid metrics/flags, and missing current-week data.

**Step 4: Run focused tests to verify RED**

Expected: every new test errors on the missing decoder rather than fixture or
test setup mistakes.

### Task 3: Implement Minimal Strict Decoder

**Files:**
- Modify: `flushot.py`

**Step 1: Add exact structure and scalar validators**

Require the reviewed nested structure, strict nonnegative integers excluding
booleans, finite percentage metrics, and binary flags.

**Step 2: Validate response catalogs and weeks**

Require response MMWR and virus catalogs to agree with normalized metadata,
reject duplicates, and require the metadata current week in the response.

**Step 3: Decode every positional summary row**

Flatten separate lab collection segments only after validating them; require
lab types 1 and 2, region types 1 and 3, HHS regions 1-10, national region 0,
and the exact virus set for each lab.

**Step 4: Return the stable nested source model**

Preserve labs and region grains separately, sort identifier maps, normalize
source flags to booleans, and leave both inputs unchanged.

**Step 5: Run focused and full tests**

Expected: all new regressions and every existing test pass.

### Task 4: Preserve Durable Contracts

**Files:**
- Modify: `scripts/check-baseline.sh`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-fluview-phase2-regional-decoder.md`

**Step 1: Add fixture, source, test, plan, and guidance contracts**

Require exact provenance, fixture completeness, decoder source/test markers,
unchanged legacy default, synchronized safety guidance, and completed plan
evidence.

**Step 2: Run local and external verification**

Run `make check`, repository-root Make targets, and absolute-Makefile checks
from `/tmp`. Expected: all portable tests and static contracts pass.

**Step 3: Run live and hostile validation**

Decode a current official response and reject isolated structure, fixture,
catalog, positional, count, guidance, and plan mutations.

**Step 4: Review and merge exact green head**

Commit and push the focused branch, invoke `$codex-review` and skip only an
authentication failure, wait for hosted Python and CodeQL, then merge only the
exact reviewed head SHA.

## Verification Completed

- Six focused decoder tests produced 21 expected errors on the missing API,
  then passed after the strict positional decoder was implemented.
- A separate catalog-label regression failed against the first implementation
  and passed after the complete response catalog was matched to metadata.
- The minimized 66,225-byte fixture records the exact request, response date,
  media type, original 1,166,773-byte length, and SHA-256.
- All 92 portable tests passed.
- The full current official response decoded 38 weeks, both lab types, all ten
  HHS regions per lab, national region 0, and every expected virus category.
- `make check`, `make lint`, `make test`, and `make build` passed.
- Repository-root and absolute-Makefile verification from `/tmp` passed.
- Ten isolated hostile provenance, fixture completeness, schema, decoder,
  regression, guidance, and plan mutations were rejected.
- JSON syntax, in-memory Python compilation, shell syntax, current-tree
  gitleaks, and diff whitespace validation passed.
