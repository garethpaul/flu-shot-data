#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PLAN="$ROOT_DIR/docs/plans/2026-06-08-flu-shot-data-python3-baseline.md"
PERCENT_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-percent-normalization.md"
HEADER_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-summary-header-guard.md"
SUBHEADING_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-optional-subheading.md"
TABLE_SELECTION_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-table-selection.md"
SUMMARY_ROW_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-summary-row-skip.md"
FETCH_URL_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-fetch-url-validation.md"
FETCH_HOST_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-fetch-host-validation.md"
FETCH_CREDENTIAL_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-fetch-credential-guard.md"
FETCH_URL_PARTS_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-fetch-url-parts-guard.md"
FETCH_TIMEOUT_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-fetch-timeout-validation.md"
WEEK_METADATA_PLAN="$ROOT_DIR/docs/plans/2026-06-10-flu-week-metadata-validation.md"
LIVE_FETCH_BOUNDARY_PLAN="$ROOT_DIR/docs/plans/2026-06-12-live-fetch-boundaries.md"
DUPLICATE_REGION_PLAN="$ROOT_DIR/docs/plans/2026-06-12-duplicate-region-guard.md"
CI_PLAN="$ROOT_DIR/docs/plans/2026-06-10-ci-baseline.md"
CI_WORKFLOW="$ROOT_DIR/.github/workflows/check.yml"
CODEOWNERS="$ROOT_DIR/.github/CODEOWNERS"
PYTHON=${PYTHON:-python3}

cleanup_bytecode() {
  find "$ROOT_DIR" -maxdepth 3 -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
  find "$ROOT_DIR" -maxdepth 3 -type f -name "*.pyc" -delete 2>/dev/null || true
}

trap cleanup_bytecode EXIT
cleanup_bytecode

require_file() {
  path=$1
  if [ ! -f "$ROOT_DIR/$path" ]; then
    printf '%s\n' "Required file missing: $path" >&2
    exit 1
  fi
}

for path in \
  ".gitignore" \
  ".github/CODEOWNERS" \
  ".github/workflows/check.yml" \
  "CHANGES.md" \
  "Makefile" \
  "README.md" \
  "SECURITY.md" \
  "VISION.md" \
  "flushot.py" \
  "tests/test_flushot.py" \
  "tests/fixtures/cdc_weekly_summary.html" \
  "docs/plans/2026-06-09-flu-shot-fetch-credential-guard.md" \
  "docs/plans/2026-06-09-flu-shot-fetch-timeout-validation.md" \
  "docs/plans/2026-06-10-flu-week-metadata-validation.md" \
  "docs/plans/2026-06-12-live-fetch-boundaries.md" \
  "docs/plans/2026-06-12-duplicate-region-guard.md" \
  "docs/plans/2026-06-10-ci-baseline.md" \
  "docs/plans/2026-06-09-flu-shot-fetch-url-parts-guard.md" \
  "docs/plans/2026-06-09-flu-shot-summary-row-skip.md" \
  "docs/plans/2026-06-09-flu-shot-fetch-host-validation.md" \
  "docs/plans/2026-06-09-flu-shot-fetch-url-validation.md" \
  "docs/plans/2026-06-09-flu-shot-optional-subheading.md" \
  "docs/plans/2026-06-09-flu-shot-table-selection.md" \
  "docs/plans/2026-06-09-flu-shot-summary-header-guard.md" \
  "docs/plans/2026-06-09-flu-shot-percent-normalization.md" \
  "docs/plans/2026-06-08-flu-shot-data-python3-baseline.md"; do
  require_file "$path"
done

workflow_paths=$(find "$ROOT_DIR/.github/workflows" -type f \( -name '*.yml' -o -name '*.yaml' \) -print | LC_ALL=C sort)
if [ "$workflow_paths" != "$CI_WORKFLOW" ]; then
  printf '%s\n' "The reviewed check workflow must be the only GitHub Actions workflow." >&2
  exit 1
fi

if ! grep -Fq "seen_regions: set[str] = set()" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "region_key = region.casefold()" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "CDC summary table contains duplicate region rows" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_parse_records_rejects_duplicate_regions_case_insensitively" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq 'for region in ("Region 1", "region 1")' "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Parser must reject duplicate region records case-insensitively." >&2
  exit 1
fi

codeowner_rules=$(grep -Ev '^[[:space:]]*(#|$)' "$CODEOWNERS" 2>/dev/null || true)
if [ "$codeowner_rules" != '* @garethpaul' ]; then
  printf '%s\n' "CODEOWNERS must retain repository-wide ownership." >&2
  exit 1
fi

if grep -E '^[[:space:]]*(-[[:space:]]+)?uses:' "$CI_WORKFLOW" | grep -Ev '@[0-9a-f]{40}([[:space:]]+#.*)?$' >/dev/null; then
  printf '%s\n' "GitHub Actions must use immutable commit revisions." >&2
  exit 1
fi

workflow_uses=$(grep -E '^[[:space:]]*(-[[:space:]]+)?uses:' "$CI_WORKFLOW" | sed -E 's/^[[:space:]]*(-[[:space:]]+)?//' | LC_ALL=C sort)
expected_workflow_uses=$(printf '%s\n' \
  'uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3' \
  'uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405 # v6.2.0' | LC_ALL=C sort)
if [ "$workflow_uses" != "$expected_workflow_uses" ]; then
  printf '%s\n' "GitHub Actions must use only the reviewed setup actions." >&2
  exit 1
fi

if [ "$(grep -Ec '^permissions:$' "$CI_WORKFLOW")" -ne 1 ] ||
  [ "$(grep -Ec '^  contents: read$' "$CI_WORKFLOW")" -ne 1 ] ||
  grep -Eq 'write-all|contents:[[:space:]]*write|pull-requests:[[:space:]]*write|actions:[[:space:]]*write' "$CI_WORKFLOW"; then
  printf '%s\n' "GitHub Actions permissions must remain globally read-only." >&2
  exit 1
fi

if [ "$(grep -Ec '^[[:space:]]*persist-credentials: false$' "$CI_WORKFLOW")" -ne 1 ] ||
  grep -Eq '^[[:space:]]*persist-credentials: true$' "$CI_WORKFLOW"; then
  printf '%s\n' "GitHub Actions checkout credentials must not persist." >&2
  exit 1
fi

if [ "$(grep -Ec '^[[:space:]]*(-[[:space:]]+)?run:' "$CI_WORKFLOW")" -ne 1 ] ||
  ! grep -Eq '^[[:space:]]*run: make check[[:space:]]*$' "$CI_WORKFLOW" ||
  grep -Eq '^[[:space:]]*(if|continue-on-error):|\$\{\{[[:space:]]*if[[:space:]]' "$CI_WORKFLOW"; then
  printf '%s\n' "GitHub Actions must run exactly the offline Make gate without bypasses." >&2
  exit 1
fi

for workflow_contract in \
  'push:' \
  'branches:' \
  '- master' \
  'pull_request:' \
  'workflow_dispatch:' \
  'cancel-in-progress: true' \
  'runs-on: ubuntu-24.04' \
  'timeout-minutes: 10' \
  'fail-fast: false' \
  'python-version: ["3.10", "3.12", "3.14"]' \
  'python-version: ${{ matrix.python-version }}'; do
  if ! grep -Fq -- "$workflow_contract" "$CI_WORKFLOW"; then
    printf '%s\n' "GitHub Actions workflow must keep contract: $workflow_contract" >&2
    exit 1
  fi
done

if ! awk '
  /^  pull_request:$/ {
    found = 1
    if (getline <= 0 || $0 != "  push:") exit 1
  }
  END { if (!found) exit 1 }
' "$CI_WORKFLOW"; then
  printf '%s\n' "Pull request verification must apply without branch restrictions." >&2
  exit 1
fi

if ! grep -Fq "without contacting live CDC endpoints" "$ROOT_DIR/SECURITY.md" ||
  ! grep -Fq "Python 3.10, 3.12, and 3.14" "$ROOT_DIR/CHANGES.md" ||
  ! grep -Fq "docs/plans/2026-06-10-ci-baseline.md" "$ROOT_DIR/README.md"; then
  printf '%s\n' "Project docs must record the offline hosted Python matrix." >&2
  exit 1
fi
"$PYTHON" -m py_compile "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py"
"$PYTHON" -m unittest discover -s "$ROOT_DIR/tests" -p "test*.py"

if grep -Eq 'mechanize|cookielib|simplejson|BeautifulSoup|print ' "$ROOT_DIR/flushot.py" ||
  grep -Fq "http://www.cdc.gov/flu/weekly/" "$ROOT_DIR/flushot.py"; then
  printf '%s\n' "Scraper must stay Python 3 compatible and use the HTTPS CDC URL." >&2
  exit 1
fi

if ! grep -Fq "parse_records" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "write_outputs" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "fetch_html" "$ROOT_DIR/flushot.py"; then
  printf '%s\n' "Scraper must keep fetch, parse, and write concerns separated." >&2
  exit 1
fi

if ! grep -Fq "1 <= int(week_num) <= 53" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'Influenza Season Week (\d+)' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'datetime.strptime(week_end, "%B %d, %Y")' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_parse_records_rejects_out_of_range_week_number" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_parse_records_rejects_invalid_week_ending_date" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_parse_records_accepts_week_boundaries" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "for week_number in (1, 53)" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_parse_records_rejects_week_zero" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Parser must validate CDC week numbers and calendar dates." >&2
  exit 1
fi

if ! grep -Fq "def validate_fetch_url" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "urlparse" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'parsed.scheme != "https"' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "not hostname" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "parsed.username is not None" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "parsed.password is not None" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "parsed.query or parsed.fragment" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'hostname != "cdc.gov"' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'not hostname.endswith(".cdc.gov")' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "validate_fetch_url(url)" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_validate_fetch_url_requires_https_with_host" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_validate_fetch_url_rejects_embedded_credentials" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_validate_fetch_url_rejects_query_and_fragment" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "https://example.com/flu/weekly/" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Scraper must validate fetch URLs before opening network requests." >&2
  exit 1
fi

if ! grep -Fq "def fetch_timeout" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "timeout_value = int(value)" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "1 <= timeout_value <= 300" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "timeout_seconds = fetch_timeout(timeout)" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "timeout=timeout_seconds" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_fetch_timeout_rejects_invalid_or_out_of_range_values" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "not-a-timeout" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "301" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Scraper must validate live fetch timeouts before opening network requests." >&2
  exit 1
fi

if ! grep -Fq "class CDCNoRedirectHandler" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "validate_fetch_url(newurl)" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "CDC fetch redirects are not allowed" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "validate_fetch_url(response.geturl())" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "MAX_RESPONSE_BYTES = 2 * 1024 * 1024" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "def read_response_bytes" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_redirect_handler_revalidates_targets" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_read_response_rejects_streamed_oversize" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_fetch_html_uses_validated_bounded_response" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_fetch_html_rejects_untrusted_final_url" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Live CDC fetches must revalidate redirects and bound response resources." >&2
  exit 1
fi

if ! grep -Fq "lint: check" "$ROOT_DIR/Makefile" ||
  ! grep -Fq "test: check" "$ROOT_DIR/Makefile" ||
  ! grep -Fq "build: check" "$ROOT_DIR/Makefile"; then
  printf '%s\n' "Makefile must expose lint, test, and build gates." >&2
  exit 1
fi

if ! grep -Fq "def normalize_percent" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "normalize_percent(row[2])" "$ROOT_DIR/flushot.py"; then
  printf '%s\n' "Percent-positive values must be normalized through the parser helper." >&2
  exit 1
fi

if ! grep -Fq "EXPECTED_TABLE_HEADERS" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "def has_expected_summary_header" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "parser.tables" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "expected flu summary headers" "$ROOT_DIR/flushot.py"; then
  printf '%s\n' "Parser must validate the expected CDC summary table headers." >&2
  exit 1
fi

if ! grep -Fq "test_parse_records_fails_when_summary_header_is_missing" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_parse_records_skips_unrelated_matching_tables" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "Unexpected metric" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Tests must cover malformed and unrelated CDC summary table candidates." >&2
  exit 1
fi

if ! grep -Fq "has_expected_summary_header([row])" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "region = row[0].strip()" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_parse_records_skips_repeated_header_and_blank_region_rows" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Parser must skip repeated summary headers and rows without a region value." >&2
  exit 1
fi

if ! grep -Fq "for row in summary_rows[1:]" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_parse_records_without_subheading_keeps_first_region" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Parser must not require an extra non-data subheading row before region rows." >&2
  exit 1
fi

if ! grep -Fq "test_parse_records_trims_percent_spacing" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq " 12.5 % " "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Tests must cover percent-positive cells with spaced percent signs." >&2
  exit 1
fi

if ! grep -Fq "make check" "$ROOT_DIR/README.md" ||
  ! grep -Fq "fixture-based" "$ROOT_DIR/README.md" ||
  ! grep -Fq "expected flu summary headers" "$ROOT_DIR/README.md" ||
  ! grep -Fq "space before the" "$ROOT_DIR/README.md" ||
  ! grep -Fq "percent sign" "$ROOT_DIR/README.md" ||
  ! grep -Fq "CDC-owned hostnames" "$ROOT_DIR/README.md" ||
  ! grep -Fq "embedded credentials" "$ROOT_DIR/README.md" ||
  ! grep -Fq "fetch timeouts are bounded" "$ROOT_DIR/README.md" ||
  ! grep -Fq "GitHub Actions" "$ROOT_DIR/README.md" ||
  ! grep -Fq "docs/plans/2026-06-10-ci-baseline.md" "$ROOT_DIR/README.md" ||
  ! grep -Fq "flu.csv" "$ROOT_DIR/README.md" ||
  ! grep -Fq "flu.json" "$ROOT_DIR/README.md"; then
  printf '%s\n' "README must document verification, percent normalization, and generated outputs." >&2
  exit 1
fi

if ! grep -Fq "scripts/check-baseline.sh" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "Python 3" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "expected CDC summary table headers" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "matching summary table" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "CDC subdomains" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "embedded credentials" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "query strings or fragments" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "timeout values are bounded" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "GitHub Actions" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "Percent-positive cells are normalized" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "fixture-based tests" "$ROOT_DIR/VISION.md"; then
  printf '%s\n' "VISION must describe the current Python 3 parser and percent normalization baseline." >&2
  exit 1
fi

if ! grep -Fq "flu.csv" "$ROOT_DIR/.gitignore" ||
  ! grep -Fq "flu.json" "$ROOT_DIR/.gitignore" ||
  ! grep -Fq "__pycache__/" "$ROOT_DIR/.gitignore"; then
  printf '%s\n' "Generated outputs and Python caches must stay ignored." >&2
  exit 1
fi

if ! grep -Fq "GitHub Actions" "$ROOT_DIR/SECURITY.md" ||
  ! grep -Fq "GitHub Actions" "$ROOT_DIR/CHANGES.md"; then
  printf '%s\n' "Project docs must record the GitHub Actions CI baseline." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$PLAN"; then
  printf '%s\n' "Plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$PERCENT_PLAN"; then
  printf '%s\n' "Percent normalization plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$HEADER_PLAN"; then
  printf '%s\n' "Summary header guard plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$SUBHEADING_PLAN"; then
  printf '%s\n' "Optional subheading plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$TABLE_SELECTION_PLAN"; then
  printf '%s\n' "Table selection plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$SUMMARY_ROW_PLAN"; then
  printf '%s\n' "Summary row skip plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$FETCH_URL_PLAN"; then
  printf '%s\n' "Fetch URL validation plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$FETCH_HOST_PLAN"; then
  printf '%s\n' "Fetch host validation plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$FETCH_CREDENTIAL_PLAN"; then
  printf '%s\n' "Fetch credential guard plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$FETCH_URL_PARTS_PLAN"; then
  printf '%s\n' "Fetch URL parts guard plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "make check" "$FETCH_URL_PARTS_PLAN"; then
  printf '%s\n' "Fetch URL parts guard plan must record make check verification." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$FETCH_TIMEOUT_PLAN"; then
  printf '%s\n' "Fetch timeout validation plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "make check" "$FETCH_TIMEOUT_PLAN"; then
  printf '%s\n' "Fetch timeout validation plan must record make check verification." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$WEEK_METADATA_PLAN"; then
  printf '%s\n' "Flu week metadata validation plan must be marked completed." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$LIVE_FETCH_BOUNDARY_PLAN" ||
  ! grep -Fq "make check" "$LIVE_FETCH_BOUNDARY_PLAN"; then
  printf '%s\n' "Live fetch boundary plan must be completed and record verification." >&2
  exit 1
fi

python3 - "$DUPLICATE_REGION_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
verification = plan.split("## Verification Completed\n", 1)[-1]
required = (
    "All 22 offline tests",
    "Pull-request run `27392428650`",
    "push run `27392439231`",
    "CodeQL run `27402320646`",
)

if (
    statuses != ["status: completed"]
    or any(item not in verification for item in required)
    or re.search(r"\b(?:pending|todo|tbd|not run)\b", verification, re.IGNORECASE)
):
    raise SystemExit(
        "Duplicate region guard plan must remain completed with actual verification recorded."
    )
PY

if ! grep -Fq "status: completed" "$CI_PLAN" ||
  ! grep -Fq "make check" "$CI_PLAN"; then
  printf '%s\n' "CI baseline plan must be completed and record make check verification." >&2
  exit 1
fi
printf '%s\n' "flu-shot-data Python baseline checks passed."
