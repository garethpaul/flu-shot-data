---
title: CDC Fetch Port Boundary
type: security
date: 2026-06-15
status: completed
execution: code
---

# CDC Fetch Port Boundary

## Problem Frame

`validate_fetch_url()` restricts live requests to HTTPS CDC hosts, but it does
not inspect the parsed port. URLs such as `https://cdc.gov:8443/flu/weekly/`
therefore pass the provenance check, and malformed ports are deferred to later
request handling. The validator should reject every explicit port before a
request or redirect target can be used.

## Prioritized Engineering Work

1. **P0 - Authority validation:** reject explicit and malformed ports before
   network request construction.
2. **P1 - Regression coverage:** prove direct fetch URLs and redirect targets
   fail closed without opening a request.
3. **P2 - Maintained contract:** add mutation-sensitive static enforcement and
   keep project security guidance synchronized.

This change implements P0 through P2 without changing the CDC host allowlist,
response metadata policy, body limits, parser behavior, or output formats.

## Requirements

- R1. Canonical HTTPS CDC URLs without an explicit port must remain accepted.
- R2. Empty, default, and non-default explicit ports must be rejected.
- R3. Non-numeric and out-of-range ports must produce the same deterministic
  validation error rather than leaking `urlparse` implementation errors.
- R4. Redirect targets must pass the same port boundary before rejection as an
  unsupported redirect.
- R5. Static contracts must reject removal, reordering, fixture loss,
  documentation drift, and incomplete verification evidence.

## Implementation Units

### U1: Validate Parsed Authority

Files:

- `flushot.py`
- `tests/test_flushot.py`

Approach:

- Read `parsed.port` inside a narrow `ValueError` boundary.
- Reject every non-`None` port before returning the validated URL.
- Extend direct and redirect-target regressions with default, alternate,
  non-numeric, and out-of-range port cases.

### U2: Enforce The Contract

Files:

- `scripts/check-baseline.sh`
- `docs/plans/2026-06-15-cdc-fetch-port-boundary.md`

Approach:

- Verify the port parser, deterministic error translation, no-port condition,
  pre-return ordering, and focused fixtures.
- Require completed plan evidence after implementation validation.

### U3: Synchronize Guidance

Files:

- `AGENTS.md`
- `CHANGES.md`
- `README.md`
- `SECURITY.md`
- `VISION.md`

## Verification

- Focused URL and redirect tests.
- Repository and external-directory `make check` on an available maintained
  Python version.
- Hostile mutations for removed parsing, error translation, port rejection,
  ordering, fixtures, guidance, and plan completion evidence.
- Exact diff, generated artifact, conflict marker, and changed-line secret
  audits.

## Risks

- A caller that intentionally used an explicit `:443` will now be rejected.
  The canonical configured CDC URL has no explicit port, and rejecting all
  explicit ports keeps the reviewed authority boundary unambiguous.
- Live CDC transport remains outside the offline validation suite.

## Work Completed

- Parsed the URL port inside a deterministic validation boundary and rejected
  every explicit port before CDC host acceptance or request construction.
- Preserved canonical CDC hosts without explicit ports while translating
  non-numeric and out-of-range port parser failures into the same stable error.
- Added direct URL, pre-opener fetch, and redirect-target regressions for
  default, alternate, non-numeric, and out-of-range ports.
- Added a focused static checker, baseline integration, and synchronized
  contributor, security, maintenance, and change guidance.

## Verification Completed

- The focused fetch-port checker passed.
- Python 3.12 passed all 41 offline unit and integration tests.
- Repository-root and external-directory `make check` passed with bytecode
  generation disabled.
- Ten isolated hostile mutations were rejected: removed authority delimiter
  parsing, removed port parsing, removed malformed-port translation, removed
  explicit-port rejection, validation reordered after host acceptance, removed
  default-port coverage, removed no-opener proof, removed redirect coverage,
  removed guidance, and reopened plan completion evidence.
- Shell syntax, in-memory compilation, exact diff, generated artifact, conflict
  marker, and changed-line secret audits passed before delivery.
- No live CDC request was made.

## Status: Completed
