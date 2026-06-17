---
title: Output Target Type Preflight
type: security
status: planned
date: 2026-06-17
---

# Output Target Type Preflight

## Context

`write_outputs` validates output parents and path collisions before staging, but
it does not validate the type of an existing CSV or JSON destination. The
publication path can therefore rename an existing directory or special file to
a hidden backup before later cleanup fails. A configuration error must not
mutate a non-regular filesystem object.

## Priority

1. Reject existing non-regular output destinations before creating stages or
   backups.
2. Preserve support for missing outputs, regular files, and symlinks that
   resolve to distinct regular files.
3. Prove both outputs remain unchanged and no publication artifacts are created
   when either destination fails the preflight.

## Requirements

- Extend the output-path preflight in `flushot.py` to require each existing,
  resolved destination to be a regular file.
- Raise a stable `ValueError` before staging when an output resolves to a
  directory, FIFO, socket, device, or other non-regular filesystem object.
- Add focused regressions in `tests/test_flushot.py` for directory and FIFO
  destinations in both CSV and JSON positions.
- Assert the rejected target, its paired output, and the containing directory
  remain unchanged and contain no stage or backup artifacts.
- Add mutation-sensitive static contracts to `scripts/check-baseline.sh` and
  update maintained guidance in `README.md`, `SECURITY.md`, `VISION.md`, and
  `CHANGES.md`.

## Implementation Units

### 1. Destination preflight

Files:

- `flushot.py`

Validate resolved output types alongside the existing parent and collision
checks. Missing paths remain valid because publication creates them.

### 2. Regression and maintenance contracts

Files:

- `tests/test_flushot.py`
- `scripts/check-baseline.sh`

Exercise both output positions and distinguish regular files from directories
and FIFOs without relying on network access.

### 3. Guidance and evidence

Files:

- `README.md`
- `SECURITY.md`
- `VISION.md`
- `CHANGES.md`
- `docs/plans/2026-06-17-output-target-type-preflight.md`

Document the fail-closed target boundary and record only validation that was
actually executed.

## Validation

- Run the focused output-target tests.
- Run repository-root and external-directory `make check` with bytecode writes
  disabled.
- Reject isolated mutations to the regular-file check, both destination
  positions, artifact assertions, maintained guidance, and completed evidence.
- Audit the exact diff, generated artifacts, whitespace, conflict markers, and
  credential-shaped additions.
- Require exact-head hosted checks before recording terminal hosted evidence.

## Scope Boundaries

- Do not create missing parent directories.
- Do not add filesystem locking or claim crash, kernel, filesystem, or
  power-loss atomicity.
- Do not open or mutate rejected non-regular targets merely to classify them.
- Do not merge or close this stacked pull request or its predecessors without
  explicit authorization.

## Verification Results

Implementation and verification are pending.
