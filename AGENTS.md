# AGENTS.md

## Repository purpose

`garethpaul/flu-shot-data` is a dependency-free Python utility that converts a
CDC weekly influenza summary table into CSV and JSON records.

## Project structure

- `Makefile` - repository verification targets
- `scripts` - baseline checks and helper scripts
- `docs` - plans, notes, and generated README assets
- `tests` - tests and fixtures

## Development commands

- Install dependencies: none; the maintained path uses the Python standard
  library only.
- Full baseline: `make check`
- Lint/static checks: `make lint`
- Tests: `make test`
- Build: `make build`
- If a command above skips because a platform toolchain is missing, verify on a machine with that SDK before claiming platform behavior is tested.

## Coding conventions

- Prefer dependency-free tests or stdlib checks when legacy packages are unavailable.

## Testing guidance

- Test-related files detected: `tests/`, `tests/test_flushot.py`
- Start with the narrowest relevant test or Make target, then run `make check` before handing off if the change is not documentation-only.
- Keep README verification notes in sync when commands, fixtures, or supported toolchains change.

## PR / change guidance

- Keep diffs focused on the requested repository and avoid unrelated modernization or formatting churn.
- Preserve public APIs, sample behavior, file formats, and documented environment variables unless the task explicitly changes them.
- Update tests, README notes, or docs/plans when behavior, security posture, or validation commands change.
- Call out skipped platform validation, legacy toolchain assumptions, and any risky files touched in the final summary.

## Safety and gotchas

- No required secret or credential file was identified in the repository scan. If you add integrations later, keep secrets out of git.
- Keep live fetch URLs on HTTPS with a hostname; use fixtures for default tests rather than live network calls.
- Keep live fetch hosts limited to `cdc.gov` or CDC subdomains unless a reviewed source migration changes the data provenance boundary.
- Keep issue #24's reviewed FluView JSON/CSV endpoints behind source-specific
  method, path, query, request-body, media-type, and size validation; do not
  loosen the historical HTML fetcher globally.
- Keep each source-specific FluView transport bound to its exact reviewed URL,
  method, deterministic body, media type, final URL, and identifier range.
- Do not substitute provider counts for legacy jurisdiction counts or copy
  national pediatric mortality into HHS-region records.
- Use validated FluView phase 2 metadata before source joins: reject malformed
  collections, duplicate IDs, invalid weeks/dates, incomplete HHS regions, and
  unknown virus-to-lab relationships.
- Reject embedded credentials in live fetch URLs before opening network requests.
- Reject query strings or fragments in live fetch URLs unless a reviewed source migration changes the provenance boundary.
- Live CDC fetch URLs reject every explicit port before network request construction or redirect handling.
- Revalidate redirect targets and final response URLs against the CDC hostname
  policy.
- Reject automatic redirects and keep live response bodies bounded.
- Require exact HTTP 200 before final URL, response metadata, or body handling.
- Require a single ASCII-decimal `Content-Length` when present and preserve the
  streamed byte ceiling as the final size authority; a present declaration
  must match the final bounded byte count.
- Require exactly one HTML `Content-Type` field before reading live responses.
- Decode bounded live response bodies as strict UTF-8 and keep malformed-body
  errors free of response content.
- Preserve identity-only `Content-Encoding` validation before body reads; do
  not add transparent decompression without a separate bounded design.
- Keep CSV and JSON output destinations filesystem-distinct before either file
  is opened or truncated.
- Preserve validation of both output parents as existing directories before
  either file is opened or truncated.
- Preserve regular-file validation for existing resolved output targets before
  creating stages, backups, or replacing destinations.
- Preserve exact-header, string-value, and strict UTF-8 output record
  validation before either file is opened or truncated.
- Preserve paired output rollback and invocation-owned artifact cleanup for
  handled staging and publication failures; do not claim cross-path crash
  atomicity.
- If rollback itself fails, preserve recovery backups and surface the stable
  incomplete-rollback error rather than deleting prior output bytes.
- Do not let stage or backup cleanup errors mask primary staging, publication,
  or incomplete-rollback errors; continue all remaining invocation-owned
  cleanup attempts after the first cleanup failure.
- Preserve normal output modes and distinct symlink destination behavior when
  changing the paired publication implementation.
- Run `make check` before pushing parser, output schema, or documentation changes.

## Agent workflow

1. Inspect the README, Makefile, manifests, and the files directly related to the request.
2. Make the smallest source or docs change that satisfies the task; avoid generated, vendored, or local-environment files unless required.
3. Run the narrowest useful validation first, then `make check` or the documented package/platform gate when available.
4. If a required SDK, service credential, or external runtime is unavailable, record the skipped command and why.
5. Summarize changed files, commands run, and remaining risks or follow-up validation.
