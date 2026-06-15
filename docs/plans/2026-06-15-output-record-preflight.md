---
title: Output Record Preflight
type: reliability
status: completed
date: 2026-06-15
execution: code
---

# Output Record Preflight

## Problem

`write_outputs` opens and truncates the CSV before `csv.DictWriter` or JSON
encoding has validated the complete caller-supplied record set. A malformed row
can therefore destroy an existing CSV while leaving the paired JSON unchanged.

## Approach

- Materialize the record iterable once after destination-path validation.
- Require every row to be a dictionary with exactly the documented headers,
  string values, and strict UTF-8 encodability before either file is opened.
- Raise a stable `ValueError` while preserving both existing output files.
- Add focused regressions and mutation-sensitive source, guidance, and
  completed-plan contracts.

## Files

- `flushot.py`
- `tests/test_flushot.py`
- `scripts/check-baseline.sh`
- `README.md`
- `SECURITY.md`
- `VISION.md`
- `CHANGES.md`
- `AGENTS.md`
- `docs/plans/2026-06-15-output-record-preflight.md`

## Verification

- Prove malformed schema, non-string values, and invalid UTF-8 currently alter
  an existing destination before failing, then prove both sentinels survive.
- Run focused tests followed by repository-root and external-directory
  `make check`.
- Reject isolated source, regression, guidance, and plan-evidence mutations.
- Audit the exact diff, generated artifacts, and credential-shaped additions.

## Non-Goals

- Do not implement multi-file transactional publication or directory creation.
- Do not change parsing, CDC fetching, valid output schemas, or CLI behavior.
- Do not merge or close stacked pull requests without owner authorization.

## Status: Completed

## Work Completed

- Materialize and validate every output row after destination checks but before
  either output file is opened.
- Reject non-dictionary rows, non-exact headers, non-string values, and text
  that cannot be encoded as strict UTF-8 with stable `ValueError` messages.
- Preserve existing CSV and JSON bytes for every rejected record class.
- Add source, regression, guidance, and completed-plan baseline contracts.

## Verification Completed

- The focused regressions failed against the prior implementation because an
  extra field and invalid UTF-8 failed after CSV truncation while a non-string
  value was accepted; all three passed after the record preflight was added.
- Python 3.12.8 repository-root and external-directory `make check` passed
  all 50 offline tests, static contracts, and in-memory syntax compilation.
- Seven isolated hostile mutations were rejected for validator invocation,
  exact-header enforcement, string-value enforcement, strict UTF-8 encoding,
  sentinel regression coverage, maintained guidance, and plan completion
  evidence.
- Exact diff, generated-artifact, and credential-pattern audits passed.
- No live CDC request was made.
