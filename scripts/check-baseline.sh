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
CONTENT_TYPE_PLAN="$ROOT_DIR/docs/plans/2026-06-13-response-content-type-boundary.md"
STRICT_UTF8_PLAN="$ROOT_DIR/docs/plans/2026-06-13-strict-utf8-response-decoding.md"
CONTENT_ENCODING_PLAN="$ROOT_DIR/docs/plans/2026-06-13-response-content-encoding-boundary.md"
DUPLICATE_CONTENT_TYPE_PLAN="$ROOT_DIR/docs/plans/2026-06-13-duplicate-response-content-type.md"
LOCATION_INDEPENDENT_MAKE_PLAN="$ROOT_DIR/docs/plans/2026-06-13-location-independent-make.md"
RESPONSE_STATUS_PLAN="$ROOT_DIR/docs/plans/2026-06-14-response-status-boundary.md"
RESPONSE_STATUS_CHECK="$ROOT_DIR/scripts/check-response-status-boundary.py"
CONTENT_LENGTH_PLAN="$ROOT_DIR/docs/plans/2026-06-14-002-security-response-content-length-boundary-plan.md"
CONTENT_LENGTH_CHECK="$ROOT_DIR/scripts/check-content-length-boundary.py"
CONTENT_LENGTH_INTEGRITY_PLAN="$ROOT_DIR/docs/plans/2026-06-14-response-content-length-integrity.md"
CONTENT_LENGTH_INTEGRITY_CHECK="$ROOT_DIR/scripts/check-content-length-integrity.py"
DUPLICATE_CHARSET_PLAN="$ROOT_DIR/docs/plans/2026-06-15-duplicate-content-type-charset.md"
DUPLICATE_CHARSET_CHECK="$ROOT_DIR/scripts/check-duplicate-charset.py"
FETCH_PORT_PLAN="$ROOT_DIR/docs/plans/2026-06-15-cdc-fetch-port-boundary.md"
FETCH_PORT_CHECK="$ROOT_DIR/scripts/check-fetch-port-boundary.py"
OUTPUT_PATH_PLAN="$ROOT_DIR/docs/plans/2026-06-15-output-path-collision.md"
OUTPUT_PARENT_PLAN="$ROOT_DIR/docs/plans/2026-06-15-output-parent-preflight.md"
OUTPUT_RECORD_PLAN="$ROOT_DIR/docs/plans/2026-06-15-output-record-preflight.md"
PAIRED_OUTPUT_PLAN="$ROOT_DIR/docs/plans/2026-06-15-paired-output-publication.md"
CLEANUP_ERROR_PLAN="$ROOT_DIR/docs/plans/2026-06-16-output-cleanup-error-preservation.md"
STAGING_CLEANUP_PLAN="$ROOT_DIR/docs/plans/2026-06-16-staging-cleanup-error-preservation.md"
OUTPUT_TARGET_TYPE_PLAN="$ROOT_DIR/docs/plans/2026-06-17-output-target-type-preflight.md"
CI_PLAN="$ROOT_DIR/docs/plans/2026-06-10-ci-baseline.md"
CI_WORKFLOW="$ROOT_DIR/.github/workflows/check.yml"
CODEOWNERS="$ROOT_DIR/.github/CODEOWNERS"
PYTHON=${PYTHON:-python3}

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
  "docs/plans/2026-06-13-response-content-type-boundary.md" \
  "docs/plans/2026-06-13-strict-utf8-response-decoding.md" \
  "docs/plans/2026-06-13-response-content-encoding-boundary.md" \
  "docs/plans/2026-06-13-duplicate-response-content-type.md" \
  "docs/plans/2026-06-13-location-independent-make.md" \
  "docs/plans/2026-06-14-response-status-boundary.md" \
  "scripts/check-response-status-boundary.py" \
  "docs/plans/2026-06-14-002-security-response-content-length-boundary-plan.md" \
  "scripts/check-content-length-boundary.py" \
  "docs/plans/2026-06-14-response-content-length-integrity.md" \
  "scripts/check-content-length-integrity.py" \
  "docs/plans/2026-06-15-duplicate-content-type-charset.md" \
  "scripts/check-duplicate-charset.py" \
  "docs/plans/2026-06-15-cdc-fetch-port-boundary.md" \
  "scripts/check-fetch-port-boundary.py" \
  "docs/plans/2026-06-15-output-path-collision.md" \
  "docs/plans/2026-06-15-output-parent-preflight.md" \
  "docs/plans/2026-06-15-output-record-preflight.md" \
  "docs/plans/2026-06-15-paired-output-publication.md" \
  "docs/plans/2026-06-16-output-cleanup-error-preservation.md" \
  "docs/plans/2026-06-16-staging-cleanup-error-preservation.md" \
  "docs/plans/2026-06-17-output-target-type-preflight.md" \
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

python3 "$FETCH_PORT_CHECK" "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py"

python3 - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
tests = Path(sys.argv[2]).read_text()

source_contracts = (
    "def validate_output_paths(",
    "csv_output.resolve() == json_output.resolve()",
    "csv_output.samefile(json_output)",
    "except FileNotFoundError:",
    'raise ValueError("CSV and JSON outputs must use distinct filesystem targets.")',
    "csv_output, json_output = validate_output_paths(csv_path, json_path)",
)
if any(contract not in source for contract in source_contracts):
    raise SystemExit("Output writer must reject resolved and same-file destination collisions.")

test_contracts = (
    "test_write_outputs_rejects_identical_destinations_before_truncation",
    "test_write_outputs_rejects_symlink_aliases_before_truncation",
    "test_write_outputs_rejects_hard_link_aliases_before_truncation",
    'self.assertEqual(b"sentinel", output_path.read_bytes())',
)
if any(contract not in tests for contract in test_contracts):
    raise SystemExit("Output path collision regressions must preserve pre-existing bytes.")

writer = source[source.index("def write_outputs("):]
order = (
    "validate_output_paths(csv_path, json_path)",
    "records = validate_output_records(records)",
    "stage_outputs(records, csv_output, json_output)",
    "publish_output_pair(((csv_output, csv_stage), (json_output, json_stage)))",
)
if any(contract not in writer for contract in order):
    raise SystemExit("Output destinations and records must be validated before staging and publication.")
positions = [writer.index(contract) for contract in order]
if positions != sorted(positions):
    raise SystemExit("Output destinations and records must be validated before staging and publication.")

stage_writer = source[source.index("def stage_outputs("):source.index("def move_existing_output_to_backup(")]
if 'csv_stage.open("w"' not in stage_writer or 'json_stage.open("w"' not in stage_writer:
    raise SystemExit("Complete output staging must write only invocation-owned stage paths.")
if 'csv_output.open("w"' in source or 'json_output.open("w"' in source:
    raise SystemExit("Validated output destinations must not be opened directly for writing.")
PY

"$PYTHON" "$RESPONSE_STATUS_CHECK" \
  "$ROOT_DIR/flushot.py" \
  "$ROOT_DIR/tests/test_flushot.py" \
  "$RESPONSE_STATUS_PLAN"

"$PYTHON" "$CONTENT_LENGTH_CHECK" \
  "$ROOT_DIR/flushot.py" \
  "$ROOT_DIR/tests/test_flushot.py" \
  "$CONTENT_LENGTH_PLAN"

"$PYTHON" "$CONTENT_LENGTH_INTEGRITY_CHECK" \
  "$ROOT_DIR/flushot.py" \
  "$ROOT_DIR/tests/test_flushot.py" \
  "$CONTENT_LENGTH_INTEGRITY_PLAN"

"$PYTHON" "$DUPLICATE_CHARSET_CHECK" \
  "$ROOT_DIR/flushot.py" \
  "$ROOT_DIR/tests/test_flushot.py" \
  "$DUPLICATE_CHARSET_PLAN"

if ! grep -Fq 'override ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))' "$ROOT_DIR/Makefile" ||
  ! grep -Fq '"$(ROOT)/scripts/check-baseline.sh"' "$ROOT_DIR/Makefile"; then
  printf '%s\n' "Makefile verification must protect the loaded Makefile root from overrides." >&2
  exit 1
fi

if ! grep -Fq '(cd "$ROOT_DIR" &&' "$ROOT_DIR/scripts/check-baseline.sh" ||
  ! grep -Fq 'PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -m unittest discover -s tests -p "test*.py")' "$ROOT_DIR/scripts/check-baseline.sh"; then
  printf '%s\n' "Offline Python verification must run from the repository root." >&2
  exit 1
fi

recursive_remove='rm -''rf'
find_delete='-de''lete'
if grep -Fq -- "$recursive_remove" "$ROOT_DIR/scripts/check-baseline.sh" ||
  grep -Fq -- "$find_delete" "$ROOT_DIR/scripts/check-baseline.sh" ||
  ! grep -Fq 'compile(path.read_bytes(), str(path), "exec")' "$ROOT_DIR/scripts/check-baseline.sh"; then
  printf '%s\n' "Offline verification must compile in memory without recursive artifact cleanup." >&2
  exit 1
fi

if ! grep -Fq "status: completed" "$LOCATION_INDEPENDENT_MAKE_PLAN" ||
  ! grep -Fq "from /tmp" "$LOCATION_INDEPENDENT_MAKE_PLAN" ||
  ! grep -Fq "absolute Makefile path" "$ROOT_DIR/README.md" ||
  ! grep -Fq "Made offline verification independent" "$ROOT_DIR/CHANGES.md"; then
  printf '%s\n' "Location-independent Make plan and guidance must record completed external verification." >&2
  exit 1
fi

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
"$PYTHON" - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" <<'PY'
import sys
from pathlib import Path

for raw_path in sys.argv[1:]:
    path = Path(raw_path)
    compile(path.read_bytes(), str(path), "exec")
PY
(cd "$ROOT_DIR" &&
  PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -m unittest discover -s tests -p "test*.py")

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
  ! grep -Fq "test_validate_fetch_url_rejects_explicit_or_malformed_ports" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_fetch_html_rejects_explicit_port_before_building_opener" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "https://example.com/flu/weekly/" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Scraper must validate fetch URLs before opening network requests." >&2
  exit 1
fi

for fetch_port_doc in AGENTS.md README.md SECURITY.md VISION.md CHANGES.md; do
  if ! grep -Fq "Live CDC fetch URLs reject every explicit port before network request construction or redirect handling." "$ROOT_DIR/$fetch_port_doc"; then
    printf '%s\n' "$fetch_port_doc must document the explicit fetch-port boundary." >&2
    exit 1
  fi
done

for fetch_port_plan_contract in \
  "status: completed" \
  "## Status: Completed" \
  "## Work Completed" \
  "## Verification Completed" \
  "hostile mutations were rejected"; do
  if ! grep -Fq "$fetch_port_plan_contract" "$FETCH_PORT_PLAN"; then
    printf '%s\n' "Fetch port plan must record completed evidence: $fetch_port_plan_contract" >&2
    exit 1
  fi
done

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

if ! grep -Fq "def validate_html_content_type" "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'get_all("Content-Type", [])' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'len(content_types) > 1' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'media_type != "text/html"' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq 'charset.lower() not in {"utf-8", "utf8"}' "$ROOT_DIR/flushot.py" ||
  ! grep -Fq "test_validate_response_content_type_accepts_utf8_html" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_validate_response_content_type_rejects_missing_or_incompatible_values" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_fetch_html_rejects_content_type_before_reading_body" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "test_fetch_html_rejects_duplicate_content_type_before_reading_body" "$ROOT_DIR/tests/test_flushot.py" ||
  ! grep -Fq "self.assertEqual(0, response.read_calls)" "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Live CDC fetches must validate HTML and UTF-8 response metadata before body reads." >&2
  exit 1
fi

python3 - "$ROOT_DIR/flushot.py" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
fetch = source.split("def fetch_html(", 1)[-1].split("\ndef parse_week_metadata", 1)[0]
contract = (
    "validate_fetch_url(response.geturl())",
    "validate_html_content_type(response.headers)",
    "read_response_bytes(response, max_bytes)",
)
positions = [fetch.find(fragment) for fragment in contract]
if -1 in positions or positions != sorted(positions) or len(set(positions)) != len(positions):
    raise SystemExit("Final URL and response metadata validation must remain ahead of body reads.")
PY

python3 - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
tests = Path(sys.argv[2]).read_text()
validator = source.split("def validate_html_content_type", 1)[-1].split(
    "\ndef validate_content_encoding", 1
)[0]
required_validator = (
    'get_all = getattr(headers, "get_all", None)',
    'content_types = get_all("Content-Type", [])',
    "content_types = [] if content_type is None else [content_type]",
    "if len(content_types) > 1:",
    'raise ValueError("CDC response must declare exactly one Content-Type.")',
)
if any(item not in validator for item in required_validator):
    raise SystemExit("Live responses must reject duplicate Content-Type fields.")

test_name = "def test_fetch_html_rejects_duplicate_content_type_before_reading_body"
if tests.count(test_name) != 1:
    raise SystemExit("Focused tests must keep one duplicate Content-Type regression.")
test = tests.split(test_name, 1)[-1].split("\n    def ", 1)[0]
required_test = (
    '"text/html; charset=utf-8",',
    '"application/json",',
    'headers["Content-Type"] = second_content_type',
    "self.assertEqual(0, response.read_calls)",
)
if any(item not in test for item in required_test):
    raise SystemExit("Duplicate Content-Type tests must cover matching and conflicting fields before reads.")
PY

python3 - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
tests = Path(sys.argv[2]).read_text()
validator = source.split("def validate_content_encoding", 1)[-1].split(
    "\ndef read_response_bytes", 1
)[0]
required_validator = (
    'get_all = getattr(headers, "get_all", None)',
    'content_encodings = get_all("Content-Encoding", [])',
    "content_encodings = [] if content_encoding is None else [content_encoding]",
    "if not content_encodings:",
    "if len(content_encodings) != 1:",
    "content_encoding = content_encodings[0]",
    "normalized_encoding = content_encoding.strip().lower()",
    'if normalized_encoding != "identity":',
    'raise ValueError("CDC response Content-Encoding must be identity.")',
)
if any(item not in validator for item in required_validator):
    raise SystemExit("Live responses must allow only absent or identity content encoding.")

fetch = source.split("def fetch_html", 1)[-1].split("\ndef parse_week_metadata", 1)[0]
ordered = (
    "validate_fetch_url(response.geturl())",
    "validate_html_content_type(response.headers)",
    "validate_content_encoding(response.headers)",
    "response_bytes = read_response_bytes(response, max_bytes)",
    "return decode_html_bytes(response_bytes)",
)
positions = [fetch.find(item) for item in ordered]
if -1 in positions or positions != sorted(positions) or len(set(positions)) != len(positions):
    raise SystemExit("Content encoding must be validated before reading response bytes.")

accepted_name = "def test_fetch_html_accepts_absent_or_identity_content_encoding"
rejected_name = "def test_fetch_html_rejects_unsupported_content_encoding_before_reading_body"
if tests.count(accepted_name) != 1 or tests.count(rejected_name) != 1:
    raise SystemExit("Focused tests must preserve both content-encoding regressions.")
accepted_test = tests.split(accepted_name, 1)[-1].split("\n    def ", 1)[0]
rejected_test = tests.split(rejected_name, 1)[-1].split("\n    def ", 1)[0]
required_accepted = (
    'for content_encoding in (None, "identity", " IDENTITY ")',
    "self.assertGreater(response.read_calls, 0)",
)
required_rejected = (
    'for content_encoding in ("", "gzip", "deflate", "br", "identity, gzip")',
    "flushot.fetch_html(max_bytes=40)",
    'duplicate_headers["Content-Encoding"] = "identity"',
    'duplicate_headers["Content-Encoding"] = "gzip"',
    "self.assertEqual(0, response.read_calls)",
)
if any(item not in accepted_test for item in required_accepted) or any(
    item not in rejected_test for item in required_rejected
):
    raise SystemExit("Focused tests must preserve identity-only encoding and no-read rejection coverage.")
PY

python3 - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
tests = Path(sys.argv[2]).read_text()
decode = source.split("def decode_html_bytes(", 1)[-1].split("\ndef fetch_html", 1)[0]
fetch = source.split("def fetch_html(", 1)[-1].split("\ndef parse_week_metadata", 1)[0]

required_decode = (
    'body.decode("utf-8")',
    "except UnicodeDecodeError:",
    'raise ValueError("CDC response body must be valid UTF-8.") from None',
)
required_tests = (
    "test_fetch_html_preserves_valid_multibyte_utf8",
    "test_fetch_html_rejects_malformed_utf8_without_leaking_body",
    'b"<html>private-\\xff-value</html>"',
    "bounded_read.assert_called_once_with(response, 40)",
    "self.assertIsNone(error.exception.__cause__)",
)
fetch_contract = (
    "validate_fetch_url(response.geturl())",
    "validate_html_content_type(response.headers)",
    "response_bytes = read_response_bytes(response, max_bytes)",
    "return decode_html_bytes(response_bytes)",
)
positions = [fetch.find(fragment) for fragment in fetch_contract]

if any(fragment not in decode for fragment in required_decode):
    raise SystemExit("Live response bytes must use strict UTF-8 with generic error translation.")
if 'errors="replace"' in source or 'errors="ignore"' in source:
    raise SystemExit("Live response decoding must not use lossy UTF-8 error handling.")
if any(fragment not in tests for fragment in required_tests):
    raise SystemExit("Strict UTF-8 behavior must retain focused valid and malformed response tests.")
if -1 in positions or positions != sorted(positions) or len(set(positions)) != len(positions):
    raise SystemExit("Strict UTF-8 decoding must remain after bounded response reading.")
PY

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

if ! grep -Fq "absent or one explicit identity Content-Encoding" "$ROOT_DIR/README.md" ||
  ! grep -Fq 'absent or one explicit identity `Content-Encoding`' "$ROOT_DIR/SECURITY.md" ||
  ! grep -Fq "identity-only content encoding" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "identity-only response content encoding" "$ROOT_DIR/CHANGES.md" ||
  ! grep -Fq 'identity-only `Content-Encoding`' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Repository guidance must document the response content-encoding boundary." >&2
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

if ! grep -Fq 'exactly one `text/html` field' "$ROOT_DIR/README.md" ||
  ! grep -Fq 'exactly one `text/html` field' "$ROOT_DIR/SECURITY.md" ||
  ! grep -Fq "exactly one HTML media metadata field" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq 'Required live CDC responses to declare `text/html`' "$ROOT_DIR/CHANGES.md"; then
  printf '%s\n' "Project docs must record the response content-type boundary." >&2
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

python3 - "$CONTENT_TYPE_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "validator removal mutation failed",
    "media allowlist mutation failed",
    "validation ordering mutation failed",
    "hosted pull-request check",
)

if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Response content-type plan must record completed status and actual verification."
    )
PY

python3 - "$STRICT_UTF8_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "lossy decode mutation failed",
    "exception translation mutation failed",
    "malformed-byte test mutation failed",
    "decode ordering mutation failed",
    "hosted pull-request check",
)

if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Strict UTF-8 response plan must record completed status and actual verification."
    )
PY

python3 - "$CONTENT_ENCODING_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "validator removal mutation failed",
    "gzip allowlist mutation failed",
    "duplicate-field mutation failed",
    "validation ordering mutation failed",
    "no-read assertion mutation failed",
    "plan evidence mutation failed",
    "hosted pull-request check",
)
if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Response content-encoding plan must record completed status and actual verification."
    )
verification = plan.split("## Verification Completed\n", 1)[-1]
if re.search(r"\b(?:pending|todo|tbd|not run)\b", verification, re.IGNORECASE):
    raise SystemExit("Response content-encoding verification must not remain pending.")
PY

python3 - "$DUPLICATE_CONTENT_TYPE_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "six hostile mutations were rejected",
    "all four Make gates passed",
    "No live CDC request was made",
    "hosted pull-request check",
)
if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Duplicate Content-Type plan must record completed status and actual verification."
    )
PY

if ! grep -Fq 'exactly one `text/html` field' "$ROOT_DIR/README.md" ||
  ! grep -Fq 'exactly one `text/html` field' "$ROOT_DIR/SECURITY.md" ||
  ! grep -Fq "exactly one HTML media metadata field" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "Rejected duplicate CDC response Content-Type fields" "$ROOT_DIR/CHANGES.md" ||
  ! grep -Fq 'Require exactly one HTML `Content-Type` field' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Project docs must preserve duplicate Content-Type rejection." >&2
  exit 1
fi

if ! grep -Fq 'distinct filesystem targets' "$ROOT_DIR/README.md" ||
  ! grep -Fq 'distinct filesystem targets' "$ROOT_DIR/SECURITY.md" ||
  ! grep -Fq 'same-file output destination collisions' "$ROOT_DIR/VISION.md" ||
  ! grep -Fq 'Rejected colliding CSV and JSON output destinations' "$ROOT_DIR/CHANGES.md" ||
  ! grep -Fq 'output destinations filesystem-distinct' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Project docs must preserve output destination collision rejection." >&2
  exit 1
fi

python3 - "$OUTPUT_PATH_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "all 44 offline tests",
    "repository and external-directory `make check`",
    "Seven isolated hostile mutations were rejected",
    "No live CDC request was made",
)
if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Output path collision plan must record completed status and actual verification."
    )
PY

if ! grep -Fq 'for output in (csv_output, json_output):' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'if not output.parent.resolve().is_dir():' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'test_write_outputs_rejects_missing_parent_before_truncation' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_rejects_non_directory_parent_before_truncation' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'self.assertEqual(b"sentinel", csv_path.read_bytes())' "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Output parents must be preflighted before either destination is truncated." >&2
  exit 1
fi

if ! grep -Fq 'existing directory before either file is opened' "$ROOT_DIR/README.md" || \
  ! grep -Fq 'be existing directories before either' "$ROOT_DIR/SECURITY.md" || \
  ! grep -Fq 'Preflight both output parent directories' "$ROOT_DIR/VISION.md" || \
  ! grep -Fq 'Preflighted CSV and JSON output parent directories' "$ROOT_DIR/CHANGES.md" || \
  ! grep -Fq 'output parents as existing directories' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Project docs must preserve output-parent preflight behavior." >&2
  exit 1
fi

python3 - "$OUTPUT_PARENT_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "all 46 offline tests",
    "repository and external-directory `make check`",
    "Six isolated hostile mutations were rejected",
    "No live CDC request was made",
)
if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Output parent preflight plan must record completed status and actual verification."
    )
PY

if ! grep -Fq 'def validate_output_records(' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'records = validate_output_records(records)' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'set(record) != expected_headers' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'if not isinstance(value, str):' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'value.encode("utf-8")' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'test_write_outputs_rejects_extra_fields_before_truncation' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_rejects_non_dictionary_rows_before_truncation' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_rejects_non_string_values_before_truncation' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_rejects_invalid_utf8_before_truncation' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'self.assertEqual(b"json sentinel", json_path.read_bytes())' "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Output records must be fully validated before either destination is truncated." >&2
  exit 1
fi

if ! grep -Fq 'exact documented headers, string values, and' "$ROOT_DIR/README.md" || \
  ! grep -Fq 'documented header set and contain only valid' "$ROOT_DIR/SECURITY.md" || \
  ! grep -Fq 'Preflight the complete output record schema' "$ROOT_DIR/VISION.md" || \
  ! grep -Fq 'Preflighted output record headers, value types, and UTF-8 text' "$ROOT_DIR/CHANGES.md" || \
  ! grep -Fq 'exact-header, string-value, and strict UTF-8 output record' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Project docs must preserve output-record preflight behavior." >&2
  exit 1
fi

python3 - "$OUTPUT_RECORD_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "all 50 offline tests",
    "repository-root and external-directory `make check`",
    "Seven isolated hostile mutations were rejected",
    "No live CDC request was made",
)
if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Output record preflight plan must record completed status and actual verification."
    )
PY

if ! grep -Fq 'def stage_outputs(' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'def reserve_output_stage(output: Path)' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'def cleanup_output_paths(paths: Iterable[Path])' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'cleanup_output_paths(' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'creation_mode=0o666' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'stage.chmod(existing_mode)' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'def move_existing_output_to_backup(output: Path)' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'def publish_output_pair(' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'os.replace(state["stage"], state["output"])' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'for state in reversed(states):' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'retain_recovery_backups = True' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'recovery backups were retained' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'active_error = sys.exc_info()[1]' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'cleanup_error = None' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'if cleanup_error is None:' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'if cleanup_error is not None and active_error is None:' "$ROOT_DIR/flushot.py" || \
  ! grep -Fq 'test_write_outputs_preserves_pair_when_json_staging_fails' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_cleanup_failure_does_not_mask_staging_failure' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_cleanup_failure_does_not_mask_mode_preservation_failure' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_preserves_destination_modes' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_preserves_distinct_symlink_destinations' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_cleans_first_stage_when_second_reservation_fails' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_cleans_stage_when_mode_preservation_fails' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_rolls_back_pair_when_second_publication_fails' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_rolls_back_pair_when_second_backup_fails' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_removes_new_pair_when_second_publication_fails' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_write_outputs_retains_backup_when_rollback_is_incomplete' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_cleanup_failure_does_not_mask_publication_failure' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_cleanup_failure_does_not_mask_incomplete_rollback' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'test_successful_publication_attempts_all_cleanup_after_failure' "$ROOT_DIR/tests/test_flushot.py" || \
  ! grep -Fq 'self.assertEqual({"flu.csv", "flu.json"}, set(os.listdir(tmpdir)))' "$ROOT_DIR/tests/test_flushot.py"; then
  printf '%s\n' "Paired outputs must stage completely, roll back publication failures, and clean invocation artifacts." >&2
  exit 1
fi

if ! grep -Fq 'staged completely before either destination is replaced' "$ROOT_DIR/README.md" || \
  ! grep -Fq 'every remaining invocation-owned cleanup is still attempted' "$ROOT_DIR/README.md" || \
  ! grep -Fq 'handled staging or publication exceptions' "$ROOT_DIR/SECURITY.md" || \
  ! grep -Fq 'Cleanup failures must not mask a primary staging' "$ROOT_DIR/SECURITY.md" || \
  ! grep -Fq 'Roll back paired output publication failures' "$ROOT_DIR/VISION.md" || \
  ! grep -Fq 'Preserve primary staging and publication failures across cleanup errors' "$ROOT_DIR/VISION.md" || \
  ! grep -Fq 'Added rollback-capable paired CSV and JSON publication' "$ROOT_DIR/CHANGES.md" || \
  ! grep -Fq 'Preserved primary paired-publication and incomplete-rollback errors' "$ROOT_DIR/CHANGES.md" || \
  ! grep -Fq 'Preserve paired output rollback and invocation-owned artifact cleanup' "$ROOT_DIR/AGENTS.md" || \
  ! grep -Fq 'Do not let stage or backup cleanup errors mask primary staging' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Project docs must preserve paired-output publication behavior and boundaries." >&2
  exit 1
fi

python3 - "$PAIRED_OUTPUT_PLAN" <<'PY'
import re
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required = (
    "all 59 offline tests",
    "repository-root and external-directory `make check`",
    "isolated hostile mutations were rejected",
    "No live CDC request was made",
    "does not claim multi-path crash or power-loss atomicity",
)
if statuses != ["status: completed"] or any(item not in plan for item in required):
    raise SystemExit(
        "Paired output publication plan must record completed status, actual verification, and the crash-atomicity boundary."
    )
PY

"$PYTHON" - "$CLEANUP_ERROR_PLAN" <<'PY'
import sys
from pathlib import Path

plan = Path(sys.argv[1]).read_text()
normalized_plan = " ".join(plan.split())
required = (
    "Status: Completed",
    "All 62 offline tests passed",
    "Repository-root and external-directory `make check` passed",
    "Six isolated mutations were rejected",
    "no live CDC request was made",
    "does not claim process-crash, kernel, filesystem, or power-loss atomicity",
)
if any(item not in normalized_plan for item in required):
    raise SystemExit(
        "Output cleanup error preservation plan must record completed status, "
        "actual verification, and the crash-atomicity boundary."
    )
PY

"$PYTHON" - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" "$STAGING_CLEANUP_PLAN" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
tests = Path(sys.argv[2]).read_text()
plan = " ".join(Path(sys.argv[3]).read_text().split())

stage_writer = source[source.index("def stage_outputs("):source.index("def move_existing_output_to_backup(")]
stage_reservation = source[source.index("def reserve_output_stage("):source.index("def stage_outputs(")]
required_tests = (
    "test_cleanup_failure_does_not_mask_staging_failure",
    "test_cleanup_failure_does_not_mask_mode_preservation_failure",
)
required_plan = (
    "Status: Completed",
    "All 64 offline tests passed",
    "Repository-root and external-directory `make check` passed",
    "Five isolated mutations were rejected",
    "no live CDC request was made",
    "does not claim process-crash, kernel, filesystem, or power-loss atomicity",
)

if "cleanup_output_paths(" not in stage_writer or ".unlink(" in stage_writer:
    raise SystemExit("Staging failures must use shared cleanup without masking the primary error.")
if "cleanup_output_paths((stage,))" not in stage_reservation or ".unlink(" in stage_reservation:
    raise SystemExit("Mode-preservation failures must not be masked by stage cleanup.")
if any(name not in tests for name in required_tests):
    raise SystemExit("Staging cleanup regressions must remain registered.")
if any(item not in plan for item in required_plan):
    raise SystemExit(
        "Staging cleanup error preservation plan must record completed status, "
        "actual verification, and the crash-atomicity boundary."
    )
PY
"$PYTHON" - "$ROOT_DIR/flushot.py" "$ROOT_DIR/tests/test_flushot.py" "$OUTPUT_TARGET_TYPE_PLAN" <<'PY'
import sys
from pathlib import Path

source = Path(sys.argv[1]).read_text()
tests = Path(sys.argv[2]).read_text()
plan = " ".join(Path(sys.argv[3]).read_text().split())

validator = source[source.index("def validate_output_paths("):source.index("def validate_output_records(")]
required_validator = (
    "output_mode = resolved_output.stat().st_mode",
    "except FileNotFoundError:",
    "if not stat.S_ISREG(output_mode):",
    'raise ValueError("Each existing output target must be a regular file.")',
)
required_tests = (
    "test_write_outputs_rejects_csv_directory_target_before_staging",
    "test_write_outputs_rejects_json_directory_target_before_staging",
    "test_write_outputs_rejects_csv_fifo_target_before_staging",
    "test_write_outputs_rejects_json_fifo_target_before_staging",
    'glob(".*.stage-*")',
    'glob(".*.backup-*")',
)
required_plan = (
    "status: completed",
    "All 68 offline tests passed",
    "Repository-root and external-directory `make check` passed",
    "Eight isolated mutations were rejected",
    "Hosted run `27673714464` passed",
    "`363d61aebae31c41ba769014551104bb24172afd`",
    "no live CDC request was made",
    "does not claim crash, kernel, filesystem, or power-loss atomicity",
)

if any(item not in validator for item in required_validator):
    raise SystemExit("Existing output targets must be regular files before staging.")
if any(item not in tests for item in required_tests):
    raise SystemExit("Directory and FIFO output-target regressions must remain registered.")
if any(item not in plan for item in required_plan):
    raise SystemExit(
        "Output target type preflight plan must record completed status, "
        "actual verification, and the crash-atomicity boundary."
    )
PY
if ! grep -Fq 'Each existing resolved destination must be a regular file' "$ROOT_DIR/README.md" || \
  ! grep -Fq 'Existing resolved output destinations must be regular files' "$ROOT_DIR/SECURITY.md" || \
  ! grep -Fq 'Reject existing non-regular output targets before staging or publication' "$ROOT_DIR/VISION.md" || \
  ! grep -Fq 'Rejected existing directory and special-file output targets before staging' "$ROOT_DIR/CHANGES.md" || \
  ! grep -Fq 'Preserve regular-file validation for existing resolved output targets' "$ROOT_DIR/AGENTS.md"; then
  printf '%s\n' "Project guidance must preserve the regular-file output target boundary." >&2
  exit 1
fi
printf '%s\n' "flu-shot-data Python baseline checks passed."
