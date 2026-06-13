---
title: Duplicate Response Content Type Rejection
type: security
status: completed
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

## Work Completed

- Enumerated all `Content-Type` header fields and rejected more than one before
  parsing the existing HTML media type and charset policy.
- Added matching and conflicting duplicate regressions through `fetch_html`,
  including zero-read assertions.
- Extended the static baseline and repository guidance for the boundary.

## Verification Completed

- The focused duplicate-content-type test and complete 30-test suite passed.
- The six hostile mutations were rejected: header enumeration removal, duplicate
  allowlisting, body-read reordering, no-read assertion loss, stale plan status,
  and missing evidence.
- The all four Make gates passed result was first confirmed in the isolated
  mutation fixture and then rerun against the final worktree.
- Python compilation, shell syntax, `git diff --check`, and intended-path
  artifact and secret scans are included in final-tree verification.
- No live CDC request was made; current production metadata and markup
  compatibility are not claimed.
- The hosted pull-request check and code-scanning result will be recorded
  against the exact pushed head in the external tracker.
