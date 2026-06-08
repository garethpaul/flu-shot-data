## Flu Shot Data Vision

This document explains the current state and direction of the project.
Project overview and developer docs: [`README.md`](README.md)

Flu Shot Data is a Python 3 scraper that reads CDC weekly flu summary data
and writes `flu.csv` and `flu.json`.

The repository is useful as a preserved public-health data extraction script
using standard-library fetching, table parsing, CSV output, and JSON conversion.
Basic context lives in [`README.md`](README.md).

The goal is to keep the data extraction process understandable while making
source fragility, generated outputs, and runtime assumptions explicit.

The current focus is:

Priority:

- Preserve the CDC weekly-summary extraction logic
- Keep CSV and JSON output schemas visible
- Avoid committing generated data unless intentionally versioned
- Keep the parser testable without live CDC network access

Current baseline:

- `scripts/check-baseline.sh` and `make check` verify Python 3 syntax,
  fixture-based tests, generated-output ignores, and static parser guardrails.
- Fetching, parsing, and output writing are separate functions in `flushot.py`.
- The CDC URL uses HTTPS.
- `flu.csv` and `flu.json` are treated as generated outputs unless intentionally
  reviewed as data artifacts.

Next priorities:

- Validate the parser against the current live CDC page before publishing generated data
- Add provenance metadata if generated outputs are intentionally committed
- Update source URLs if CDC structure changes

Contribution rules:

- One PR = one focused parser, dependency, output, or documentation change.
- Document source URL and output schema changes.
- Use small HTML fixtures for parser tests.
- Keep generated outputs separate from code changes unless reviewed as data.

## Security And Responsible Use

Canonical security policy and reporting:

- [`SECURITY.md`](SECURITY.md)

Public health data should be handled carefully. Changes must avoid silently
mislabeling weeks, dates, regions, or metrics when the upstream page changes.

## What We Will Not Merge (For Now)

- Live-only tests as the default quality gate
- Generated data dumps without provenance
- Parser rewrites without fixture coverage
- Claims of current CDC compatibility without verification

This list is a roadmap guardrail, not a permanent rule.
Strong user demand and strong technical rationale can change it.
