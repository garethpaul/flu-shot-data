---
title: Response Content-Length Boundary
type: security
date: 2026-06-14
status: planned
execution: code
---

# Response Content-Length Boundary

## Summary

Reject ambiguous or malformed CDC `Content-Length` metadata before reading the
response body while preserving the existing streamed byte limit.

## Problem Frame

The fetcher currently reads `Content-Length` through a single-value accessor.
Duplicate field lines or comma-combined values can therefore be interpreted
inconsistently by intermediaries even though the streamed body remains bounded.

## Requirements

- **R1.** A response may omit `Content-Length`, but a present value must be one
  non-empty ASCII decimal field.
- **R2.** Duplicate field lines, comma-combined values, signs, whitespace,
  negatives, and non-decimal syntax must fail before the first body read.
- **R3.** A valid declared length above the configured maximum must continue to
  fail before the first body read.
- **R4.** The streamed byte limit must continue to protect responses without a
  declared length or with a smaller dishonest declaration.
- **R5.** The static gate and completed plan must preserve executable regression
  coverage and actual verification evidence.

## Key Technical Decisions

- **Fail closed on repeated values:** RFC 9110 allows recipients to reject
  repeated identical lengths, which avoids normalization ambiguity here.
- **Validate field syntax before integer conversion:** `int()` accepts signs and
  surrounding whitespace that are outside the decimal field grammar.
- **Keep streaming as the authority:** declared metadata is an early rejection
  signal, not a substitute for counting received bytes.

## Scope Boundaries

- Do not change the two-megabyte response limit or chunk size.
- Do not allow compressed responses, redirects, alternate media types, or
  non-200 statuses.
- Do not add live CDC requests to the offline test suite.

## Implementation Units

### U1. Validate response length metadata

**Goal:** Parse `Content-Length` as one canonical decimal field before reading.

**Requirements:** R1, R2, R3, R4

**Dependencies:** None

**Files:** `flushot.py`, `tests/test_flushot.py`

**Approach:** Read all field instances when supported, reject more than one,
require ASCII digits only, compare the parsed value with the configured limit,
and retain the existing streamed count.

**Execution note:** Add the malformed and duplicate metadata tests before
changing the parser.

**Test scenarios:**

- Missing `Content-Length` streams successfully within the limit.
- One decimal value at the limit is accepted.
- Duplicate identical and conflicting fields are rejected before reading.
- Comma-combined, signed, padded, empty, negative, and non-decimal values are
  rejected before reading.
- A smaller declared length followed by an oversized body is still rejected by
  the streamed limit.

**Verification:** Focused response-length tests prove metadata rejection order
and streamed enforcement.

### U2. Preserve the fail-closed contract

**Goal:** Make weakening the response-length boundary fail the repository gate.

**Requirements:** R5

**Dependencies:** U1

**Files:** `scripts/check-content-length-boundary.py`,
`scripts/check-baseline.sh`, `README.md`, `SECURITY.md`, `VISION.md`,
`CHANGES.md`,
`docs/plans/2026-06-14-002-security-response-content-length-boundary-plan.md`

**Approach:** Add a focused static contract for all-value retrieval, decimal
syntax, pre-read ordering, executable tests, guidance, and completed evidence.

**Test scenarios:**

- Removing duplicate detection, decimal syntax validation, pre-read ordering,
  executable coverage, or completed evidence fails an isolated mutation.
- Root and external-directory `make check` both pass.

**Verification:** Full tests, static contracts, hostile mutations, and final
artifact and secret audits pass on the intended diff.

## Risks And Dependencies

- Some servers emit repeated identical lengths; this client intentionally
  rejects them for a smaller trusted response surface.
- Header containers without `get_all` can expose only one value; the fallback
  remains necessary for simple fakes and compatible standard-library objects.

## Sources And Research

- RFC 9110, Section 8.6, Content-Length:
  https://www.rfc-editor.org/rfc/rfc9110#section-8.6

## Verification

Pending implementation.
