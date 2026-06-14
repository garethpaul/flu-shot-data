---
title: CDC Response Status Boundary
type: security
status: completed
date: 2026-06-14
---

# CDC Response Status Boundary

## Summary

Require an exact HTTP 200 CDC response before final-URL validation, response
metadata inspection, body reads, decoding, or parsing. This rejects partial and
other successful-status variants that `urllib` may otherwise return normally.

## Prioritized Engineering Tasks

1. Add a focused response status validator.
2. Invoke it first inside the opened-response boundary.
3. Add representative non-200 regression coverage that proves no body read.
4. Add source-order, test-contract, and synchronized documentation checks.

## Requirements

- R1. Only status 200 may continue through the live CDC fetch path.
- R2. Status validation must precede final URL and metadata validation.
- R3. Rejected statuses must not read or expose response body content.
- R4. Existing redirect, URL, content type, content encoding, byte limit, and
  strict UTF-8 boundaries must remain unchanged.
- R5. Static contracts must prove guard ordering and representative statuses.

## Non-Goals

- Retrying transient HTTP failures.
- Following redirects or accepting partial content.
- Making a live CDC request from the offline maintenance gate.

## Verification

- The focused regression rejected 199, 201, 204, 206, 301, 400, 404, 429, and
  500 before final-response validation or body reads.
- Seven hostile mutations were rejected across the exact status, validator use,
  pre-metadata ordering, status matrix, no-read assertion, final-URL boundary,
  and completed-plan evidence.
- `make check`, `make lint`, `make test`, and `make build` passed the offline
  maintenance baseline from the repository root and `make check` passed through
  the absolute Makefile path from an external working directory.
- No live CDC request was made; all network behavior used deterministic fakes.
- Exact intended-path, generated-artifact, whitespace, conflict-marker,
  workflow/dependency preservation, and changed-line credential-pattern audits
  passed.
