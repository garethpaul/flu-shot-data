---
title: Location-Independent Flu Verification
type: reliability
date: 2026-06-13
status: planned
execution: code
---

# Location-Independent Flu Verification

## Summary

Resolve the maintained offline checker from the loaded Makefile so every
documented gate works when Make is invoked outside the checkout.

## Requirements

- R1. Derive the repository root from `MAKEFILE_LIST`.
- R2. Invoke `scripts/check-baseline.sh` through its repository-rooted path.
- R3. Add a static contract that rejects caller-directory-relative invocation.
- R4. Preserve parser behavior, fixtures, output schema, workflow, provenance,
  metadata, redirect, timeout, byte-limit, response-header, and decoding
  boundaries.
- R5. Record actual root and external-directory verification before completion.

## Verification Plan

- Run `make check`, `make lint`, `make test`, and `make build` at repository
  root.
- Run the full gate from `/tmp` through the absolute Makefile path.
- Reject isolated hostile root-derivation, checker-path, documentation,
  plan-status, and verification-evidence mutations.
- Run Python compilation, shell syntax, `git diff --check`, exact-path review,
  secret scanning, and generated-artifact inspection.

## Non-Goals

- Changing parser, fetch, response validation, output, or workflow behavior.
- Making a live CDC request or claiming current CDC markup compatibility.

## Work Completed

Pending implementation.

## Verification Completed

Pending implementation and verification.
