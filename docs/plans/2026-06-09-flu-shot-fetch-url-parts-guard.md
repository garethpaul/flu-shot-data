---
title: Flu Shot Fetch URL Parts Guard
date: 2026-06-09
status: completed
execution: code
---

## Context

Live CDC fetch URL validation already required HTTPS, a CDC-owned host, and no
embedded credentials. The scraper does not need query strings or fragments for
the reviewed weekly-summary source URL, so accepting those parts widened the
source provenance boundary without adding value.

## Goals

- Reject live fetch URLs that include query strings.
- Reject live fetch URLs that include fragments.
- Preserve existing HTTPS, host, and credential validation.
- Keep validation covered by offline unit and static baseline checks.

## Implementation

- Added `parsed.query` and `parsed.fragment` rejection in `validate_fetch_url()`.
- Added fixture-independent unit coverage for query and fragment URL values.
- Extended `scripts/check-baseline.sh`, README, SECURITY, VISION, and CHANGES.

## Verification

- `sh -n scripts/check-baseline.sh`
- `python3 -m unittest discover -s tests -p "test*.py"`
- `scripts/check-baseline.sh`
- `make lint`
- `make test`
- `make build`
- `make check`
- `git diff --check`
