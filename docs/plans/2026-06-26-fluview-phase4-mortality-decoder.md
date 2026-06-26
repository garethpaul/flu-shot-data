# FluView Phase 4 Mortality Decoder Implementation Plan

Status: Completed

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Record a minimized official phase 4 fixture and add strict grain-preserving pediatric mortality decoding.

**Architecture:** Keep phase 4 transport and decoding separate. Normalize national weekly mortality through the current report week and HHS season totals into separate structures, validating their shared season total without fabricating regional weekly values.

**Tech Stack:** Python 3 standard library, JSON, datetime, unittest, GNU Make, GitHub Actions.

---

### Task 1: Record Official Phase 4 Fixture

**Files:**
- Create: `tests/fixtures/fluview_phase4_mortality_2026-06-26.json`

**Step 1: Record exact source provenance**

Include URL, GET method, retrieval timestamp, media type, full byte count, and
full SHA-256.

**Step 2: Minimize consumed current-season data**

Retain one season, 53 week rows, 265 weekly-virus rows, four virus categories,
one report record, and ten HHS season rows.

**Step 3: Validate fixture syntax and counts**

Run `python3 -m json.tool` and focused provenance/count assertions.

### Task 2: Define Decoder Test-First

**Files:**
- Modify: `tests/test_flushot.py`

**Step 1: Write happy-path, non-mutation, and order tests**

Assert report metadata, 38 published national weeks, exact virus counts,
separate ten-region season totals, equal total 184, and unchanged inputs.

**Step 2: Run focused tests to verify RED**

Expected: missing `parse_fluview_phase4_mortality`.

**Step 3: Write hostile source regressions**

Cover collection shape, duplicates, catalog/report mismatch, week metadata,
five-row completeness, count arithmetic, future values, region coverage/rates,
and total disagreement.

### Task 3: Implement Minimal Strict Decoder

**Files:**
- Modify: `flushot.py`

**Step 1: Validate current season, report, and virus catalog**

Bind the response to normalized phase 2 season/current-week metadata.

**Step 2: Normalize all current-season weekly groups**

Require IDs 0-4, count relationships, category sums, and zero future rows;
publish only weeks through the current report week.

**Step 3: Normalize HHS season totals**

Require regions 1-10, nonnegative counts/rates, and equality with the national
season total.

**Step 4: Run focused and full tests**

Expected: all new and existing tests pass.

### Task 4: Preserve Durable Contracts

**Files:**
- Modify: `scripts/check-baseline.sh`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-fluview-phase4-mortality-decoder.md`

**Step 1: Add fixture, decoder, test, plan, and guidance contracts**

Require exact provenance, minimized completeness, source/test markers, grain
separation, synchronized guidance, and completed plan evidence.

**Step 2: Run local, live, external, and hostile validation**

Run all Make gates, full live decoding, syntax checks, gitleaks, and ten
isolated mutations.

**Step 3: Review and merge exact green head**

Commit/push, invoke `$codex-review` and skip only authentication failure, wait
for hosted Python and CodeQL, then merge only the exact reviewed SHA.
