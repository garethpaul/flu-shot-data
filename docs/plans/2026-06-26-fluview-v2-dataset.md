# FluView V2 Dataset Implementation Plan

Status: Completed

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Preserve the regional yearweek join key and build a deterministic truthful `schema_version: 2` dataset from every validated FluView source.

**Architecture:** Extend the existing regional source model without breaking its fields, then add one pure join/builder function. The builder validates source identity, exact regional/ILINet coverage, duplicated ILI consistency, and mortality coverage before emitting explicit regional, laboratory, and mortality resources.

**Tech Stack:** Python 3 standard library, JSON, unittest, GNU Make, GitHub Actions.

---

### Task 1: Record Complete Join Fixture

**Files:**
- Create: `tests/fixtures/fluview_phase2_line_all_regions_2026-06-26.json`

Record exact full-response byte counts and SHA-256 values for all ten official
ILINet region responses while retaining the two weeks shared by the minimized
regional fixture.

### Task 2: Preserve Regional Join Key Test-First

**Files:**
- Modify: `tests/test_flushot.py`
- Modify: `flushot.py`

Write a failing assertion for `yearweek`, verify RED, then preserve the already
validated integer in each decoded regional week.

### Task 3: Define V2 Builder Test-First

**Files:**
- Modify: `tests/test_flushot.py`

Write happy-path schema, ordering, field-name, lab separation, mortality-grain,
and non-mutation tests. Add failures for season/current-week mismatch, missing
regions/weeks, duplicate/wrong region identity, ILI disagreement, catalog
drift, and mortality gaps. Verify all fail because the builder is absent.

### Task 4: Implement Minimal V2 Builder

**Files:**
- Modify: `flushot.py`

Add `build_fluview_v2_dataset` with strict source validation, deterministic
lists, explicit names, canonical ILI output, separate lab surveillance, and
grain-preserving mortality collections. Run focused and complete tests.

### Task 5: Preserve Durable Contracts

**Files:**
- Modify: `scripts/check-baseline.sh`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-fluview-v2-dataset.md`

Add fixture/schema/test/plan/guidance contracts, run full live 380-record
validation, external Make gates, hostile mutations, syntax checks, and
gitleaks. Commit/push, invoke `$codex-review` and skip only authentication
failure, wait for hosted Python/CodeQL, and merge only the exact reviewed SHA.

## Verification Completed

- RED: regional `yearweek` was absent, the v2 builder was absent, and malformed
  metric types escaped the intended validation boundary.
- GREEN: all 110 fixture-backed unit tests pass after preserving `yearweek`,
  adding the fail-closed builder, and normalizing malformed metrics to
  `ValueError`.
- Live: the reviewed CDC sources produced 380 regional records, 38 national
  mortality weeks, ten HHS season totals, and a season total of 184 deaths for
  current yearweek 202624.
- `make check` is the final repository gate after these plan and guidance
  records are complete.
