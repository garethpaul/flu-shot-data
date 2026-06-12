import csv
import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

import flushot


FIXTURE = Path(__file__).parent / "fixtures" / "cdc_weekly_summary.html"


class FakeResponse:
    def __init__(self, body=b"", url=flushot.CDC_FLU_URL, headers=None):
        self.body = BytesIO(body)
        self.url = url
        self.headers = headers or {}

    def read(self, size=-1):
        return self.body.read(size)

    def geturl(self):
        return self.url

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

    def test_read_response_rejects_streamed_oversize(self):
        response = FakeResponse(body=b"12345678901")

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            flushot.read_response_bytes(response, max_bytes=10)

    def test_fetch_html_uses_validated_bounded_response(self):
        response = FakeResponse(
            body=b"<html>ok</html>",
            headers={"Content-Length": "15"},
        )
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            html = flushot.fetch_html(timeout="45", max_bytes=20)

        self.assertEqual("<html>ok</html>", html)
        self.assertEqual(45, opener.timeout)
        self.assertEqual(flushot.CDC_FLU_URL, opener.request.full_url)

    def test_fetch_html_rejects_untrusted_final_url(self):
        response = FakeResponse(body=b"ignored", url="https://example.com/private")
        opener = FakeOpener(response)

        with patch("flushot.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "cdc.gov"):
                flushot.fetch_html(max_bytes=20)


if __name__ == "__main__":
    unittest.main()
