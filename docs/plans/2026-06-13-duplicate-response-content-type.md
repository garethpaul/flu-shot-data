---
title: Duplicate Response Content Type Rejection
type: security
status: planned
date: 2026-06-13
---

# Duplicate Response Content Type Rejection

## Summary

Reject CDC responses with multiple `Content-Type` fields before reading the
body so conflicting media metadata cannot be interpreted using only one value.

## Requirements

- R1. Require exactly one non-blank `Content-Type` field.
- R2. Preserve the existing `text/html` and UTF-8-compatible charset policy.
- R3. Reject duplicate fields before the first response-body read.
- R4. Add focused tests for matching and conflicting duplicates through the
  complete fetch path, including a no-read assertion.
- R5. Preserve URL, redirect, timeout, size, content-encoding, strict UTF-8,
  parser, schema, and output behavior.
- R6. Add static, documentation, completion, and mutation contracts.
- R7. Do not claim live CDC compatibility or make a live request.

## Verification Plan

- Run focused duplicate-content-type tests and all four Make gates.
- Reject validator, duplicate allowlist, no-read, ordering, stale-plan, and
  missing-evidence mutations.
- Run Python compilation, shell syntax, diff, artifact, and secret audits.
- Take one bounded exact-head PR/check/code-scanning snapshot after push.

## Non-Goals

- Supporting non-HTML media types or non-UTF-8 charsets.
- Changing content encoding, decompression, body limits, or parsing.
- Changing dependencies, CI versions, or output files.
