# Staging Cleanup Error Preservation

Status: In Progress

## Context

CSV and JSON output staging reserves both temporary files before paired
publication. If reservation, mode preservation, or serialization fails,
`stage_outputs()` removes any stages it owns. Those direct cleanup calls run
while the primary staging exception is active, so an `unlink()` failure can
replace the actionable staging error and stop cleanup of the other stage.

## Goals

- R1: Preserve the original staging error when owned-stage cleanup also fails.
- R2: Attempt cleanup for every reserved stage even after one cleanup attempt
  fails.
- R3: Preserve the existing successful staging and paired publication behavior.
- R4: Protect the behavior with focused fault-injection tests and a static
  baseline contract.

## Non-Goals

- Do not change output schemas, destination validation, publication rollback,
  CDC parsing, or fetch policy.
- Do not suppress cleanup errors when no primary staging error exists.
- Do not claim process-crash, kernel, filesystem, or power-loss atomicity.

## Implementation

1. Add one small cleanup helper that attempts every supplied path and records
   the first cleanup error.
2. Use it from staging failure handling while allowing the active staging error
   to propagate unchanged.
3. Reuse the helper in publication cleanup without changing its recovery-backup
   retention behavior.
4. Add tests for serialization-plus-cleanup failure and continued cleanup after
   the first stage cleanup failure.
5. Extend the baseline checker and project guidance with the staging guarantee.

## Verification

- Run focused output tests and the full `make check`, `make lint`, `make test`,
  and `make build` gates with explicit timeouts.
- Run the complete check from an external working directory.
- Reject isolated mutations that restore masking, stop cleanup after the first
  failure, bypass the helper, remove the tests, or reopen completed plan status.
- Audit the exact diff, generated artifacts, credential-like additions, file
  modes, and branch/upstream state before committing.

## Risks

- Helper reuse must not alter publication rollback or recovery-backup retention.
- Exception propagation must remain deterministic: primary staging errors take
  precedence, while cleanup-only failures remain visible where applicable.
