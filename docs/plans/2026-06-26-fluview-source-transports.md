# FluView Source Transports Implementation Plan

Status: Completed

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add bounded source-specific transport functions for the four reviewed FluView JSON and CSV endpoints without changing the live default.

**Architecture:** Keep the legacy HTML fetcher intact. Add dedicated source functions that construct only reviewed requests and reuse response status, content encoding, byte-limit, and UTF-8 primitives; add narrow media-type, exact-final-URL, identifier, and JSON-object validation.

**Tech Stack:** Python 3 standard library, `urllib.request`, `json`, `unittest`, GNU Make, GitHub Actions.

---

### Task 1: Lock Request Shapes

**Files:**
- Modify: `tests/test_flushot.py`

**Step 1: Write failing GET transport tests**

Test exact phase 2/phase 4 URLs, GET methods, user agent, JSON response parsing,
and exact final-URL enforcement.

**Step 2: Run focused tests to verify RED**

Run the named tests with `python3 -m unittest` and expect missing functions.

**Step 3: Write failing POST transport tests**

Test exact phase 2 JSON and CSV URLs, POST methods, deterministic JSON bodies,
content type, identifier validation before opener construction, and parsed
returns.

**Step 4: Run focused tests to verify RED**

Expect missing source-specific functions.

### Task 2: Implement Shared Boundaries

**Files:**
- Modify: `flushot.py`
- Modify: `tests/test_flushot.py`

**Step 1: Add exact source URL constants and identifier validators**

Reject non-integer/bool season IDs and region IDs outside 1 through 10.

**Step 2: Add one-value media-type validation**

Accept only `application/json` with absent or UTF-8 charset for JSON and only
`application/octet-stream` for the reviewed CSV export.

**Step 3: Add strict JSON-object decoding**

Decode strict UTF-8, parse JSON without leaking response content, and reject
non-object roots.

**Step 4: Implement the four dedicated request functions**

Use the existing no-redirect opener, exact status, exact final URL, identity
encoding, bounded read, and strict decoding boundaries.

**Step 5: Run focused and full unit tests**

Expected: all source transport tests and existing tests pass.

### Task 3: Preserve Durable Contracts

**Files:**
- Modify: `scripts/check-baseline.sh`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `VISION.md`
- Modify: `CHANGES.md`
- Modify: `docs/plans/2026-06-26-fluview-source-transports.md`

**Step 1: Add mutation-sensitive source/test/plan contracts**

Require exact URLs, functions, validation messages, test names, unchanged
legacy default, synchronized guidance, and completed plan evidence.

**Step 2: Run `make check`**

Expected: specialized boundaries and all portable tests pass.

**Step 3: Run hostile mutations and hygiene checks**

Reject removed URL/method/media/identifier/root contracts; run compile, shell
syntax, gitleaks, and diff whitespace checks.

**Step 4: Commit and open a focused PR**

Push the exact validated head, invoke `$codex-review`, wait for hosted Python
and CodeQL gates, then merge only the exact green reviewed head.

## Verification Completed

- Nine focused regressions failed first because the source functions and
  constants did not exist; the CSV parameter regression separately failed
  while the media validator was intentionally removed, and the JSON parameter
  regression failed on an unreviewed `profile` parameter.
- All 78 portable tests passed after implementation.
- Live calls through all four source-specific functions passed against the
  reviewed CDC endpoints, including phase 2 metadata/region data, ILINet CSV,
  and phase 4 pediatric mortality data.
- `make check` passed all tests and specialized transport boundaries.
- The baseline found and drove a focused repair to the fetch-port static checker,
  which now inspects its named regression instead of imposing a repository-wide
  assertion count.
- A private-helper rename typo was rejected by the source contract and corrected
  before final validation.
- Repository-root and absolute-Makefile verification from `/tmp` passed.
- Ten isolated hostile mutations were rejected across exact URLs, final URLs,
  request bodies, identifier bounds, media types, JSON roots and parameters,
  the legacy default, public guidance, and plan status.
- In-memory Python compilation, shell syntax, current-tree gitleaks, and diff
  whitespace validation passed.
