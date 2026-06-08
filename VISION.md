## Flu Shot Data Vision

This document explains the current state and direction of the project.
Project overview and developer docs: [`README.md`](README.md)

Flu Shot Data is a Python 2-era scraper that reads CDC weekly flu summary data
and writes `flu.csv` and `flu.json`.

The repository is useful as a preserved public-health data extraction script
using mechanize, BeautifulSoup, CSV output, and JSON conversion. Basic context
lives in [`README.md`](README.md).

The goal is to keep the data extraction process understandable while making
source fragility, generated outputs, and runtime assumptions explicit.

The current focus is:

Priority:

- Preserve the CDC weekly-summary extraction logic
- Keep CSV and JSON output schemas visible
- Avoid committing generated data unless intentionally versioned
- Make Python 2 and dependency assumptions clear

Next priorities:

- Add README setup, run, and output examples
- Port to supported Python and maintained HTML parsing libraries
- Add fixture-based tests so parsing is not coupled to live CDC markup
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
