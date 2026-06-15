---
title: Duplicate Content-Type Charset Boundary
type: security
date: 2026-06-15
status: completed
execution: code
---

# Duplicate Content-Type Charset Boundary

## Summary

Reject CDC HTML responses whose single `Content-Type` field contains more than
one `charset` parameter. Avoid ambiguous first-value parsing before reading or
decoding the response body.

## Requirements

- R1. Inspect the parsed Content-Type parameter list rather than relying only
  on `get_content_charset()`.
- R2. Reject repeated charset parameters even when all values are identical.
- R3. Reject conflicting UTF-8 and non-UTF-8 charset parameters before reading
  the response body.
- R4. Continue accepting no charset or exactly one `utf-8`/`utf8` parameter.
- R5. Preserve status, URL, redirect, media type, content encoding, body size,
  declared length integrity, strict UTF-8 decoding, and parser contracts.
- R6. Add mutation-sensitive static coverage and truthful completed evidence.

## Scope Boundaries

- Do not reject unrelated unique Content-Type parameters.
- Do not add content negotiation, decompression, or alternate encodings.
- Do not make a live CDC request during validation.

## Implementation Units

1. Enforce charset parameter cardinality during Content-Type validation.
2. Add direct and fetch-order regression tests for identical and conflicting
   duplicate charset parameters.
3. Extend the maintenance baseline, run hostile mutations and all local gates,
   then audit the exact intended paths and generated artifacts.

## Verification

- Python 3.10.19, 3.12.8, and 3.14.0 each passed the full `make check` gate
  with all 39 offline tests.
- Direct validation rejects identical, conflicting, case-varied, and encoded
  duplicate charset parameters while preserving absent, plain, and RFC 2231
  encoded single UTF-8 declarations.
- Fetch-order coverage proves duplicate charset metadata fails before the first
  response-body read.
- Nine hostile mutations were rejected across parameter parsing,
  case-insensitive matching, cardinality, normalized value selection,
  identical/conflicting fixtures, no-read proof, and incomplete plan evidence.
- External-directory `make check`, in-memory compilation, shell syntax, exact
  diff, secret, and generated-artifact audits passed before delivery.
