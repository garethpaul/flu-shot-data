# Security Policy

## Supported Versions

The supported security scope for `flu-shot-data` is the current default branch, `master`. Older commits, tags, branches, forks, demos, and generated artifacts are not actively supported unless the repository explicitly marks them as maintained.

Project summary: Flu Shot Data to CSV

## Reporting a Vulnerability

Please report suspected vulnerabilities through GitHub's private vulnerability reporting or by opening a draft GitHub Security Advisory for `garethpaul/flu-shot-data` when that option is available. If GitHub does not show a private reporting option for this repository, contact the repository owner through GitHub and avoid posting exploit details publicly until the issue can be assessed.

Do not open a public issue that includes exploit code, secrets, personal data, or detailed reproduction steps for an unpatched vulnerability.

## What to Include

Helpful reports include:

- the affected file, endpoint, permission, dependency, or workflow
- a concise impact statement explaining what an attacker could do
- reproduction steps using test data and accounts you control
- the branch, commit SHA, platform version, device, runtime, or dependency versions used
- logs, screenshots, or proof-of-concept snippets that demonstrate impact without exposing private data

## Project Security Posture

- This repository appears to be a public sample, documentation, or utility project. The active security scope is the code and documentation on the default branch.
- Review found external API integrations or credential-adjacent configuration; changes in those areas should receive security-focused review before merge.
- Review found network clients, sockets, web APIs, or service endpoints; changes in those areas should receive security-focused review before merge.
- Fetch URLs should remain HTTPS URLs with explicit hosts before network requests are opened.
- Fetch hosts should remain limited to `cdc.gov` or CDC subdomains unless a
  reviewed source migration changes the data provenance boundary.
- Fetch URLs should reject embedded credentials before network requests are
  opened.
- Fetch URLs should reject query strings or fragments unless a reviewed source
  migration changes the data provenance boundary.
- Issue #24's reviewed FluView endpoints require source-specific query, POST
  body, JSON, and CSV policies. Implement them as narrow adapters; do not relax
  the historical HTML fetcher's global URL or response-metadata boundaries.
- Every source-specific FluView transport requires its exact final URL, fixed
  method and request shape, identity encoding, one reviewed media type, strict
  UTF-8, and the declared/streamed 2 MiB ceiling before parsing.
- Treat only validated FluView phase 2 metadata as join authority; upstream
  collection shape, identifiers, dates, catalogs, and relationships are
  untrusted until normalized by the fixture-backed decoder.
- Live CDC fetch URLs reject every explicit port before network request construction or redirect handling.
- Fetch timeouts should be bounded before network requests are opened so invalid
  or excessive caller-provided values do not control live request behavior.
- Automatic redirects are rejected, final response URLs remain inside the
  HTTPS CDC hostname boundary, and response bodies are bounded.
- Live CDC responses must be exactly HTTP 200 before URL, metadata, or body
  processing continues.
- An optional `Content-Length` must be a single ASCII-decimal field within the
  configured limit. Ambiguous or malformed declarations fail before body reads,
  a present declaration must equal the final bounded byte count, and streamed
  byte counting remains authoritative.
- Live response metadata must declare exactly one `text/html` field; duplicate
  fields and duplicate charset parameters are rejected, a single explicit
  charset must be UTF-8-compatible, and validation must occur before
  response-body reads.
- Bounded live response bodies must decode as strict UTF-8. Malformed bytes
  fail with a generic error that does not include response content.
- Live responses must use absent or one explicit identity `Content-Encoding`;
  compressed, duplicated, or transformed bodies fail before any body read.
- Parsed influenza week numbers and ending dates should be validated before
  public-health records are emitted.
- Duplicate region labels should fail parsing before public-health outputs are
  written, including duplicates that differ only by letter case.
- CSV and JSON outputs must resolve to distinct filesystem targets before
  either destination is opened or truncated.
- CSV and JSON output parents must be existing directories before either
  destination is opened or truncated.
- Existing resolved output destinations must be regular files; directories and
  special files fail before stages or backups are created.
- Output records must match the documented header set and contain only valid
  UTF-8 strings before either destination is opened or truncated.
- Paired CSV and JSON outputs must preserve their prior generation across
  handled staging or publication exceptions and remove invocation-owned stage
  and backup files. This does not provide multi-path crash atomicity.
- Preserve existing output modes and distinct symlink target semantics while
  staging publication files in the resolved destination directories.
- If a rollback syscall fails, retain recovery backups instead of deleting the
  prior generation; operators must resolve the reported incomplete rollback.
- Cleanup failures must not mask a primary staging, publication, or
  incomplete-rollback error, and one failed cleanup attempt must not stop later
  owned-artifact cleanup attempts.
- GitHub Actions runs the offline `make check` matrix with read-only repository
  permissions so fixture, fetch URL, parser, and output guardrails stay
  enforced without contacting live CDC endpoints.
- Checkout credentials are not persisted, and workflow actions remain pinned
  to immutable commit revisions.
- Repository-wide CODEOWNERS records ownership for parser, workflow, and data
  provenance changes; branch rules must require review for enforcement.
- Review found file, document, data, or media parsing flows; changes in those areas should receive security-focused review before merge.
- No primary dependency manifest was detected in the repository root. If dependencies are added later, include a manifest and prefer reproducible installation instructions.

## Service and API Notes

For web services, APIs, sockets, or scraping workflows, prioritize reports involving authentication bypass, authorization errors, injection, server-side request forgery, unsafe deserialization, credential leakage, data exposure, or denial-of-service conditions. Use test accounts and minimal proof-of-concept traffic only.

## Dependency and Supply Chain Security

Dependency updates should come from trusted package managers and should keep lockfiles in sync when lockfiles exist. Do not commit credentials, private keys, tokens, generated secrets, or machine-local configuration. If a vulnerability depends on a compromised package, typosquatting risk, insecure transitive dependency, or unsafe build step, include the package name, affected version, and the path through which it is used.

## Safe Research Guidelines

Good-faith research is welcome when it stays within these boundaries:

- use only accounts, devices, data, and infrastructure that you own or have explicit permission to test
- avoid destructive actions, persistence, spam, phishing, social engineering, or denial-of-service testing
- minimize access to personal data and stop testing immediately if private data is exposed
- do not exfiltrate secrets or third-party data; report the minimum evidence needed to verify impact
- keep vulnerability details confidential until the maintainer has assessed the report

## Maintainer Response

The maintainer will review complete reports as availability allows, prioritize issues by exploitability and impact, and coordinate a fix or mitigation when the affected code is still maintained. For sample, archived, or educational repositories, the likely remediation may be documentation, dependency updates, or clearly marking unsupported code rather than a production-style patch release.
