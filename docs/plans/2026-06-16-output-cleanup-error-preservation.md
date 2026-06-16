# Output Cleanup Error Preservation

Status: Completed

## Context

Paired CSV/JSON publication rolls back both destinations when staging or
publication fails. Its unconditional `finally` cleanup currently calls
`Path.unlink()` directly. If that cleanup also fails, the cleanup exception
replaces the primary publication or incomplete-rollback error and can stop
cleanup of later invocation-owned artifacts.

## Goals

- R1: Preserve the original publication error when later stage or backup
  cleanup also fails.
- R2: Preserve the stable incomplete-rollback error and its publication-error
  cause when cleanup also fails.
- R3: Attempt cleanup for every invocation-owned stage and disposable backup,
  even after one cleanup attempt fails.
- R4: Raise a cleanup error when publication succeeded but owned-artifact
  cleanup did not complete.
- R5: Keep recovery backups when rollback is incomplete and preserve existing
  output modes, symlink behavior, and successful publication behavior.
- R6: Protect the behavior with focused runtime tests and baseline contracts.

## Non-Goals

- Do not claim process-crash, kernel, filesystem, or power-loss atomicity.
- Do not change output schemas, CDC parsing, fetch policy, destination
  validation, or public function signatures.
- Do not suppress cleanup failures when no earlier operation failed.

## Implementation

1. Detect whether a primary publication or rollback exception is active while
   the unconditional cleanup phase runs.
2. Run each stage and eligible backup cleanup independently, collecting the
   first cleanup exception without stopping later attempts.
3. Let the active primary error propagate after cleanup; otherwise raise the
   first cleanup error.
4. Add focused tests for publication-plus-cleanup failure,
   incomplete-rollback-plus-cleanup failure, and successful-publication cleanup
   failure.
5. Update project guidance and changelog with the handled-error guarantee.

## Verification

- Run the focused publication tests and the full `make check`, `make lint`,
  `make test`, and `make build` gates from bounded commands.
- Run the complete check from an external working directory.
- Reject isolated mutations that restore direct `finally` cleanup, stop after
  the first cleanup error, mask the primary publication error, delete recovery
  backups, or remove the new tests and completed-plan evidence.
- Audit the exact diff, generated artifacts, credential-like values, file
  modes, and branch/upstream state before committing.

## Risks

- Exception chaining must remain deterministic so operators see the primary
  publication failure rather than a secondary cleanup detail.
- Cleanup failures can leave invocation-owned artifacts; tests must prove all
  remaining cleanup attempts still run and recovery backups are retained only
  when required.

## Work Completed

- Preserved active publication and incomplete-rollback exceptions through the
  unconditional cleanup phase.
- Attempted every invocation-owned stage and disposable backup cleanup after a
  cleanup failure, raising the first cleanup error only after otherwise
  successful publication.
- Added fault-injection regressions for primary publication errors,
  incomplete rollback, and successful publication with cleanup failure.
- Updated repository guidance, security posture, changelog, and static
  baseline contracts.

## Actual Verification

- All 62 offline tests passed in the focused suite and in `make check`,
  `make lint`, `make test`, and `make build`.
- Repository-root and external-directory `make check` passed with bounded
  commands.
- Six isolated mutations were rejected across active-error detection,
  continue-after-cleanup behavior, recovery-backup retention, test
  registration, guidance, and explicit exception cause chaining.
- Shell syntax, Python compilation, whitespace, exact diff, generated
  artifacts, credential-like additions, file modes, and branch/upstream state
  were audited; no live CDC request was made.
- The handled-exception guarantee still does not claim process-crash, kernel,
  filesystem, or power-loss atomicity.
