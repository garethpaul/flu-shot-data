---
title: Flu Shot Fetch Host Validation
date: 2026-06-09
status: completed
execution: code
---

## Context

The scraper already required live fetch URLs to use HTTPS with a host, but it
still accepted any HTTPS host. This tool is specifically for CDC flu summary
data, so alternate live hosts should be rejected unless the source provenance
is intentionally reviewed.

## Goals

- Keep the default CDC weekly flu URL unchanged.
- Allow `cdc.gov` and CDC subdomains for live fetches.
- Reject non-CDC HTTPS hosts before opening network requests.
- Keep fixture-based tests offline and deterministic.
- Extend static verification and docs for the source-host boundary.

## Implementation

- Added hostname validation in `validate_fetch_url()`.
- Covered non-CDC host rejection and CDC subdomain acceptance in unit tests.
- Extended `scripts/check-baseline.sh`, README, SECURITY, VISION, and CHANGES.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `scripts/check-baseline.sh`
- `make check`
- `make lint`
- `make test`
- `make build`
- `git diff --check`
