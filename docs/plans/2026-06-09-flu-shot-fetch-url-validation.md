---
title: Flu Shot Fetch URL Validation
date: 2026-06-09
status: completed
execution: code
---

## Context

`fetch_html` accepts a URL override for live CDC page retrieval. The default URL
uses HTTPS, but overrides were not validated before opening a network request.

## Goals

- Preserve the default CDC weekly flu summary URL.
- Reject non-HTTPS fetch URLs before network access.
- Reject hostless fetch URLs before network access.
- Keep fixture-based tests as the default quality gate.
- Expose `make lint`, `make test`, and `make build` aliases for the static
  baseline.

## Implementation

- Added `validate_fetch_url` using `urllib.parse.urlparse`.
- Called the validator from `fetch_html` before building the request.
- Added unit coverage for HTTPS, HTTP, and hostless URL cases.
- Extended the static baseline, README, VISION, SECURITY, and CHANGES.
- Added Makefile aliases for lint, test, and build gates.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `scripts/check-baseline.sh`
- `make lint`
- `make test`
- `make build`
- `make check`
- `git diff --check`
