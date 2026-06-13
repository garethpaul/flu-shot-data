---
title: Strict UTF-8 Response Decoding
type: security
status: planned
date: 2026-06-13
---

# Strict UTF-8 Response Decoding

## Summary

Reject malformed live CDC response bytes instead of silently replacing invalid
UTF-8 sequences before the HTML parser sees them.

## Priority

1. Keep decoded text faithful to the UTF-8 response contract.
2. Fail closed with a generic error when response bytes are malformed.
3. Preserve the existing URL, redirect, metadata, timeout, byte-limit, parser,
   and output boundaries.

## Requirements

- R1. Live response bodies must use strict UTF-8 decoding after bounded reading.
- R2. `errors="replace"`, `errors="ignore"`, or equivalent lossy decoding must
  not be used for CDC response data.
- R3. `UnicodeDecodeError` must become a generic `ValueError` that does not
  include response bytes, decoded fragments, URLs, or exception details.
- R4. A focused test must accept valid UTF-8 and reject malformed bytes through
  `fetch_html` after exactly one bounded read attempt.
- R5. Existing content-type-before-read and final-URL-before-read ordering must
  remain unchanged.
- R6. Static contracts must reject lossy decoding, missing exception handling,
  weakened tests, decode-before-bounds ordering, and incomplete plan evidence.
- R7. README, SECURITY, VISION, CHANGES, and AGENTS must describe the strict
  decode boundary without claiming live CDC compatibility.

## Non-Goals

- Supporting or transcoding ISO-8859-1, Windows-1252, UTF-16, compressed bodies,
  or content sniffing.
- Changing the trusted CDC host set, URL path policy, redirect policy, timeout,
  response-size limit, parser rules, output schema, or generated files.
- Making a live CDC request or publishing generated data.
- Adding dependencies or changing the Python compatibility matrix.

## Implementation Units

### 1. Strict Decode Helper

Files: `flushot.py`

- Decode bounded bytes with strict UTF-8 semantics.
- Translate decode failures to a generic repository-specific `ValueError`.

### 2. Focused Tests

Files: `tests/test_flushot.py`

- Preserve a successful multibyte UTF-8 response.
- Reject malformed UTF-8 through the complete fetch path without leaking body
  content in the error.

### 3. Static Contracts

Files: `scripts/check-baseline.sh`

- Require strict decoding, generic error translation, focused tests, ordering,
  documentation, and completed verification evidence.

### 4. Repository Guidance

Files: `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`, `AGENTS.md`

- Record strict decode behavior and the continuing offline/live-validation
  distinction.

## Verification Plan

- Run focused decode tests and `make check`, `make lint`, `make test`, and
  `make build`.
- Restore replacement decoding, remove exception translation, weaken malformed
  byte coverage, and move decode before bounded reading; the unit or static
  gates must reject each mutation.
- Run Python compilation, shell syntax, `git diff --check`, and intended-file
  secret scans.
- Take bounded exact-head pull-request, workflow, and code-scanning snapshots
  after push; do not start a watch loop.

## Work Completed

Pending implementation.

## Verification Completed

Pending implementation and verification.
