# FluView Source Transports Design

Status: Completed

## Problem

Issue #24 now has a verified source map, but production code only supports a
query-free HTML GET. The current official sources require two fixed GET URLs
with reviewed queries and two fixed JSON POSTs returning JSON or CSV. Broadly
allowing queries, POST bodies, or new media types in `fetch_html` would weaken a
mature transport boundary and make unrelated CDC URLs callable.

## Options Considered

1. Generalize `fetch_html` into a configurable request helper. This centralizes
   code but turns method, path, query, body, and response type into caller
   authority and risks weakening the legacy contract.
2. Add one generic FluView endpoint function with an endpoint enum. This is
   narrower, but still makes invalid method/body combinations representable and
   pushes source policy into branching configuration.
3. Add four source-specific functions sharing only bounded response primitives.
   Each function owns its exact URL, method, request shape, media type, and
   return type. This duplicates a small amount of request construction while
   making unsupported requests impossible through the public API.

## Decision

Use four dedicated functions:

- `fetch_fluview_phase2_init()` — fixed GET, JSON object;
- `fetch_fluview_phase2_region_data(season_id, region_id)` — fixed POST for HHS
  regions 1 through 10, JSON object;
- `fetch_fluview_phase2_line_csv(season_id, region_id)` — fixed POST for one HHS
  region and ILINet source, UTF-8 CSV text;
- `fetch_fluview_phase4_init()` — fixed GET, JSON object.

Positive integer season identifiers and HHS region identifiers 1 through 10 are
validated before opener construction. POST bodies use deterministic compact
JSON and `Content-Type: application/json`. Every response must have exact HTTP
200, an exact final URL, identity content encoding, a single reviewed media
type, strict UTF-8, and the existing 2 MiB declared/streamed byte ceiling. JSON
must decode to an object. The historical HTML fetcher remains unchanged.

## Error Handling

Input errors fail before network setup. Response status, final URL, metadata,
size, UTF-8, JSON syntax, and JSON root failures use stable `ValueError`
messages without including response bytes. Redirects remain rejected by the
existing handler.

## Validation

Tests use the existing response/opener doubles at the network boundary while
asserting real request method, URL, headers, serialized body, bounded read,
decoding, and parsed return values. Focused tests must be observed failing before
implementation, then the full offline gate and hostile contract mutations must
pass.
