import csv
import json
import os
import tempfile
import unittest
from email.message import Message
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

import flushot


FIXTURE = Path(__file__).parent / "fixtures" / "cdc_weekly_summary.html"


class FakeResponse:
    def __init__(self, body=b"", url=flushot.CDC_FLU_URL, headers=None, status=200):
        self.body = BytesIO(body)
        self.url = url
        self.headers = headers or {}
        self.status = status
        self.read_calls = 0

    def read(self, size=-1):
        self.read_calls += 1
        return self.body.read(size)

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return self.response


class FluShotParserTests(unittest.TestCase):
    def test_parse_records_from_fixture(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(2, len(records))
        self.assertEqual("12", records[0]["WEEK_NUM"])
        self.assertEqual("March 23, 2024", records[0]["WEEK_END"])
        self.assertEqual("National", records[0]["HHS_REGION"])
        self.assertEqual("12.5", records[0]["PCT_FLU_POS"])
        self.assertEqual("Region 1", records[1]["HHS_REGION"])

    def test_parse_records_trims_percent_spacing(self):
        html = FIXTURE.read_text(encoding="utf-8").replace("12.5%", " 12.5 % ")
        records = flushot.parse_records(html)

        self.assertEqual("12.5", records[0]["PCT_FLU_POS"])

    def test_parse_records_without_subheading_keeps_first_region(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "      <tr>\n"
            "        <th colspan=\"9\">National and Regional Summary</th>\n"
            "      </tr>\n",
            "",
        )
        records = flushot.parse_records(html)

        self.assertEqual(2, len(records))
        self.assertEqual("National", records[0]["HHS_REGION"])

    def test_parse_records_skips_unrelated_matching_tables(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "    <table cellpadding=\"3\">",
            "    <table cellpadding=\"3\">\n"
            "      <tr><th>Unrelated</th><th>Count</th></tr>\n"
            "      <tr><td>Before summary</td><td>1</td></tr>\n"
            "    </table>\n"
            "    <table cellpadding=\"3\">",
            1,
        )
        records = flushot.parse_records(html)

        self.assertEqual(2, len(records))
        self.assertEqual("National", records[0]["HHS_REGION"])

    def test_parse_records_skips_repeated_header_and_blank_region_rows(self):
        header = (
            "      <tr>\n"
            "        <th>Region</th>\n"
            "        <th>ILI</th>\n"
            "        <th>Percent positive</th>\n"
            "        <th>Jurisdictions</th>\n"
            "        <th>A H3</th>\n"
            "        <th>A 2009 H1N1</th>\n"
            "        <th>A no subtype</th>\n"
            "        <th>B</th>\n"
            "        <th>Ped deaths</th>\n"
            "      </tr>"
        )
        blank_region = (
            "      <tr><td> </td><td>1.0</td><td>2%</td><td>1</td>"
            "<td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>"
        )
        html = FIXTURE.read_text(encoding="utf-8").replace(
            header,
            f"{header}\n{header}\n{blank_region}",
            1,
        )

        records = flushot.parse_records(html)

        self.assertEqual(2, len(records))
        self.assertEqual(["National", "Region 1"], [row["HHS_REGION"] for row in records])

    def test_parse_records_rejects_duplicate_regions_case_insensitively(self):
        duplicate_row = (
            "      <tr>\n"
            "        <td><strong>{region}</strong></td>\n"
            "        <td>2.1</td><td>8.1%</td><td>6</td>\n"
            "        <td>3</td><td>4</td><td>0</td><td>1</td><td>0</td>\n"
            "      </tr>\n"
        )

        for region in ("Region 1", "region 1"):
            with self.subTest(region=region):
                html = FIXTURE.read_text(encoding="utf-8").replace(
                    "    </table>",
                    duplicate_row.format(region=region) + "    </table>",
                )

                with self.assertRaisesRegex(ValueError, "duplicate region"):
                    flushot.parse_records(html)

    def test_write_outputs_uses_expected_schema(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            with csv_path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            with json_path.open(encoding="utf-8") as json_file:
                json_rows = json.load(json_file)

        self.assertEqual(flushot.HEADERS, list(rows[0].keys()))
        self.assertEqual(rows, json_rows)

    def test_write_outputs_rejects_identical_destinations_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flu-output"
            output_path.write_bytes(b"sentinel")

            with self.assertRaisesRegex(ValueError, "distinct filesystem targets"):
                flushot.write_outputs(
                    records,
                    csv_path=output_path,
                    json_path=output_path,
                )

            self.assertEqual(b"sentinel", output_path.read_bytes())

    def test_write_outputs_rejects_symlink_aliases_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flu-output"
            alias_path = Path(tmpdir) / "flu-alias"
            output_path.write_bytes(b"sentinel")
            alias_path.symlink_to(output_path)

            with self.assertRaisesRegex(ValueError, "distinct filesystem targets"):
                flushot.write_outputs(
                    records,
                    csv_path=output_path,
                    json_path=alias_path,
                )

            self.assertEqual(b"sentinel", output_path.read_bytes())

    def test_write_outputs_rejects_hard_link_aliases_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flu-output"
            alias_path = Path(tmpdir) / "flu-alias"
            output_path.write_bytes(b"sentinel")
            os.link(output_path, alias_path)

            with self.assertRaisesRegex(ValueError, "distinct filesystem targets"):
                flushot.write_outputs(
                    records,
                    csv_path=output_path,
                    json_path=alias_path,
                )

            self.assertEqual(b"sentinel", output_path.read_bytes())

    def test_write_outputs_rejects_missing_parent_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "missing" / "flu.json"
            csv_path.write_bytes(b"sentinel")

            with self.assertRaisesRegex(ValueError, "output parent must be an existing directory"):
                flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertEqual(b"sentinel", csv_path.read_bytes())

    def test_write_outputs_rejects_non_directory_parent_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_parent = Path(tmpdir) / "not-a-directory"
            json_path = json_parent / "flu.json"
            csv_path.write_bytes(b"sentinel")
            json_parent.write_bytes(b"parent sentinel")

            with self.assertRaisesRegex(ValueError, "output parent must be an existing directory"):
                flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertEqual(b"sentinel", csv_path.read_bytes())
            self.assertEqual(b"parent sentinel", json_parent.read_bytes())

    def test_write_outputs_rejects_extra_fields_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0]["UNEXPECTED"] = "value"

        self.assert_malformed_records_preserve_outputs(records, "documented headers")

    def test_write_outputs_rejects_non_dictionary_rows_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0] = ["not", "a", "record"]

        self.assert_malformed_records_preserve_outputs(records, "documented headers")

    def test_write_outputs_rejects_non_string_values_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0]["NUM_JURIS"] = 10

        self.assert_malformed_records_preserve_outputs(records, "string values")

    def test_write_outputs_rejects_invalid_utf8_before_truncation(self):
        records = flushot.parse_records(FIXTURE.read_text(encoding="utf-8"))
        records[0]["HHS_REGION"] = "invalid \ud800"

        self.assert_malformed_records_preserve_outputs(records, "valid UTF-8")

    def assert_malformed_records_preserve_outputs(self, records, message):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "flu.csv"
            json_path = Path(tmpdir) / "flu.json"
            csv_path.write_bytes(b"csv sentinel")
            json_path.write_bytes(b"json sentinel")

            with self.assertRaisesRegex(ValueError, message):
                flushot.write_outputs(records, csv_path=csv_path, json_path=json_path)

            self.assertEqual(b"csv sentinel", csv_path.read_bytes())
            self.assertEqual(b"json sentinel", json_path.read_bytes())

    def test_parse_records_fails_when_metadata_is_missing(self):
        with self.assertRaisesRegex(ValueError, "week number and ending date"):
            flushot.parse_records("<html><table cellpadding='3'></table></html>")

    def test_parse_records_rejects_out_of_range_week_number(self):
        for invalid_week in (99, 530, 531):
            html = FIXTURE.read_text(encoding="utf-8").replace(
                "Influenza Season Week 12", f"Influenza Season Week {invalid_week}"
            )

            with self.assertRaisesRegex(ValueError, "between 1 and 53"):
                flushot.parse_records(html)

    def test_parse_records_accepts_week_boundaries(self):
        for week_number in (1, 53):
            html = FIXTURE.read_text(encoding="utf-8").replace(
                "Influenza Season Week 12", f"Influenza Season Week {week_number}"
            )

            records = flushot.parse_records(html)

            self.assertEqual(str(week_number), records[0]["WEEK_NUM"])

    def test_parse_records_rejects_week_zero(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "Influenza Season Week 12", "Influenza Season Week 0"
        )

        with self.assertRaisesRegex(ValueError, "between 1 and 53"):
            flushot.parse_records(html)

    def test_parse_records_rejects_invalid_week_ending_date(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "March 23, 2024", "February 31, 2024"
        )

        with self.assertRaisesRegex(ValueError, "valid calendar date"):
            flushot.parse_records(html)

    def test_parse_records_fails_when_summary_header_is_missing(self):
        html = FIXTURE.read_text(encoding="utf-8").replace(
            "<th>Percent positive</th>", "<th>Unexpected metric</th>"
        )

        with self.assertRaisesRegex(ValueError, "expected flu summary headers"):
            flushot.parse_records(html)

    def test_validate_fetch_url_requires_https_with_host(self):
        self.assertEqual(flushot.CDC_FLU_URL, flushot.validate_fetch_url(flushot.CDC_FLU_URL))

        with self.assertRaisesRegex(ValueError, "HTTPS URL"):
            flushot.validate_fetch_url("http://www.cdc.gov/flu/weekly/")

        with self.assertRaisesRegex(ValueError, "HTTPS URL"):
            flushot.validate_fetch_url("https:///flu/weekly/")

        with self.assertRaisesRegex(ValueError, "cdc.gov"):
            flushot.validate_fetch_url("https://example.com/flu/weekly/")

        self.assertEqual(
            "https://data.cdc.gov/flu/weekly/",
            flushot.validate_fetch_url("https://data.cdc.gov/flu/weekly/"),
        )

    def test_validate_fetch_url_rejects_embedded_credentials(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            flushot.validate_fetch_url("https://user:pass@www.cdc.gov/flu/weekly/")

    def test_validate_fetch_url_rejects_query_and_fragment(self):
        with self.assertRaisesRegex(ValueError, "query strings or fragments"):
            flushot.validate_fetch_url("https://www.cdc.gov/flu/weekly/?source=sample")

        with self.assertRaisesRegex(ValueError, "query strings or fragments"):
            flushot.validate_fetch_url("https://www.cdc.gov/flu/weekly/#summary")

    def test_validate_fetch_url_rejects_explicit_or_malformed_ports(self):
        rejected = (
            "https://www.cdc.gov:/flu/weekly/",
            "https://www.cdc.gov:443/flu/weekly/",
            "https://www.cdc.gov:8443/flu/weekly/",
            "https://www.cdc.gov:not-a-port/flu/weekly/",
            "https://www.cdc.gov:65536/flu/weekly/",
        )
        for url in rejected:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "explicit port"):
                    flushot.validate_fetch_url(url)

    def test_fetch_html_rejects_explicit_port_before_building_opener(self):
        with patch("flushot.build_opener") as build_opener:
            with self.assertRaisesRegex(ValueError, "explicit port"):
                flushot.fetch_html("https://www.cdc.gov:443/flu/weekly/")

        build_opener.assert_not_called()

    def test_fetch_timeout_rejects_invalid_or_out_of_range_values(self):
        self.assertEqual(30, flushot.fetch_timeout(""))
        self.assertEqual(30, flushot.fetch_timeout("not-a-timeout"))
        self.assertEqual(30, flushot.fetch_timeout(0))
        self.assertEqual(30, flushot.fetch_timeout(301))
        self.assertEqual(45, flushot.fetch_timeout("45"))

    def test_redirect_handler_revalidates_targets(self):
        handler = flushot.CDCNoRedirectHandler()
        request = Request(flushot.CDC_FLU_URL)

        with self.assertRaisesRegex(ValueError, "cdc.gov"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://example.com/private",
            )

        with self.assertRaisesRegex(ValueError, "explicit port"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://www.cdc.gov:8443/flu/weekly/",
            )

        with self.assertRaisesRegex(ValueError, "redirects are not allowed"):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://www.cdc.gov/flu/weekly/index.html",
            )

    def test_read_response_rejects_declared_oversize(self):
        response = FakeResponse(headers={"Content-Length": "11"})

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

        self.assertEqual(0, response.read_calls)

    def test_read_response_accepts_missing_or_exact_content_length(self):
        for headers in ({}, {"Content-Length": "10"}):
            with self.subTest(headers=headers):
                response = FakeResponse(body=b"1234567890", headers=headers)

                self.assertEqual(
                    b"1234567890",
                    flushot.read_response_bytes(response, max_bytes=10),
                )

    def test_read_response_rejects_body_shorter_than_content_length(self):
        response = FakeResponse(
            body=b"123456789",
            headers={"Content-Length": "10"},
        )

        with self.assertRaisesRegex(ValueError, "does not match Content-Length"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_read_response_rejects_body_longer_than_content_length(self):
        response = FakeResponse(
            body=b"1234567890",
            headers={"Content-Length": "9"},
        )

        with self.assertRaisesRegex(ValueError, "does not match Content-Length"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_read_response_rejects_duplicate_content_length_before_reading(self):
        for values in (("10", "10"), ("9", "10")):
            with self.subTest(values=values):
                headers = Message()
                for value in values:
                    headers["Content-Length"] = value
                response = FakeResponse(body=b"1234567890", headers=headers)

                with self.assertRaisesRegex(ValueError, "exactly one Content-Length"):
                    flushot.read_response_bytes(response, max_bytes=10)

                self.assertEqual(0, response.read_calls)

    def test_read_response_rejects_noncanonical_content_length_before_reading(self):
        rejected = ("", " 10", "10 ", "+10", "-1", "10, 10", "1.0", "ten")
        for content_length in rejected:
            with self.subTest(content_length=content_length):
                response = FakeResponse(
                    body=b"1234567890",
                    headers={"Content-Length": content_length},
                )

                with self.assertRaisesRegex(ValueError, "ASCII decimal"):
                    flushot.read_response_bytes(response, max_bytes=10)

                self.assertEqual(0, response.read_calls)

    def test_read_response_rejects_streamed_oversize(self):
        response = FakeResponse(body=b"12345678901")

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_read_response_rejects_streamed_oversize_after_smaller_declaration(self):
        response = FakeResponse(
            body=b"12345678901",
            headers={"Content-Length": "1"},
        )

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_fetch_html_requires_exact_success_status_before_metadata_or_body(self):
        for status in (199, 201, 204, 206, 301, 400, 404, 429, 500):
            response = FakeResponse(
                body=b"private response",
                status=status,
                headers={"Content-Type": "text/html; charset=utf-8"},
            )
            opener = FakeOpener(response)

            with self.subTest(status=status):
                with patch("flushot.build_opener", return_value=opener):
                    with patch(
                        "flushot.validate_fetch_url",
                        wraps=flushot.validate_fetch_url,
                    ) as validate_url:
                        with self.assertRaisesRegex(
                            ValueError,
                            r"^CDC response status must be 200\.$",
                        ):
                            flushot.fetch_html(max_bytes=40)
                self.assertEqual(0, response.read_calls)
                validate_url.assert_called_once_with(flushot.CDC_FLU_URL)

    def test_validate_response_content_type_accepts_utf8_html(self):
        for content_type in (
            "text/html",
            "text/html; charset=UTF-8",
            "text/html; charset=utf8",
            "TEXT/HTML; Charset=UTF-8",
            "text/html; charset*=utf-8''utf-8",
        ):
            with self.subTest(content_type=content_type):
                flushot.validate_html_content_type({"Content-Type": content_type})

    def test_validate_response_content_type_rejects_missing_or_incompatible_values(self):
        rejected = (
            ({}, "declare an HTML Content-Type"),
            ({"Content-Type": "application/json"}, "must be text/html"),
            ({"Content-Type": "text/html; charset=iso-8859-1"}, "must use UTF-8"),
        )

        for headers, message in rejected:
            with self.subTest(headers=headers):
                with self.assertRaisesRegex(ValueError, message):
                    flushot.validate_html_content_type(headers)

    def test_validate_response_content_type_rejects_duplicate_charset_parameters(
        self,
    ):
        for content_type in (
            "text/html; charset=utf-8; charset=utf-8",
            "text/html; charset=utf-8; charset=iso-8859-1",
            "text/html; CHARSET=utf8; charset=UTF-8",
            "text/html; charset*=utf-8''utf-8; charset=utf-8",
        ):
            with self.subTest(content_type=content_type):
                with self.assertRaisesRegex(
                    ValueError,
                    r"^CDC response Content-Type must declare at most one charset parameter\.$",
                ):
                    flushot.validate_html_content_type({"Content-Type": content_type})

    def test_fetch_html_rejects_duplicate_charset_before_reading_body(self):
        response = FakeResponse(
            body=b"private response",
            headers={
                "Content-Type": "text/html; charset=utf-8; charset=iso-8859-1"
            },
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(
                ValueError,
                r"^CDC response Content-Type must declare at most one charset parameter\.$",
            ):
                flushot.fetch_html(max_bytes=40)

        self.assertEqual(0, response.read_calls)

    def test_fetch_html_rejects_content_type_before_reading_body(self):
        response = FakeResponse(
            body=b'{"not": "html"}',
            headers={"Content-Type": "application/json"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "must be text/html"):
                flushot.fetch_html(max_bytes=20)

        self.assertEqual(0, response.read_calls)

    def test_fetch_html_rejects_duplicate_content_type_before_reading_body(self):
        for second_content_type in (
            "text/html; charset=utf-8",
            "application/json",
        ):
            headers = Message()
            headers["Content-Type"] = "text/html; charset=utf-8"
            headers["Content-Type"] = second_content_type
            response = FakeResponse(body=b"private response", headers=headers)
            opener = FakeOpener(response)

            with self.subTest(second_content_type=second_content_type):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(
                        ValueError,
                        r"^CDC response must declare exactly one Content-Type\.$",
                    ):
                        flushot.fetch_html(max_bytes=40)
                self.assertEqual(0, response.read_calls)

    def test_fetch_html_uses_validated_bounded_response(self):
        response = FakeResponse(
            body=b"<html>ok</html>",
            headers={
                "Content-Length": "15",
                "Content-Type": "text/html; charset=utf-8",
            },
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            html = flushot.fetch_html(timeout="45", max_bytes=20)

        self.assertEqual("<html>ok</html>", html)
        self.assertEqual(45, opener.timeout)
        self.assertEqual(flushot.CDC_FLU_URL, opener.request.full_url)

    def test_fetch_html_accepts_absent_or_identity_content_encoding(self):
        for content_encoding in (None, "identity", " IDENTITY "):
            headers = {"Content-Type": "text/html; charset=utf-8"}
            if content_encoding is not None:
                headers["Content-Encoding"] = content_encoding
            response = FakeResponse(body=b"<html>ok</html>", headers=headers)
            opener = FakeOpener(response)

            with self.subTest(content_encoding=content_encoding):
                with patch("flushot.build_opener", return_value=opener):
                    self.assertEqual(
                        "<html>ok</html>",
                        flushot.fetch_html(max_bytes=20),
                    )
                self.assertGreater(response.read_calls, 0)

    def test_fetch_html_rejects_unsupported_content_encoding_before_reading_body(self):
        for content_encoding in ("", "gzip", "deflate", "br", "identity, gzip"):
            response = FakeResponse(
                body=b"encoded private response",
                headers={
                    "Content-Type": "text/html; charset=utf-8",
                    "Content-Encoding": content_encoding,
                },
            )
            opener = FakeOpener(response)

            with self.subTest(content_encoding=content_encoding):
                with patch("flushot.build_opener", return_value=opener):
                    with self.assertRaisesRegex(
                        ValueError,
                        r"^CDC response Content-Encoding must be identity\.$",
                    ):
                        flushot.fetch_html(max_bytes=40)
                self.assertEqual(0, response.read_calls)

        duplicate_headers = Message()
        duplicate_headers["Content-Type"] = "text/html; charset=utf-8"
        duplicate_headers["Content-Encoding"] = "identity"
        duplicate_headers["Content-Encoding"] = "gzip"
        response = FakeResponse(
            body=b"encoded private response",
            headers=duplicate_headers,
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(
                ValueError,
                r"^CDC response Content-Encoding must be identity\.$",
            ):
                flushot.fetch_html(max_bytes=40)
        self.assertEqual(0, response.read_calls)

    def test_fetch_html_preserves_valid_multibyte_utf8(self):
        expected = "<html>caf\u00e9</html>"
        response = FakeResponse(
            body=expected.encode("utf-8"),
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            html = flushot.fetch_html(max_bytes=30)

        self.assertEqual(expected, html)

    def test_fetch_html_rejects_malformed_utf8_without_leaking_body(self):
        response = FakeResponse(
            body=b"<html>private-\xff-value</html>",
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with patch(
                "flushot.read_response_bytes",
                wraps=flushot.read_response_bytes,
            ) as bounded_read:
                with self.assertRaisesRegex(
                    ValueError,
                    r"^CDC response body must be valid UTF-8\.$",
                ) as error:
                    flushot.fetch_html(max_bytes=40)

        bounded_read.assert_called_once_with(response, 40)
        self.assertNotIn("private", str(error.exception))
        self.assertIsNone(error.exception.__cause__)

    def test_fetch_html_rejects_untrusted_final_url(self):
        response = FakeResponse(body=b"ignored", url="https://example.com/private")
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "cdc.gov"):
                flushot.fetch_html(max_bytes=20)


if __name__ == "__main__":
    unittest.main()
