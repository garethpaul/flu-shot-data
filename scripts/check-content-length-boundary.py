#!/usr/bin/env python3
import re
import sys
from pathlib import Path


source_path, tests_path, plan_path = map(Path, sys.argv[1:4])
source = source_path.read_text()
tests = tests_path.read_text()
plan = plan_path.read_text()

required_source = (
    'get_all = getattr(headers, "get_all", None)',
    'content_lengths = get_all("Content-Length", [])',
    'if len(content_lengths) > 1:',
    're.fullmatch(r"[0-9]+", content_length)',
    "validate_content_length(response.headers, max_bytes)",
)
for fragment in required_source:
    if fragment not in source:
        raise SystemExit("CDC Content-Length boundary missing: " + fragment)

validator = source.split("def validate_content_length", 1)[-1].split(
    "def read_response_bytes", 1
)[0]
if "response.read" in validator:
    raise SystemExit("CDC Content-Length validation must precede body reads.")

required_tests = (
    "test_read_response_accepts_missing_or_exact_content_length",
    "test_read_response_rejects_duplicate_content_length_before_reading",
    "test_read_response_rejects_noncanonical_content_length_before_reading",
    "test_read_response_rejects_streamed_oversize_after_smaller_declaration",
    "self.assertEqual(0, response.read_calls)",
)
for fragment in required_tests:
    if fragment not in tests:
        raise SystemExit("CDC Content-Length regression missing: " + fragment)

frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required_plan = (
    "focused response-length tests",
    "isolated hostile mutations",
    "make check",
)
plan_lower = plan.lower()
if statuses != ["status: completed"] or any(
    item not in plan_lower for item in required_plan
):
    raise SystemExit(
        "Response Content-Length plan must record completed status and verification."
    )

print("CDC response Content-Length boundary checks passed.")
