#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PLAN="$ROOT_DIR/docs/plans/2026-06-08-flu-shot-data-python3-baseline.md"
PERCENT_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-percent-normalization.md"
HEADER_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-summary-header-guard.md"
SUBHEADING_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-optional-subheading.md"
TABLE_SELECTION_PLAN="$ROOT_DIR/docs/plans/2026-06-09-flu-shot-table-selection.md"
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
  "CHANGES.md" \
  "Makefile" \
  "README.md" \
  "SECURITY.md" \
  "VISION.md" \
  "flushot.py" \
  "tests/test_flushot.py" \
  "tests/fixtures/cdc_weekly_summary.html" \
  "docs/plans/2026-06-09-flu-shot-optional-subheading.md" \
  "docs/plans/2026-06-09-flu-shot-table-selection.md" \
  "docs/plans/2026-06-09-flu-shot-summary-header-guard.md" \
  "docs/plans/2026-06-09-flu-shot-percent-normalization.md" \
  "docs/plans/2026-06-08-flu-shot-data-python3-baseline.md"; do
  require_file "$path"
done

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
  ! grep -Fq "space before the percent sign" "$ROOT_DIR/README.md" ||
  ! grep -Fq "flu.csv" "$ROOT_DIR/README.md" ||
  ! grep -Fq "flu.json" "$ROOT_DIR/README.md"; then
  printf '%s\n' "README must document verification, percent normalization, and generated outputs." >&2
  exit 1
fi

if ! grep -Fq "scripts/check-baseline.sh" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "Python 3" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "expected CDC summary table headers" "$ROOT_DIR/VISION.md" ||
  ! grep -Fq "matching summary table" "$ROOT_DIR/VISION.md" ||
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

printf '%s\n' "flu-shot-data Python baseline checks passed."
