---
title: Flu Shot Fetch Timeout Validation
date: 2026-06-09
status: completed
execution: code
---

## Context

Live CDC fetch URLs are validated before network requests, but the request
timeout was passed through directly. A caller could provide zero, negative,
very large, or non-numeric timeout values and bypass the scraper's intended
bounded network behavior.

## Goals

- Preserve the default 30-second fetch timeout.
- Accept practical timeout overrides from callers.
- Fall back to the default for non-numeric, zero, negative, or excessive values.
- Keep timeout validation covered by offline tests and static baseline checks.

## Implementation

- Added `fetch_timeout()` with a 1-to-300 second accepted range.
- Routed `fetch_html()` through the helper before calling `urlopen`.
- Added unit coverage for invalid, out-of-range, and valid timeout values.
- Updated README, SECURITY, VISION, CHANGES, and `scripts/check-baseline.sh`.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `scripts/check-baseline.sh`
- `make check`
- `git diff --check`
