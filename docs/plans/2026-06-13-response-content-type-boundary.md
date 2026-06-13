---
title: Response Content-Type Boundary
type: security
status: in_progress
date: 2026-06-13
---

# Response Content-Type Boundary

## Summary

Reject live CDC responses that are not declared HTML or that declare an
incompatible charset before reading and decoding their bodies.

## Priority

1. Validate response metadata before resource consumption.
2. Keep UTF-8 decoding aligned with accepted charset declarations.
3. Preserve URL, redirect, timeout, byte-limit, and offline parser behavior.

## Requirements

- R1. Live responses must include a `Content-Type` header.
- R2. The normalized media type must be exactly `text/html`.
- R3. A missing charset is accepted as the existing UTF-8 default; explicit
  `utf-8` and `utf8` declarations are accepted case-insensitively.
- R4. Other media types or charsets must raise a generic `ValueError` before
  the first response-body read.
- R5. Tests must cover missing type, non-HTML type, incompatible charset,
  accepted UTF-8 declarations, and guard-before-read ordering.
- R6. Static contracts and repository guidance must preserve the metadata
  boundary and completed verification evidence.

## Non-Goals

- Live CDC requests, content sniffing, transcoding other charsets, or parsing
  compressed response formats.
- Changing the trusted CDC host set, URL path policy, redirect policy, timeout,
  or 2 MiB response limit.
- Replacing `urllib`, `HTMLParser`, output formats, fixtures, or CI versions.
- Claiming current live CDC markup compatibility from offline tests.

## Implementation Units

### 1. Metadata Validator

Files: `flushot.py`

- Parse `Content-Type` with the standard-library email message API.
- Accept only HTML with absent or UTF-8-compatible charset metadata.
- Call the validator after final-URL validation and before body reads.

### 2. Focused Tests

Files: `tests/test_flushot.py`

- Extend fake responses with realistic HTML metadata.
- Cover accepted and rejected media/charset values and prove rejection occurs
  before `read()`.

### 3. Static Contracts and Guidance

Files: `scripts/check-baseline.sh`, `README.md`, `SECURITY.md`, `VISION.md`, `CHANGES.md`

- Require the validator, ordering, focused tests, docs, and completed evidence.

## Verification Plan

- Run focused tests and `make check`, `make lint`, `make test`, and `make build`.
- Remove the validator call, weaken the media-type allowlist, and move validation
  after body reading; the static or unit gates must reject each mutation.
- Run Python compilation, shell syntax, `git diff --check`, and intended-file
  secret scans.
- Take one bounded exact-head pull-request and CodeQL snapshot after push; do
  not poll.
