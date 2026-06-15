#!/usr/bin/env python3
import sys
from pathlib import Path


def function_body(source: str, function_name: str) -> str:
    marker = f"def {function_name}("
    start = source.find(marker)
    if start == -1:
        raise SystemExit(f"Required function missing: {function_name}")
    end = source.find("\ndef ", start + len(marker))
    return source[start:] if end == -1 else source[start:end]


def test_body(source: str, test_name: str) -> str:
    marker = f"    def {test_name}("
    start = source.find(marker)
    if start == -1:
        raise SystemExit(f"Required test missing: {test_name}")
    end = source.find("\n    def test_", start + len(marker))
    return source[start:] if end == -1 else source[start:end]


def require(source: str, value: str, message: str) -> None:
    if value not in source:
        raise SystemExit(message)


def main(source_path: Path, test_path: Path, plan_path: Path) -> None:
    source = source_path.read_text(encoding="utf-8")
    validator = function_body(source, "validate_html_content_type")
    tests = test_path.read_text(encoding="utf-8")
    direct_test = test_body(
        tests,
        "test_validate_response_content_type_rejects_duplicate_charset_parameters",
    )
    fetch_test = test_body(
        tests,
        "test_fetch_html_rejects_duplicate_charset_before_reading_body",
    )
    plan = plan_path.read_text(encoding="utf-8")

    for value, message in (
        ("message.get_params()[1:]", "Content-Type parameters must be inspected."),
        (
            'if name.lower() == "charset"',
            "Charset parameters must be matched case-insensitively.",
        ),
        (
            "if len(charset_parameters) > 1:",
            "Duplicate charset parameters must be rejected.",
        ),
        (
            "charset = message.get_content_charset()",
            "The single optional charset must use the parser's normalized value.",
        ),
    ):
        require(validator, value, message)

    for value in (
        "charset=utf-8; charset=utf-8",
        "charset=utf-8; charset=iso-8859-1",
        "charset*=utf-8''utf-8; charset=utf-8",
    ):
        require(direct_test, value, "Direct duplicate charset coverage is missing: " + value)

    for value in (
        "charset=utf-8; charset=iso-8859-1",
        "flushot.fetch_html(max_bytes=40)",
        "self.assertEqual(0, response.read_calls)",
    ):
        require(fetch_test, value, "Fetch-order charset coverage is missing: " + value)

    for value in (
        "status: completed",
        "hostile mutations were rejected",
        "make check",
    ):
        require(plan, value, "Duplicate charset plan evidence is missing: " + value)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: check-duplicate-charset.py SOURCE_FILE TEST_FILE PLAN_FILE"
        )
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
