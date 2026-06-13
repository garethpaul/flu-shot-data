---
title: Location-Independent Flu Verification
type: reliability
date: 2026-06-13
status: completed
execution: code
---

# Location-Independent Flu Verification

## Summary

Resolve the maintained offline checker from the loaded Makefile so every
documented gate works when Make is invoked outside the checkout.

## Requirements

- R1. Derive the repository root from `MAKEFILE_LIST`.
- R2. Invoke `scripts/check-baseline.sh` through its repository-rooted path.
- R3. Run the checker's Python compilation and unittest discovery from the
  repository root.
- R4. Add static contracts that reject caller-directory-relative checker or
  Python execution.
- R5. Preserve parser behavior, fixtures, output schema, workflow, provenance,
  metadata, redirect, timeout, byte-limit, response-header, and decoding
  boundaries.
- R6. Record actual root and external-directory verification before completion.

## Verification Plan

- Run `make check`, `make lint`, `make test`, and `make build` at repository
  root.
- Run the full gate from `/tmp` through the absolute Makefile path.
- Reject isolated hostile root-derivation, checker-path, Python-working-directory,
  documentation, plan-status, and verification-evidence mutations.
- Run Python compilation, shell syntax, `git diff --check`, exact-path review,
  secret scanning, and generated-artifact inspection.

## Non-Goals

- Changing parser, fetch, response validation, output, or workflow behavior.
- Making a live CDC request or claiming current CDC markup compatibility.

## Work Completed

- Derived the repository root from the loaded Makefile and invoked the offline
  checker through that absolute path.
- Ran Python compilation and unittest discovery from the repository root so
  imports remain deterministic outside the checkout.
- Extended the baseline with rooted-Makefile, completed-plan, external-run, and
  synchronized-guidance contracts.
- Preserved parser, fixture, output-schema, workflow, provenance, metadata,
  redirect, timeout, byte-limit, response-header, and decoding behavior.

## Verification Completed

- `make check`, `make lint`, `make test`, and `make build` passed at repository
  root.
- The full gate passed from /tmp through the absolute Makefile path.
- Six isolated hostile root-derivation, checker-path,
  Python-working-directory, documentation, plan-status, and
  verification-evidence mutations were rejected.
- Python compilation, shell syntax, `git diff --check`, exact-path review,
  added-line secret scanning, and generated-artifact inspection passed.
- No live CDC request was made, so current production metadata and markup
  compatibility are not claimed.
