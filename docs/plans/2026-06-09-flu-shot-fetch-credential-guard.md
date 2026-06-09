---
title: Flu Shot Fetch Credential Guard
date: 2026-06-09
status: completed
execution: code
---

## Context

Live fetch URL validation required HTTPS, a host, and a CDC-owned hostname, but
URLs with embedded username or password components could still pass those
checks. The scraper does not need credentialed CDC URLs, and accepting userinfo
would make source review and logging boundaries less clear.

## Goals

- Reject live fetch URLs that include embedded username or password values.
- Preserve HTTPS and CDC-owned hostname validation.
- Keep fixture-based tests offline and deterministic.
- Extend static verification and docs for the fetch URL credential boundary.

## Implementation

- Added `parsed.username` and `parsed.password` rejection in
  `validate_fetch_url()`.
- Added a unit test for `https://user:pass@www.cdc.gov/flu/weekly/`.
- Extended `scripts/check-baseline.sh`, README, SECURITY, VISION, and CHANGES.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `scripts/check-baseline.sh`
- `make check`
- `make lint`
- `make test`
- `make build`
- `git diff --check`
