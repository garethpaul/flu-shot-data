---
title: Response Content Encoding Boundary
type: security
status: planned
date: 2026-06-13
---

# Response Content Encoding Boundary

## Summary

Reject compressed or otherwise transformed CDC response bodies before reading
them because this dependency-free client supports only absent or explicit
`identity` content encoding.

## Priority

1. Make the unsupported response-transformation boundary explicit and early.
2. Prevent encoded bytes from reaching bounded UTF-8 decoding or HTML parsing.
3. Preserve URL, redirect, media type, charset, timeout, byte-limit, parser,
   and output behavior.

## Requirements

- R1. Live responses may omit `Content-Encoding` or declare exactly
  case-insensitive `identity` with surrounding whitespace ignored.
- R2. Blank, gzip, deflate, Brotli, comma-separated, and other encoding values
  must fail with a generic `ValueError`.
- R3. Encoding metadata must be validated after final URL and content-type
  validation but before the first response-body read.
- R4. Focused fetch tests must prove accepted and rejected values and assert
  rejected responses are never read.
- R5. Static contracts must reject missing validation, permissive allowlists,
  read-before-validation ordering, weakened tests, documentation drift, or
  incomplete plan evidence.
- R6. README, SECURITY, VISION, CHANGES, and AGENTS must describe the
  identity-only boundary without claiming live CDC compatibility.
- R7. The completed plan must record actual focused, full-suite, mutation, and
  hosted verification evidence.

## Non-Goals

- Decompressing gzip, deflate, Brotli, or any other content encoding.
- Sending an `Accept-Encoding` negotiation header.
- Changing the trusted CDC host set, URL path policy, redirect policy, timeout,
  response-size limit, content-type/charset policy, parser, or output schema.
- Making a live CDC request or publishing generated data.
- Adding dependencies or changing the Python compatibility matrix.

## Implementation Units

### 1. Encoding Metadata Validator

Files: `flushot.py`

- Accept absent or explicit identity encoding and reject every other value.
- Invoke the validator before bounded response reading.

### 2. Focused Tests

Files: `tests/test_flushot.py`

- Cover absent and case-normalized identity values through the complete fetch
  path.
- Cover blank and transformed values while proving no body read occurs.

### 3. Static Contracts

Files: `scripts/check-baseline.sh`

- Require the exact allowlist, fetch ordering, focused tests, documentation,
  and completed verification evidence.

### 4. Repository Guidance

Files: `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`, `AGENTS.md`

- Record the identity-only transport representation and continuing offline/live
  validation distinction.

## Verification Plan

- Run focused content-encoding tests and `make check`, `make lint`, `make test`,
  and `make build`.
- Remove the validator, allow gzip, move validation after reading, weaken the
  no-read assertion, and regress plan evidence; each mutation must be rejected.
- Run Python compilation, shell syntax, `git diff --check`, and intended-file
  secret/artifact scans.
- Take bounded exact-head pull-request, workflow, and code-scanning snapshots
  after push; do not start a watch loop.

## Work Completed

Pending implementation.

## Verification Completed

Pending implementation and verification.
