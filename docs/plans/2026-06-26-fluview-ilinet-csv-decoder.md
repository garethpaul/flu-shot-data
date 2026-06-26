# FluView ILINet CSV Decoder Implementation Plan

Status: Completed

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Record a minimized official ILINet CSV fixture and add strict typed decoding for truthful regional provider and visit counts.

**Architecture:** Keep transport, CSV source decoding, and later cross-source joins separate. Validate the exact reviewed CSV envelope and row arithmetic, then return a stable `yearweek`-keyed source model tagged with season and region provenance.

**Tech Stack:** Python 3 standard library, csv, decimal, unittest, GNU Make, GitHub Actions.

---

### Task 1: Record Official CSV Fixture

**Files:**
- Create: `tests/fixtures/fluview_phase2_line_region1_2026-06-26.json`

**Step 1: Record exact provenance**

Include the reviewed URL, POST method and body, retrieval timestamp, response
media type, full response byte count, and full response SHA-256.

**Step 2: Minimize source text**

Retain the exact title/header plus first, year-crossover, and current rows.

**Step 3: Validate JSON and embedded CSV**

Run `python3 -m json.tool` and a focused provenance assertion.

### Task 2: Define Decoder Test-First

**Files:**
- Modify: `tests/test_flushot.py`

**Step 1: Write normalization and non-mutation tests**

Assert typed identifier envelope, sorted `yearweek` rows, representative
provider/visit counts and percentages, and unchanged source text.

**Step 2: Run focused test to verify RED**

Run the named unittest and expect an AttributeError for the absent parser.

**Step 3: Write malformed-source regressions**

Cover exact title/header drift, blank/extra rows, duplicates, malformed
integers, invalid year/week, reserved-column content, count arithmetic,
percentage mismatch, and invalid identifiers.

**Step 4: Run all focused regressions to verify RED**

Expected: failures arise from the absent decoder, not fixture setup.

### Task 3: Implement Minimal Strict Decoder

**Files:**
- Modify: `flushot.py`

**Step 1: Add exact CSV envelope constants and scalar parsers**

Require ASCII-decimal integer fields and finite decimal percentage fields.

**Step 2: Validate every source row**

Reject duplicate `yearweek` keys, invalid ranges, reserved-column content, and
count/percentage arithmetic disagreement.

**Step 3: Return sorted typed source rows**

Preserve provider semantics and all populated age/count/ILI fields without
adding legacy aliases or cross-source joins.

**Step 4: Run focused and full tests**

Expected: all new regressions and existing tests pass.

### Task 4: Preserve Durable Contracts

**Files:**
- Modify: `scripts/check-baseline.sh`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-fluview-ilinet-csv-decoder.md`

**Step 1: Add fixture, decoder, test, plan, and guidance contracts**

Require exact provenance, minimized fixture shape, source/test markers,
unchanged legacy semantics, synchronized guidance, and completed plan evidence.

**Step 2: Run local and external verification**

Run `make check`, aliases, repository-root Make, and absolute-Makefile checks.

**Step 3: Run live and hostile validation**

Decode the full current CSV and reject isolated provenance, envelope, numeric,
arithmetic, semantic, guidance, and plan mutations.

**Step 4: Review and merge exact green head**

Commit and push, invoke `$codex-review` and skip only an authentication failure,
wait for hosted Python and CodeQL, then merge only the exact reviewed SHA.

## Verification Completed

- Five focused decoder tests produced 18 expected errors on the missing API,
  then passed after the strict CSV decoder was implemented.
- An additional excessive-precision regression escaped as
  `decimal.InvalidOperation`, then passed after percentage text was bounded and
  normalized to `ValueError`.
- The minimized 1,381-byte fixture records the exact request, response date,
  media type, original 2,583-byte length, and SHA-256.
- All 98 portable tests passed.
- The full current official CSV decoded 38 unique yearweeks from 202540 through
  202624; Region 1's current provider count normalized to 270.
- `make check`, `make lint`, `make test`, and `make build` passed.
- Repository-root and absolute-Makefile verification from `/tmp` passed.
- Ten isolated hostile provenance, fixture envelope, row completeness, source,
  output, regression, guidance, and plan mutations were rejected.
- JSON syntax, in-memory Python compilation, shell syntax, current-tree
  gitleaks, and diff whitespace validation passed.
