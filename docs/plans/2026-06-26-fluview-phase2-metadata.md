# FluView Phase 2 Metadata Implementation Plan

Status: Completed

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Record a minimized official phase 2 initialization fixture and add strict normalized metadata decoding for later v2 joins.

**Architecture:** Keep transport and decoding separate. Tests load a provenance-bearing minimized fixture, while production accepts the raw response object and returns a new stable dictionary after collection, identifier, duplicate, string, date, relationship, and completeness validation.

**Tech Stack:** Python 3 standard library, JSON, datetime, unittest, GNU Make, GitHub Actions.

---

### Task 1: Record Official Fixture

**Files:**
- Create: `tests/fixtures/fluview_phase2_init_2026-06-26.json`

**Step 1: Record provenance**

Include exact source URL, method, retrieval timestamp, content type, full response byte count, and full response SHA-256.

**Step 2: Minimize the response**

Retain two seasons, representative current-season MMWR rows including year crossover and latest week, all ten HHS regions, both lab types, and every current virus catalog entry using only decoder-consumed fields.

**Step 3: Validate JSON and fixture contracts**

Run `python3 -m json.tool` and a focused provenance assertion.

### Task 2: Define Decoder Behavior Test-First

**Files:**
- Modify: `tests/test_flushot.py`

**Step 1: Write happy-path and order-independence tests**

Assert normalized current season/week, complete region map, lab map, virus map,
input non-mutation, and order-independent selection.

**Step 2: Run focused tests to verify RED**

Expected: missing `parse_fluview_phase2_metadata`.

**Step 3: Write malformed-structure regressions**

Cover missing/non-list collections, duplicate IDs, invalid booleans/ranges,
invalid date/yearweek, incomplete/noncanonical regions, empty strings, unknown
lab references, disabled-only seasons, and missing current-season weeks.

**Step 4: Run focused tests to verify RED**

Expected: missing decoder.

### Task 3: Implement Minimal Normalizer

**Files:**
- Modify: `flushot.py`

**Step 1: Add private collection and scalar validators**

Require lists of objects, strict integers excluding booleans, and non-empty
strings.

**Step 2: Normalize seasons and MMWR weeks**

Reject duplicates and invalid metadata; select the highest enabled season ID
and greatest validated current-season MMWR ID.

**Step 3: Normalize regions, lab types, and viruses**

Require complete canonical HHS regions, required lab IDs, unique virus IDs, and
known lab references.

**Step 4: Run focused and full tests**

Expected: decoder regressions and all existing tests pass.

### Task 4: Preserve Durable Contracts

**Files:**
- Modify: `scripts/check-baseline.sh`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-fluview-phase2-metadata.md`

**Step 1: Add fixture/source/test/plan contracts**

Require exact provenance, minimized fixture fields, decoder source and tests,
unchanged default, synchronized guidance, and completed plan evidence.

**Step 2: Run local and external `make check`**

Expected: all tests and static contracts pass.

**Step 3: Run live fetch-to-decoder smoke and hostile mutations**

Verify current official data decodes, then reject fixture, duplicate, date,
region, relationship, guidance, and plan mutations.

**Step 4: Commit, push, review, and merge exact green head**

Invoke `$codex-review`; skip only authentication failure. Wait for hosted Python
and CodeQL, then merge only the exact verified head.

## Verification Completed

- Six focused decoder tests produced 37 expected errors on the missing API,
  then passed after strict normalization was implemented.
- The minimized 4,199-byte fixture records the exact source URL, response date,
  media type, original 357,473-byte length, and SHA-256.
- All 85 portable tests passed.
- The full current official phase 2 response normalized to season 2025-26,
  MMWR week 24 ending 2026-06-20, ten HHS regions, two lab types, and twelve
  virus categories.
- `make check` remains the required complete offline gate.
- Repository-root and absolute-Makefile verification from `/tmp` passed.
- Ten hostile provenance, fixture completeness, selection, duplicate, date,
  region, relationship, guidance, and plan mutations were rejected.
- JSON syntax, in-memory Python compilation, shell syntax, current-tree
  gitleaks, and diff whitespace validation passed.
