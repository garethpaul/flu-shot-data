# Live Fetch Boundaries

status: completed

## Context

The live scraper validated only the initial CDC URL and read the complete
response without a size bound. Automatic redirects could therefore leave the
documented CDC provenance boundary, and an unexpectedly large response could
consume unbounded memory.

## Changes

- Reject automatic redirects before urllib drains redirect bodies, and
  revalidate the final response URL against the HTTPS CDC hostname policy.
- Limit live response bodies to 2 MiB and reject oversized declared or streamed
  content before decoding.
- Add dependency-free tests for redirect rejection, final URL validation,
  response-size limits, and the complete bounded fetch path.

## Verification

- `python3 -m unittest discover -s tests -p "test*.py"`
- `make check`
- `git diff --check`
