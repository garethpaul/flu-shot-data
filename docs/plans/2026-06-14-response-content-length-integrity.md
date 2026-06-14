---
title: Response Content-Length Integrity
type: security
date: 2026-06-14
status: completed
execution: code
---

# Response Content-Length Integrity

## Summary

Require a present CDC `Content-Length` declaration to match the bounded bytes
actually received. Preserve optional headers, strict field syntax, duplicate
rejection, the 2 MiB streamed ceiling, strict UTF-8 decoding, and offline tests.

## Problem Frame

The current fetch boundary validates one canonical decimal `Content-Length`
and rejects values above the configured maximum before reading. It does not
retain the parsed value, so a response that ends before the declared length or
delivers more bytes than a smaller declaration can still reach HTML parsing as
long as the global streamed ceiling is not exceeded. A present length is an
integrity assertion about the enclosed octets and should fail closed when the
received byte count differs.

## Requirements

- A missing `Content-Length` must continue to allow bounded streaming.
- A valid present declaration must be returned as an integer after existing
  syntax, duplicate, and maximum-size validation.
- The final received byte count must equal a present declaration.
- Both truncated bodies and bodies longer than their declaration must fail with
  a generic error that does not include response content.
- The independent streamed maximum must continue to reject oversized bodies.
- Focused tests and the repository gate must reject removal of either mismatch
  direction, the optional-header behavior, or completed verification evidence.

## Key Technical Decisions

- Compare after bounded streaming so the global ceiling remains authoritative
  even when a declaration is dishonest.
- Keep `Content-Length` optional; only a present validated declaration creates
  an exact byte-count requirement.
- Use one generic mismatch error for short and long bodies so received content
  and internal parser state are not exposed.
- Preserve the existing public fetch and output APIs.

## Implementation Units

### 1. Enforce declared-length equality

**Files:** `flushot.py`, `tests/test_flushot.py`

Return the validated optional length from `validate_content_length`, retain it
inside `read_response_bytes`, and compare it with the final accumulated byte
count before returning the body.

Test-first scenarios:

- No declaration and an in-limit body still succeeds.
- An exact declaration still succeeds.
- A body shorter than its declaration fails.
- A body longer than its declaration fails even when below the global maximum.
- Existing malformed, duplicate, preflight-oversize, and streamed-oversize
  cases retain their rejection order and behavior.

### 2. Preserve the security contract

**Files:** `scripts/check-content-length-integrity.py`,
`scripts/check-baseline.sh`, `README.md`, `SECURITY.md`, `VISION.md`,
`CHANGES.md`, `AGENTS.md`,
`docs/plans/2026-06-14-response-content-length-integrity.md`

Add a focused static contract for the optional parsed length, post-stream byte
comparison, executable regressions, guidance, and completed evidence. Run
isolated mutations that remove the short-body check, long-body check, optional
header behavior, test coverage, and completed plan evidence.

## Scope Boundaries

- Do not change the CDC URL, redirect, status, media-type, encoding, timeout,
  charset, parser, CSV, or JSON policies.
- Do not change the 2 MiB limit or chunk size.
- Do not add live network requests or third-party dependencies.
- Do not claim transport completeness beyond the bounded bytes exposed by the
  response object.

## Risks

- Some nonstandard response doubles might declare a length but expose a
  different body; they will now fail intentionally instead of being parsed.
- Standard-library HTTP framing can detect some truncation itself, but the
  explicit application check keeps the invariant testable and fail-closed for
  compatible response objects.

## Verification

- Focused unit tests for exact, missing, truncated, and overlong declarations.
- Root and external-directory `make check`.
- Isolated hostile mutations for both mismatch directions and evidence drift.
- `git diff --check`, explicit generated-artifact inspection, and changed-line
  credential-pattern inspection.

## Completed Verification

- All 37 offline tests passed, including focused unit tests for missing, exact,
  truncated, overlong, malformed, duplicate, and globally oversized response
  lengths.
- The original response-length checker and the new integrity checker passed.
- Five isolated hostile mutations were rejected for the short-body direction,
  long-body direction, optional-header behavior, executable regression names,
  and completed plan evidence.
- Root and external-directory `make check` passed after the completed plan and
  repository guidance were in their final state.

## Sources

- RFC 9110, Section 8.6, `Content-Length`:
  https://www.rfc-editor.org/rfc/rfc9110#section-8.6
