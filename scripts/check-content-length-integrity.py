#!/usr/bin/env python3
import re
import sys
from pathlib import Path


source_path, tests_path, plan_path = map(Path, sys.argv[1:4])
source = source_path.read_text()
tests = tests_path.read_text()
plan = plan_path.read_text()

required_source = (
    "def validate_content_length(headers, max_bytes: int) -> int | None:",
    "return None",
    "return declared_length",
    "declared_length = validate_content_length(response.headers, max_bytes)",
    "if declared_length is not None and total_bytes != declared_length:",
    'raise ValueError("CDC response body does not match Content-Length.")',
)
for fragment in required_source:
    if fragment not in source:
        raise SystemExit("CDC Content-Length integrity missing: " + fragment)

reader = source.split("def read_response_bytes", 1)[-1].split(
    "def decode_html_bytes", 1
)[0]
if reader.index("while True:") > reader.index("total_bytes != declared_length"):
    raise SystemExit("CDC Content-Length equality must be checked after streaming.")

required_tests = (
    "test_read_response_accepts_missing_or_exact_content_length",
    "test_read_response_rejects_body_shorter_than_content_length",
    "test_read_response_rejects_body_longer_than_content_length",
    'self.assertRaisesRegex(ValueError, "does not match Content-Length")',
)
for fragment in required_tests:
    if fragment not in tests:
        raise SystemExit("CDC Content-Length integrity regression missing: " + fragment)

frontmatter = plan.split("---", 2)[1]
statuses = re.findall(r"^status: .+$", frontmatter, flags=re.MULTILINE)
required_plan = (
    "focused unit tests",
    "isolated hostile mutations",
    "root and external-directory `make check`",
)
plan_lower = plan.lower()
if statuses != ["status: completed"] or any(
    item not in plan_lower for item in required_plan
):
    raise SystemExit(
        "Response Content-Length integrity plan must record completed status and verification."
    )

print("CDC response Content-Length integrity checks passed.")
