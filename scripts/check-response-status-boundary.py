#!/usr/bin/env python3
import ast
import sys
from pathlib import Path


source_path = Path(sys.argv[1])
test_path = Path(sys.argv[2])
plan_path = Path(sys.argv[3])
source = source_path.read_text(encoding="utf-8")
tests = test_path.read_text(encoding="utf-8")
plan = plan_path.read_text(encoding="utf-8")

ast.parse(source)
ast.parse(tests)

required_source = [
    "def validate_response_status(response) -> None:",
    "if response.getcode() != 200:",
    'raise ValueError("CDC response status must be 200.")',
    "validate_response_status(response)",
]
for fragment in required_source:
    if fragment not in source:
        raise SystemExit("CDC response status boundary missing: " + fragment)

fetch_start = source.find("def fetch_html(")
status_check = source.find("validate_response_status(response)", fetch_start)
url_check = source.find("validate_fetch_url(response.geturl())", fetch_start)
content_type = source.find("validate_html_content_type(response.headers)", fetch_start)
content_encoding = source.find("validate_content_encoding(response.headers)", fetch_start)
body_read = source.find("read_response_bytes(response, max_bytes)", fetch_start)
positions = [fetch_start, status_check, url_check, content_type, content_encoding, body_read]
if -1 in positions or positions != sorted(positions):
    raise SystemExit(
        "CDC status validation must precede final URL, metadata, and body processing."
    )

required_tests = [
    "def getcode(self):",
    "return self.status",
]
for fragment in required_tests:
    if fragment not in tests:
        raise SystemExit("CDC response status regression missing: " + fragment)

test_name = "def test_fetch_html_requires_exact_success_status_before_metadata_or_body"
test_start = tests.find(test_name)
test_end = tests.find("\n    def ", test_start + len(test_name))
status_test = tests[test_start : None if test_end == -1 else test_end]
required_status_test = [
    test_name,
    "(199, 201, 204, 206, 301, 400, 404, 429, 500)",
    "wraps=flushot.validate_fetch_url",
    "self.assertEqual(0, response.read_calls)",
    "validate_url.assert_called_once_with(flushot.CDC_FLU_URL)",
]
for fragment in required_status_test:
    if fragment not in status_test:
        raise SystemExit("CDC response status regression missing: " + fragment)

for evidence in ("status: completed", "hostile mutations were rejected", "make check"):
    if evidence not in plan:
        raise SystemExit("CDC response status plan missing: " + evidence)

print("CDC response status boundary checks passed.")
