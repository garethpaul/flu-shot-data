# FluView V2 Publication Implementation Plan

Status: Completed

**Goal:** Add an explicit JSON-only `v2` command with atomic publication while preserving the no-argument legacy command exactly.

**Architecture:** Add a narrow CLI dispatcher, one source-orchestration function, and one single-file atomic JSON writer that reuses the existing output path and staging primitives without changing the paired legacy writer.

**Tech Stack:** Python 3 standard library (`argparse`, `json`, `pathlib`), unittest, GNU Make, GitHub Actions.

## Task 1: Lock CLI Dispatch Test-First

- Add failing tests proving no arguments call legacy `run()` and `v2` calls
  only `run_fluview_v2()` with the requested JSON path.
- Reject unknown commands and options through `argparse` without fetching.

## Task 2: Lock Source Orchestration Test-First

- Add a failing test with mocked transports/decoders for metadata, one regional
  response, ten ILINet responses, mortality, builder, and writer.
- Assert exact HHS region order, source identity propagation, returned dataset,
  and one publication call.

## Task 3: Lock Atomic Writer Test-First

- Add failing tests for successful JSON output, default finite JSON behavior,
  existing-mode preservation, invalid parent/target/dataset rejection, and an
  injected serialization failure that preserves prior bytes and removes stages.

## Task 4: Implement Minimal Publication Path

- Add `write_fluview_v2_output()`, `run_fluview_v2()`, and `main()`.
- Keep `run()` and the existing paired legacy publication implementation
  unchanged.

## Task 5: Preserve Durable Contracts

- Update baseline checks, project guidance, issue #24, and `CHANGES.md`.
- Run focused/full tests, a live temporary v2 publication, external Make gates,
  hostile mutations, syntax checks, and gitleaks.
- Push a focused PR, invoke `$codex-review` (skip only authentication failure),
  wait for hosted Python/CodeQL, and merge only the exact reviewed green head.

## Verification Completed

- RED: six focused tests failed because `main`, `run_fluview_v2`, and
  `write_fluview_v2_output` did not exist.
- GREEN: all 116 fixture-backed tests pass, including dispatch, ten-source
  orchestration, finite JSON, mode preservation, invalid targets, and injected
  stage failure.
- Live: `python3 flushot.py v2 --json-path <temporary-path>` published and
  decoded a complete 380-record current dataset with 38 mortality weeks, ten
  HHS totals, and 184 season deaths.
- `make check` is the final repository gate after guidance is complete.
